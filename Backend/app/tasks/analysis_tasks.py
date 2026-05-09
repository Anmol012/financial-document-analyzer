from app.extensions import celery, mongo
from app.models import Analysis
from app.services.pdf_processor import PDFProcessor
from app.services.crewai_analyzer import FinancialAnalyzer
from bson import ObjectId
import logging
from config import Config

logger = logging.getLogger(__name__)


@celery.task(bind=True, max_retries=3, default_retry_delay=60)
def analyze_document_task(self, document_id, user_id, options=None):
    try:
        logger.info(f"Starting analysis for document {document_id}")

        document = mongo.db.documents.find_one({'_id': ObjectId(document_id)})
        if not document:
            logger.error(f"Document {document_id} not found")
            return {'error': 'Document not found'}

        mongo.db.documents.update_one(
            {'_id': ObjectId(document_id)},
            {'$set': {'status': 'analyzing'}}
        )

        analysis_data = Analysis.create(document_id, user_id)
        analysis_result = mongo.db.analyses.insert_one(analysis_data)
        analysis_id = analysis_result.inserted_id

        mongo.db.documents.update_one(
            {'_id': ObjectId(document_id)},
            {'$set': {'analysis_id': analysis_id}}
        )

        logger.info(f"Extracting text from {document['file_path']}")
        pdf_processor = PDFProcessor()

        is_valid, validation_message = pdf_processor.validate_pdf(document['file_path'])
        if not is_valid:
            raise ValueError(f"Invalid PDF: {validation_message}")

        document_text = pdf_processor.extract_text(document['file_path'])
        if not document_text or len(document_text.strip()) < 50:
            raise ValueError("Could not extract sufficient text from document")

        logger.info(f"Extracted {len(document_text)} characters from document")

        llm_provider = (options.get('llm_provider') if options else None) or Config.DEFAULT_LLM_PROVIDER

        logger.info(f"Starting AI analysis with provider: {llm_provider}")
        analyzer = FinancialAnalyzer(llm_provider=llm_provider)
        analysis_results = analyzer.analyze(document_text, options)

        confidence = calculate_confidence_score(analysis_results)

        mongo.db.analyses.update_one(
            {'_id': analysis_id},
            {'$set': Analysis.update_results(analysis_results, confidence, 'complete')}
        )
        mongo.db.documents.update_one(
            {'_id': ObjectId(document_id)},
            {'$set': {'status': 'complete'}}
        )

        logger.info(f"Analysis completed for document {document_id}")
        return {'status': 'success', 'analysis_id': str(analysis_id), 'document_id': document_id}

    except self.MaxRetriesExceededError:
        logger.error(f"Max retries exceeded for document {document_id}")
        _mark_failed(document_id)
        return {'error': 'Max retries exceeded'}

    except Exception as e:
        logger.error(f"Analysis failed for document {document_id}: {str(e)}")

        if self.request.retries >= self.max_retries:
            _mark_failed(document_id)
            if 'analysis_id' in dir():
                mongo.db.analyses.update_one(
                    {'_id': analysis_id},
                    {'$set': {'status': 'failed', 'error': str(e)}}
                )
            return {'error': str(e)}

        # Mark as failed so the status endpoint shows the right state between retries
        _mark_failed(document_id)
        raise self.retry(exc=e)


def _mark_failed(document_id):
    try:
        mongo.db.documents.update_one(
            {'_id': ObjectId(document_id)},
            {'$set': {'status': 'failed'}}
        )
    except Exception:
        pass


def calculate_confidence_score(results):
    score = 0.0
    if results.get('financialSummary') and len(str(results['financialSummary'])) > 50:
        score += 0.3
    if results.get('riskAssessment') and isinstance(results['riskAssessment'], dict):
        score += 0.25
    if results.get('marketInsights') and len(str(results.get('marketInsights', ''))) > 50:
        score += 0.25
    if results.get('recommendations') and len(str(results.get('recommendations', ''))) > 50:
        score += 0.2
    return min(score, 1.0)
