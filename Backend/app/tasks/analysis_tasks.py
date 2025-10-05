from app.extensions import celery, mongo
from app.models import Analysis, Document
from app.services.pdf_processor import PDFProcessor
from app.services.crewai_analyzer import FinancialAnalyzer
from bson import ObjectId
import logging
from config import Config

logger = logging.getLogger(__name__)

@celery.task(bind=True, max_retries=3)
def analyze_document_task(self, document_id, user_id, options=None):
    """
    Celery task to analyze a financial document
    """
    try:
        logger.info(f"Starting analysis for document {document_id}")
        
        # Get document
        document = mongo.db.documents.find_one({'_id': ObjectId(document_id)})
        if not document:
            logger.error(f"Document {document_id} not found")
            return {'error': 'Document not found'}
        
        # Update document status
        mongo.db.documents.update_one(
            {'_id': ObjectId(document_id)},
            {'$set': {'status': 'analyzing'}}
        )
        
        # Create analysis record
        analysis_data = Analysis.create(document_id, user_id)
        analysis_result = mongo.db.analyses.insert_one(analysis_data)
        analysis_id = analysis_result.inserted_id
        
        # Update document with analysis ID
        mongo.db.documents.update_one(
            {'_id': ObjectId(document_id)},
            {'$set': {'analysis_id': analysis_id}}
        )
        
        # Extract text from PDF
        logger.info(f"Extracting text from {document['file_path']}")
        pdf_processor = PDFProcessor()
        
        # Validate PDF first
        is_valid, validation_message = pdf_processor.validate_pdf(document['file_path'])
        if not is_valid:
            raise ValueError(f"Invalid PDF: {validation_message}")
        
        document_text = pdf_processor.extract_text(document['file_path'])
        
        if not document_text or len(document_text.strip()) < 50:
            raise ValueError("Could not extract sufficient text from document")
        
        logger.info(f"Extracted {len(document_text)} characters from document")
        
        # Get LLM provider from options or use default
        llm_provider = options.get('llm_provider') if options else None
        if not llm_provider:
            llm_provider = Config.DEFAULT_LLM_PROVIDER
        
        # Perform AI analysis using CrewAI
        logger.info(f"Starting AI analysis with provider: {llm_provider}")
        analyzer = FinancialAnalyzer(llm_provider=llm_provider)
        analysis_results = analyzer.analyze(document_text, options)
        
        # Calculate confidence score
        confidence = calculate_confidence_score(analysis_results)
        
        # Update analysis with results
        mongo.db.analyses.update_one(
            {'_id': analysis_id},
            {'$set': Analysis.update_results(analysis_results, confidence, 'complete')}
        )
        
        # Update document status
        mongo.db.documents.update_one(
            {'_id': ObjectId(document_id)},
            {'$set': {'status': 'complete'}}
        )
        
        logger.info(f"Analysis completed for document {document_id}")
        
        return {
            'status': 'success',
            'analysis_id': str(analysis_id),
            'document_id': document_id
        }
        
    except Exception as e:
        logger.error(f"Analysis failed for document {document_id}: {str(e)}")
        
        # Update document status to failed
        mongo.db.documents.update_one(
            {'_id': ObjectId(document_id)},
            {'$set': {'status': 'failed'}}
        )
        
        # Update analysis status if it exists
        if 'analysis_id' in locals():
            mongo.db.analyses.update_one(
                {'_id': analysis_id},
                {'$set': {'status': 'failed', 'error': str(e)}}
            )
        
        # Retry the task
        raise self.retry(exc=e, countdown=60)

def calculate_confidence_score(results):
    """
    Calculate confidence score based on analysis completeness
    """
    score = 0.0
    
    # Check if main sections are present
    if results.get('financialSummary') and len(results['financialSummary']) > 50:
        score += 0.3
    
    if results.get('riskAssessment') and isinstance(results['riskAssessment'], dict):
        score += 0.25
    
    if results.get('marketInsights') and len(results.get('marketInsights', '')) > 50:
        score += 0.25
    
    if results.get('recommendations') and len(results.get('recommendations', '')) > 50:
        score += 0.2
    
    return min(score, 1.0)