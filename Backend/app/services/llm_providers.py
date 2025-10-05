from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatOllama
from config import Config
import os
import logging

logger = logging.getLogger(__name__)

class LLMProvider:
    @staticmethod
    def get_llm(provider=None):
        """
        Get LLM instance based on provider
        Supports: openai, groq, ollama
        """
        if provider is None:
            provider = Config.DEFAULT_LLM_PROVIDER
        
        provider = provider.lower()
        
        try:
            if provider == 'openai':
                return LLMProvider._get_openai_llm()
            elif provider == 'groq':
                return LLMProvider._get_groq_llm()
            elif provider == 'ollama':
                return LLMProvider._get_ollama_llm()
            else:
                logger.warning(f"Unknown provider {provider}, falling back to OpenAI")
                return LLMProvider._get_openai_llm()
        except Exception as e:
            logger.error(f"Error initializing LLM provider {provider}: {str(e)}")
            raise
    
    @staticmethod
    def _get_openai_llm():
        """Initialize OpenAI LLM"""
        if not Config.OPENAI_API_KEY:
            raise ValueError("OpenAI API key not configured")
        
        return ChatOpenAI(
            model=Config.OPENAI_MODEL,
            temperature=0.7,
            api_key=Config.OPENAI_API_KEY
        )
    
    @staticmethod
    def _get_groq_llm():
        """Initialize Groq LLM"""
        if not Config.GROQ_API_KEY:
            raise ValueError("Groq API key not configured")
        
        # Groq uses OpenAI-compatible API
        return ChatOpenAI(
            model=Config.GROQ_MODEL,
            temperature=0.7,
            api_key=Config.GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1"
        )
    
    @staticmethod
    def _get_ollama_llm():
        """Initialize Ollama LLM"""
        return ChatOllama(
            model=Config.OLLAMA_MODEL,
            base_url=Config.OLLAMA_BASE_URL,
            temperature=0.7
        )
    
    @staticmethod
    def get_available_providers():
        """Return list of available providers based on configuration"""
        providers = []
        
        if Config.OPENAI_API_KEY:
            providers.append('openai')
        
        if Config.GROQ_API_KEY:
            providers.append('groq')
        
        # Ollama is always available if configured
        providers.append('ollama')
        
        return providers