from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from fastapi.responses import FileResponse
from bson import ObjectId
from datetime import datetime
import os
import tempfile
import logging

from app.extensions import mongo
from app.utils.export_utils import generate_pdf_report, generate_csv_report
from app.dependencies import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/history")
def get_analysis_history(
    documentId: str = Query(None),
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
    if documentId:
        query['document_id'] = ObjectId(documentId)

    cursor = mongo.db.analyses.find(query).sort('completed_at', -1).skip(skip).limit(limit)
    total = mongo.db.analyses.count_documents(query)

    history = []
    for a in cursor:
        doc = mongo.db.documents.find_one({'_id': a['document_id']})
        history.append({
            'id': str(a['_id']),
            'documentName': doc['name'] if doc else 'Unknown',
            'completedAt': a['completed_at'].isoformat() + 'Z' if a.get('completed_at') else None,
            'status': a['status'],
        })

    return {'history': history, 'total': total}


@router.get("/{analysis_id}")
def get_analysis(analysis_id: str, current_user: dict = Depends(get_current_user)):
    user_id = current_user['sub']
    user_role = current_user.get('role', 'Viewer')

    analysis = mongo.db.analyses.find_one({'_id': ObjectId(analysis_id)})
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    if user_role != 'Admin' and str(analysis['user_id']) != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")

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


@router.get("/{analysis_id}/export")
def export_analysis(
    analysis_id: str,
    format: str = Query("pdf"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user['sub']
    user_role = current_user.get('role', 'Viewer')

    if format not in ('pdf', 'csv'):
        raise HTTPException(status_code=400, detail="Invalid format. Use 'pdf' or 'csv'")

    analysis = mongo.db.analyses.find_one({'_id': ObjectId(analysis_id)})
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    if user_role != 'Admin' and str(analysis['user_id']) != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")

    doc = mongo.db.documents.find_one({'_id': analysis['document_id']})
    document_name = doc['name'] if doc else 'Unknown'

    temp_dir = tempfile.gettempdir()
    filename = f"analysis_{analysis_id}.{format}"
    filepath = os.path.join(temp_dir, filename)

    if format == 'pdf':
        generate_pdf_report(analysis, document_name, filepath)
        media_type = 'application/pdf'
    else:
        generate_csv_report(analysis, document_name, filepath)
        media_type = 'text/csv'

    # Clean up temp file after response is sent
    background_tasks.add_task(_remove_file, filepath)

    logger.info(f"Analysis exported: {analysis_id} as {format}")
    return FileResponse(filepath, media_type=media_type, filename=filename, background=background_tasks)


@router.delete("/{analysis_id}")
def delete_analysis(analysis_id: str, current_user: dict = Depends(get_current_user)):
    user_id = current_user['sub']
    user_role = current_user.get('role', 'Viewer')

    analysis = mongo.db.analyses.find_one({'_id': ObjectId(analysis_id)})
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    if user_role != 'Admin' and str(analysis['user_id']) != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")

    mongo.db.documents.update_one(
        {'analysis_id': ObjectId(analysis_id)},
        {'$set': {'analysis_id': None, 'status': 'pending'}}
    )
    mongo.db.analyses.delete_one({'_id': ObjectId(analysis_id)})

    logger.info(f"Analysis deleted: {analysis_id}")
    return {'message': 'Analysis deleted'}


def _remove_file(path: str):
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass
