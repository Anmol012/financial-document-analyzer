import PyPDF2
import pytesseract
from pdf2image import convert_from_path
import logging
import os

logger = logging.getLogger(__name__)

class PDFProcessor:
    @staticmethod
    def extract_text(pdf_path):
        """
        Extract text from PDF file
        Uses PyPDF2 for text extraction and falls back to OCR if needed
        """
        try:
            text = PDFProcessor._extract_text_pypdf(pdf_path)
            
            # If extracted text is too short, try OCR
            if len(text.strip()) < 100:
                logger.info(f"Text extraction yielded minimal text, trying OCR for {pdf_path}")
                text = PDFProcessor._extract_text_ocr(pdf_path)
            
            return text
        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path}: {str(e)}")
            raise
    
    @staticmethod
    def _extract_text_pypdf(pdf_path):
        """Extract text using PyPDF2"""
        text = ""
        
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            # Check if PDF is encrypted
            if pdf_reader.is_encrypted:
                raise ValueError("PDF is password-protected")
            
            num_pages = len(pdf_reader.pages)
            logger.info(f"Processing {num_pages} pages from {pdf_path}")
            
            for page_num in range(num_pages):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + "\n\n"
        
        return text
    
    @staticmethod
    def _extract_text_ocr(pdf_path):
        """Extract text using OCR (for scanned PDFs)"""
        text = ""
        
        try:
            # Convert PDF to images
            images = convert_from_path(pdf_path)
            
            logger.info(f"Running OCR on {len(images)} pages")
            
            for i, image in enumerate(images):
                # Perform OCR
                page_text = pytesseract.image_to_string(image)
                text += f"--- Page {i+1} ---\n{page_text}\n\n"
            
            return text
        except Exception as e:
            logger.error(f"OCR extraction failed: {str(e)}")
            raise
    
    @staticmethod
    def get_pdf_metadata(pdf_path):
        """Extract metadata from PDF"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                metadata = {
                    'num_pages': len(pdf_reader.pages),
                    'is_encrypted': pdf_reader.is_encrypted
                }
                
                # Get document info if available
                if pdf_reader.metadata:
                    info = pdf_reader.metadata
                    metadata['title'] = info.get('/Title', '')
                    metadata['author'] = info.get('/Author', '')
                    metadata['subject'] = info.get('/Subject', '')
                    metadata['creator'] = info.get('/Creator', '')
                
                return metadata
        except Exception as e:
            logger.error(f"Error extracting metadata: {str(e)}")
            return {'error': str(e)}
    
    @staticmethod
    def validate_pdf(pdf_path):
        """Validate if file is a valid PDF"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Try to access first page to validate
                if len(pdf_reader.pages) > 0:
                    _ = pdf_reader.pages[0]
                    return True, "Valid PDF"
                else:
                    return False, "PDF has no pages"
        except Exception as e:
            return False, f"Invalid PDF: {str(e)}"