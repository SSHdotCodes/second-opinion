#!/usr/bin/env python3
"""
Client Manager for Second Opinion MCP Server
Handles initialization and management of all AI service clients
"""

import os
import sys
import logging
from typing import Optional, Dict, Any

# AI API imports
import openai
import requests

# Gemini API imports - handle both possible installations gracefully
GEMINI_AVAILABLE = False
USE_NEW_SDK = False

try:
    # Try new SDK first
    import google.genai as genai
    from google.genai import types as genai_types
    GEMINI_AVAILABLE = True
    USE_NEW_SDK = True
except ImportError:
    try:
        # Fallback to old SDK
        import google.generativeai as genai
        GEMINI_AVAILABLE = True
        USE_NEW_SDK = False
    except ImportError:
        GEMINI_AVAILABLE = False

# Anthropic Claude imports
CLAUDE_AVAILABLE = False
try:
    import anthropic
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False

logger = logging.getLogger(__name__)


class ClientManager:
    """Manages all AI service client initialization and configuration"""
    
    def __init__(self):
        """Initialize the client manager"""
        # Core AI service clients
        self.openai_client = None
        self.gemini_client = None
        self.grok_client = None
        self.claude_client = None
        self.huggingface_api_key = None
        self.deepseek_client = None
        self.openrouter_client = None
        self.mistral_client = None
        self.together_client = None
        self.cohere_client = None
        self.groq_client_fast = None
        self.perplexity_client = None
        
        # New AI service clients
        self.chutes_client = None
        
        # New AI service clients
        self.replicate_api_key = None
        self.ai21_client = None
        self.stability_client = None
        self.fireworks_client = None
        self.anyscale_client = None
        
        # Local AI services
        self.ollama_client = None
        self.lmstudio_client = None
        
        # Cloud AI services
        self.azure_openai_client = None
        self.aws_bedrock_client = None
        self.vertex_ai_client = None
        
        # Specialized AI services
        self.writer_client = None
        self.jasper_client = None
        self.character_ai_client = None
        
        # Emerging AI platforms
        self.moonshot_client = None
        self.baichuan_client = None
        self.yi_client = None
        
        # Initialize all clients
        self.setup_all_clients()
    
    def setup_all_clients(self):
        """Initialize all AI service clients with environment variables"""
        logger.info("Initializing AI service clients...")
        
        # Core services
        self._setup_openai()
        self._setup_gemini()
        self._setup_grok()
        self._setup_claude()
        self._setup_huggingface()
        self._setup_deepseek()
        self._setup_openrouter()
        
        # Enhanced services
        self._setup_mistral()
        self._setup_together()
        self._setup_cohere()
        self._setup_groq_fast()
        self._setup_perplexity()
        
        # New AI platforms
        self._setup_replicate()
        self._setup_ai21()
        self._setup_stability()
        self._setup_fireworks()
        self._setup_anyscale()
        
        # Local services
        self._setup_ollama()
        self._setup_lmstudio()
        
        # Cloud services
        self._setup_azure_openai()
        self._setup_aws_bedrock()
        self._setup_vertex_ai()
        
        # Specialized services
        self._setup_writer()
        self._setup_jasper()
        self._setup_character_ai()
        
        # Emerging platforms
        self._setup_moonshot()
        self._setup_baichuan()
        self._setup_yi()
        
        # Add Chutes AI client
        self._setup_chutes()
        
        logger.info("Client initialization completed")
    
    def _setup_openai(self):
        """Initialize OpenAI client"""
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.openai_client = openai.OpenAI(api_key=api_key)
            logger.info("OpenAI client initialized")
        else:
            logger.warning("OPENAI_API_KEY not found - OpenAI features disabled")
    
    def _setup_gemini(self):
        """Initialize Gemini client"""
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key and GEMINI_AVAILABLE:
            if USE_NEW_SDK:
                self.gemini_client = genai.Client(api_key=api_key)
            else:
                genai.configure(api_key=api_key)
                self.gemini_client = genai
            logger.info("Gemini client initialized")
        else:
            if not GEMINI_AVAILABLE:
                logger.warning("Gemini API not available - install google-generativeai")
            else:
                logger.warning("GEMINI_API_KEY not found - Gemini features disabled")
    
    def _setup_grok(self):
        """Initialize Grok client (xAI API)"""
        api_key = os.getenv("GROK_API_KEY")
        if api_key:
            self.grok_client = openai.OpenAI(
                api_key=api_key,
                base_url="https://api.x.ai/v1"
            )
            logger.info("Grok client initialized")
        else:
            logger.warning("GROK_API_KEY not found - Grok features disabled")
    
    def _setup_claude(self):
        """Initialize Claude client"""
        api_key = os.getenv("CLAUDE_API_KEY")
        if api_key and CLAUDE_AVAILABLE:
            self.claude_client = anthropic.Anthropic(api_key=api_key)
            logger.info("Claude client initialized")
        else:
            if not CLAUDE_AVAILABLE:
                logger.warning("Claude API not available - install anthropic")
            else:
                logger.warning("CLAUDE_API_KEY not found - Claude features disabled")
    
    def _setup_huggingface(self):
        """Initialize HuggingFace client"""
        api_key = os.getenv("HUGGINGFACE_API_KEY")
        if api_key:
            self.huggingface_api_key = api_key
            logger.info("HuggingFace client initialized")
        else:
            logger.warning("HUGGINGFACE_API_KEY not found - HuggingFace features disabled")
    
    def _setup_deepseek(self):
        """Initialize DeepSeek client"""
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if api_key:
            self.deepseek_client = openai.OpenAI(
                api_key=api_key,
                base_url="https://api.deepseek.com"
            )
            logger.info("DeepSeek client initialized")
        else:
            logger.warning("DEEPSEEK_API_KEY not found - DeepSeek features disabled")
    
    def _setup_openrouter(self):
        """Initialize OpenRouter client"""
        api_key = os.getenv("OPENROUTER_API_KEY")
        if api_key:
            self.openrouter_client = openai.OpenAI(
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1"
            )
            logger.info("OpenRouter client initialized")
        else:
            logger.warning("OPENROUTER_API_KEY not found - OpenRouter features disabled")
    
    def _setup_mistral(self):
        """Initialize Mistral AI client"""
        api_key = os.getenv("MISTRAL_API_KEY")
        if api_key:
            self.mistral_client = openai.OpenAI(
                api_key=api_key,
                base_url="https://api.mistral.ai/v1"
            )
            logger.info("Mistral AI client initialized")
        else:
            logger.warning("MISTRAL_API_KEY not found - Mistral AI features disabled")
    
    def _setup_together(self):
        """Initialize Together AI client"""
        api_key = os.getenv("TOGETHER_API_KEY")
        if api_key:
            self.together_client = openai.OpenAI(
                api_key=api_key,
                base_url="https://api.together.xyz/v1"
            )
            logger.info("Together AI client initialized")
        else:
            logger.warning("TOGETHER_API_KEY not found - Together AI features disabled")
    
    def _setup_cohere(self):
        """Initialize Cohere client"""
        api_key = os.getenv("COHERE_API_KEY")
        if api_key:
            try:
                import cohere
                self.cohere_client = cohere.Client(api_key=api_key)
                logger.info("Cohere client initialized")
            except ImportError:
                logger.warning("Cohere package not available. Install with: pip install cohere")
                self.cohere_client = None
        else:
            logger.warning("COHERE_API_KEY not found - Cohere features disabled")
    
    def _setup_groq_fast(self):
        """Initialize Groq Fast client"""
        api_key = os.getenv("GROQ_FAST_API_KEY") or os.getenv("GROQ_API_KEY")
        if api_key:
            self.groq_client_fast = openai.OpenAI(
                api_key=api_key,
                base_url="https://api.groq.com/openai/v1"
            )
            logger.info("Groq Fast client initialized")
        else:
            logger.warning("GROQ_FAST_API_KEY not found - Enhanced Groq features disabled")
    
    def _setup_perplexity(self):
        """Initialize Perplexity AI client"""
        api_key = os.getenv("PERPLEXITY_API_KEY")
        if api_key:
            self.perplexity_client = openai.OpenAI(
                api_key=api_key,
                base_url="https://api.perplexity.ai"
            )
            logger.info("Perplexity AI client initialized")
        else:
            logger.warning("PERPLEXITY_API_KEY not found - Perplexity AI features disabled")
    
    def _setup_replicate(self):
        """Initialize Replicate AI client"""
        api_key = os.getenv("REPLICATE_API_TOKEN")
        if api_key:
            self.replicate_api_key = api_key
            logger.info("Replicate AI initialized")
        else:
            logger.warning("REPLICATE_API_TOKEN not found - Replicate AI features disabled")
    
    def _setup_ai21(self):
        """Initialize AI21 Labs client"""
        api_key = os.getenv("AI21_API_KEY")
        if api_key:
            self.ai21_client = openai.OpenAI(
                api_key=api_key,
                base_url="https://api.ai21.com/studio/v1"
            )
            logger.info("AI21 Labs client initialized")
        else:
            logger.warning("AI21_API_KEY not found - AI21 Labs features disabled")
    
    def _setup_stability(self):
        """Initialize Stability AI client"""
        api_key = os.getenv("STABILITY_API_KEY")
        if api_key:
            self.stability_client = openai.OpenAI(
                api_key=api_key,
                base_url="https://api.stability.ai/v2beta"
            )
            logger.info("Stability AI client initialized")
        else:
            logger.warning("STABILITY_API_KEY not found - Stability AI features disabled")
    
    def _setup_fireworks(self):
        """Initialize Fireworks AI client"""
        api_key = os.getenv("FIREWORKS_API_KEY")
        if api_key:
            self.fireworks_client = openai.OpenAI(
                api_key=api_key,
                base_url="https://api.fireworks.ai/inference/v1"
            )
            logger.info("Fireworks AI client initialized")
        else:
            logger.warning("FIREWORKS_API_KEY not found - Fireworks AI features disabled")
    
    def _setup_anyscale(self):
        """Initialize Anyscale client"""
        api_key = os.getenv("ANYSCALE_API_KEY")
        if api_key:
            self.anyscale_client = openai.OpenAI(
                api_key=api_key,
                base_url="https://api.endpoints.anyscale.com/v1"
            )
            logger.info("Anyscale Endpoints client initialized")
        else:
            logger.warning("ANYSCALE_API_KEY not found - Anyscale features disabled")
    
    def _setup_ollama(self):
        """Initialize Ollama client (local AI models)"""
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        api_key = os.getenv("OLLAMA_API_KEY", "ollama")
        try:
            response = requests.get(f"{base_url.replace('/v1', '')}/api/tags", timeout=2)
            if response.status_code == 200:
                self.ollama_client = openai.OpenAI(
                    api_key=api_key,
                    base_url=base_url
                )
                logger.info("Ollama client initialized")
            else:
                logger.warning("Ollama server not responding - Ollama features disabled")
        except Exception as e:
            logger.warning(f"Ollama not available: {e} - Ollama features disabled")
    
    def _setup_lmstudio(self):
        """Initialize LM Studio client (local AI models)"""
        base_url = os.getenv("LMSTUDIO_BASE_URL", "http://localhost:1234/v1")
        api_key = os.getenv("LMSTUDIO_API_KEY", "lm-studio")
        try:
            response = requests.get(f"{base_url}/models", timeout=2)
            if response.status_code == 200:
                self.lmstudio_client = openai.OpenAI(
                    api_key=api_key,
                    base_url=base_url
                )
                logger.info("LM Studio client initialized")
            else:
                logger.warning("LM Studio server not responding - LM Studio features disabled")
        except Exception as e:
            logger.warning(f"LM Studio not available: {e} - LM Studio features disabled")
    
    def _setup_azure_openai(self):
        """Initialize Azure OpenAI client"""
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        if api_key and endpoint:
            try:
                from openai import AzureOpenAI
                self.azure_openai_client = AzureOpenAI(
                    api_key=api_key,
                    azure_endpoint=endpoint,
                    api_version="2024-02-01"
                )
                logger.info("Azure OpenAI client initialized")
            except ImportError:
                logger.warning("Azure OpenAI requires newer openai package version")
        else:
            logger.warning("AZURE_OPENAI_API_KEY or AZURE_OPENAI_ENDPOINT not found - Azure OpenAI features disabled")
    
    def _setup_aws_bedrock(self):
        """Initialize AWS Bedrock client"""
        region = os.getenv("AWS_REGION", "us-east-1")
        access_key = os.getenv("AWS_ACCESS_KEY_ID")
        secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        if access_key and secret_key:
            try:
                import boto3
                self.aws_bedrock_client = boto3.client(
                    'bedrock-runtime',
                    region_name=region,
                    aws_access_key_id=access_key,
                    aws_secret_access_key=secret_key
                )
                logger.info("AWS Bedrock client initialized")
            except ImportError:
                logger.warning("AWS Bedrock requires boto3. Install with: pip install boto3")
            except Exception as e:
                logger.warning(f"AWS Bedrock setup failed: {e}")
        else:
            logger.warning("AWS credentials not found - AWS Bedrock features disabled")
    
    def _setup_vertex_ai(self):
        """Initialize Google Vertex AI client"""
        project_id = os.getenv("VERTEX_PROJECT_ID")
        location = os.getenv("VERTEX_LOCATION", "us-central1")
        if project_id:
            try:
                from google.cloud import aiplatform
                import google.auth
                aiplatform.init(project=project_id, location=location)
                self.vertex_ai_client = aiplatform
                logger.info("Google Vertex AI client initialized")
            except ImportError:
                logger.warning("Vertex AI requires google-cloud-aiplatform. Install with: pip install google-cloud-aiplatform")
            except Exception as e:
                logger.warning(f"Vertex AI setup failed: {e}")
        else:
            logger.warning("VERTEX_PROJECT_ID not found - Vertex AI features disabled")
    
    def _setup_writer(self):
        """Initialize Writer.com client"""
        api_key = os.getenv("WRITER_API_KEY")
        if api_key:
            self.writer_client = openai.OpenAI(
                api_key=api_key,
                base_url="https://api.writer.com/v1"
            )
            logger.info("Writer.com client initialized")
        else:
            logger.warning("WRITER_API_KEY not found - Writer.com features disabled")
    
    def _setup_jasper(self):
        """Initialize Jasper AI client"""
        api_key = os.getenv("JASPER_API_KEY")
        if api_key:
            self.jasper_client = openai.OpenAI(
                api_key=api_key,
                base_url="https://api.jasper.ai/v1"
            )
            logger.info("Jasper AI client initialized")
        else:
            logger.warning("JASPER_API_KEY not found - Jasper AI features disabled")
    
    def _setup_character_ai(self):
        """Initialize Character.AI client"""
        api_key = os.getenv("CHARACTER_AI_KEY")
        if api_key:
            self.character_ai_client = openai.OpenAI(
                api_key=api_key,
                base_url="https://beta.character.ai/chat/streaming"
            )
            logger.info("Character.AI client initialized")
        else:
            logger.warning("CHARACTER_AI_KEY not found - Character.AI features disabled")
    
    def _setup_moonshot(self):
        """Initialize Moonshot AI client"""
        api_key = os.getenv("MOONSHOT_API_KEY")
        if api_key:
            self.moonshot_client = openai.OpenAI(
                api_key=api_key,
                base_url="https://api.moonshot.cn/v1"
            )
            logger.info("Moonshot AI client initialized")
        else:
            logger.warning("MOONSHOT_API_KEY not found - Moonshot AI features disabled")
    
    def _setup_baichuan(self):
        """Initialize Baichuan AI client"""
        api_key = os.getenv("BAICHUAN_API_KEY")
        if api_key:
            self.baichuan_client = openai.OpenAI(
                api_key=api_key,
                base_url="https://api.baichuan-ai.com/v1"
            )
            logger.info("Baichuan AI client initialized")
        else:
            logger.warning("BAICHUAN_API_KEY not found - Baichuan AI features disabled")
    
    def _setup_yi(self):
        """Initialize 01.AI (Yi models) client"""
        api_key = os.getenv("YI_API_KEY")
        if api_key:
            self.yi_client = openai.OpenAI(
                api_key=api_key,
                base_url="https://api.lingyiwanwu.com/v1"
            )
            logger.info("01.AI (Yi models) client initialized")
        else:
            logger.warning("YI_API_KEY not found - 01.AI features disabled")
    
    def get_available_clients(self) -> Dict[str, bool]:
        """Return a dictionary of available client status"""
        return {
            "openai": self.openai_client is not None,
            "gemini": self.gemini_client is not None,
            "grok": self.grok_client is not None,
            "claude": self.claude_client is not None,
            "huggingface": self.huggingface_api_key is not None,
            "deepseek": self.deepseek_client is not None,
            "openrouter": self.openrouter_client is not None,
            "mistral": self.mistral_client is not None,
            "together": self.together_client is not None,
            "cohere": self.cohere_client is not None,
            "groq_fast": self.groq_client_fast is not None,
            "perplexity": self.perplexity_client is not None,
            "replicate": self.replicate_api_key is not None,
            "ai21": self.ai21_client is not None,
            "stability": self.stability_client is not None,
            "fireworks": self.fireworks_client is not None,
            "anyscale": self.anyscale_client is not None,
            "ollama": self.ollama_client is not None,
            "lmstudio": self.lmstudio_client is not None,
            "azure_openai": self.azure_openai_client is not None,
            "aws_bedrock": self.aws_bedrock_client is not None,
            "vertex_ai": self.vertex_ai_client is not None,
            "writer": self.writer_client is not None,
            "jasper": self.jasper_client is not None,
            "character_ai": self.character_ai_client is not None,
            "moonshot": self.moonshot_client is not None,
            "baichuan": self.baichuan_client is not None,
            "yi": self.yi_client is not None,
            "chutes": self.chutes_client is not None
        }

    def _setup_chutes(self):
        """Initialize Chutes AI client"""
        api_key = os.getenv("CHUTES_API_KEY")
        if api_key:
            self.chutes_client = openai.OpenAI(
                api_key=api_key,
                base_url="https://llm.chutes.ai/v1"
            )
            logger.info("Chutes AI client initialized")
        else:
            logger.warning("CHUTES_API_KEY not found - Chutes AI features disabled")