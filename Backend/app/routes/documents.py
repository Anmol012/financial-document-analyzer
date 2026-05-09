from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from bson import ObjectId
from datetime import datetime
import os
import re
import logging

from app.extensions import mongo
from app.models import Document
from app.tasks.analysis_tasks import analyze_document_task
from app.dependencies import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

UPLOAD_FOLDER = 'uploads'
MAX_FILE_SIZE = 104857600  # 100 MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def _secure_filename(filename: str) -> str:
    filename = os.path.basename(filename)
    filename = re.sub(r'[^\w\s.\-]', '', filename).strip()
    return filename or 'upload.pdf'


def _doc_to_dict(doc: dict) -> dict:
    return {
        'id': str(doc['_id']),
        'name': doc['name'],
        'uploadDate': doc['upload_date'].isoformat() + 'Z',
        'status': doc['status'],
        'analysisId': str(doc['analysis_id']) if doc.get('analysis_id') else None,
    }


# ─── Endpoints ───────────────────────────────────────────────────────────────

@router.post("/upload", status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    name: str = Form(None),
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user['sub']

    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    contents = await file.read()
    file_size = len(contents)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File size exceeds 100MB limit")

    filename = _secure_filename(file.filename)
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')
    unique_filename = f"{timestamp}_{filename}"
    file_path = os.path.join(UPLOAD_FOLDER, unique_filename)

    with open(file_path, 'wb') as f:
        f.write(contents)

    document_name = name or filename
    document_data = Document.create(document_name, user_id, file_path, file_size)
    result = mongo.db.documents.insert_one(document_data)

    logger.info(f"Document uploaded: {unique_filename} by user {user_id}")
    return {
        'message': 'Document uploaded',
        'document': {
            'id': str(result.inserted_id),
            'name': document_name,
            'uploadDate': document_data['upload_date'].isoformat() + 'Z',
            'status': document_data['status'],
        },
    }


@router.get("")
def get_documents(
    search: str = Query(""),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user['sub']
    user_role = current_user.get('role', 'Viewer')
    skip = (page - 1) * limit

    query = {}
    if user_role != 'Admin':
        query['user_id'] = ObjectId(user_id)
    if search:
        query['name'] = {'$regex': search, '$options': 'i'}

    cursor = mongo.db.documents.find(query).sort('upload_date', -1).skip(skip).limit(limit)
    total = mongo.db.documents.count_documents(query)

    return {
        'documents': [_doc_to_dict(d) for d in cursor],
        'total': total,
        'page': page,
    }


@router.get("/{document_id}")
def get_document(document_id: str, current_user: dict = Depends(get_current_user)):
    user_id = current_user['sub']
    user_role = current_user.get('role', 'Viewer')

    doc = mongo.db.documents.find_one({'_id': ObjectId(document_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if user_role != 'Admin' and str(doc['user_id']) != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")

    return {
        'document': {
            **_doc_to_dict(doc),
            'fileSize': doc['file_size'],
        }
    }


@router.post("/{document_id}/analyze", status_code=202)
def analyze_document(document_id: str, current_user: dict = Depends(get_current_user)):
    user_id = current_user['sub']
    user_role = current_user.get('role', 'Viewer')

    doc = mongo.db.documents.find_one({'_id': ObjectId(document_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if user_role != 'Admin' and str(doc['user_id']) != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    if doc['status'] == 'analyzing':
        raise HTTPException(status_code=400, detail="Analysis already in progress")
    if doc['status'] == 'complete':
        raise HTTPException(status_code=400, detail="Document already analyzed. Delete the analysis to re-run.")

    task = analyze_document_task.delay(document_id, user_id, {})
    mongo.db.documents.update_one(
        {'_id': ObjectId(document_id)},
        {'$set': {'task_id': task.id}}
    )

    logger.info(f"Analysis started for document {document_id}, task {task.id}")
    return {'message': 'Analysis started', 'taskId': task.id}


@router.get("/{document_id}/status")
def get_analysis_status(document_id: str, current_user: dict = Depends(get_current_user)):
    user_id = current_user['sub']
    user_role = current_user.get('role', 'Viewer')

    doc = mongo.db.documents.find_one({'_id': ObjectId(document_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if user_role != 'Admin' and str(doc['user_id']) != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")

    response = {
        'status': doc['status'],
        'analysisId': str(doc['analysis_id']) if doc.get('analysis_id') else None,
    }
    if doc.get('task_id'):
        from celery.result import AsyncResult
        from app.extensions import celery
        result = AsyncResult(doc['task_id'], app=celery)
        response['taskState'] = result.state

    return response


@router.get("/{document_id}/result")
def get_analysis_result(document_id: str, current_user: dict = Depends(get_current_user)):
    user_id = current_user['sub']
    user_role = current_user.get('role', 'Viewer')

    doc = mongo.db.documents.find_one({'_id': ObjectId(document_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if user_role != 'Admin' and str(doc['user_id']) != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    if not doc.get('analysis_id'):
        raise HTTPException(status_code=404, detail="Analysis not found or incomplete")

    analysis = mongo.db.analyses.find_one({'_id': doc['analysis_id']})
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found or incomplete")

    return {
        'analysis': {
            'id': str(analysis['_id']),
            'documentId': str(analysis['document_id']),
            'results': analysis['results'],
            'confidence': analysis['confidence'],
            'completedAt': analysis['completed_at'].isoformat() + 'Z' if analysis.get('completed_at') else None,
            'status': analysis['status'],
        }
    }


@router.delete("/{document_id}")
def delete_document(document_id: str, current_user: dict = Depends(get_current_user)):
    user_id = current_user['sub']
    user_role = current_user.get('role', 'Viewer')

    doc = mongo.db.documents.find_one({'_id': ObjectId(document_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if user_role != 'Admin' and str(doc['user_id']) != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")

    if os.path.exists(doc['file_path']):
        os.remove(doc['file_path'])
    if doc.get('analysis_id'):
        mongo.db.analyses.delete_one({'_id': doc['analysis_id']})
    mongo.db.documents.delete_one({'_id': ObjectId(document_id)})

    logger.info(f"Document deleted: {document_id}")
    return {'message': 'Document deleted'}


@router.get("/{document_id}/download")
def download_document(document_id: str, current_user: dict = Depends(get_current_user)):
    user_id = current_user['sub']
    user_role = current_user.get('role', 'Viewer')

    doc = mongo.db.documents.find_one({'_id': ObjectId(document_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if user_role != 'Admin' and str(doc['user_id']) != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    if not os.path.exists(doc['file_path']):
        raise HTTPException(status_code=404, detail="File not found on disk")

    return FileResponse(doc['file_path'], media_type='application/pdf', filename=doc['name'])
