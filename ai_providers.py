#!/usr/bin/env python3
"""
AI Providers for Second Opinion MCP Server
Contains implementations for all supported AI services
"""

import asyncio
import json
import logging
import os
import time
from typing import Sequence, Optional, Dict, Any, List
import requests

from mcp.types import TextContent

logger = logging.getLogger(__name__)


class AIProviders:
    """Handles all AI provider implementations and API calls"""
    
    def __init__(self, client_manager, conversation_manager):
        """Initialize with client and conversation managers"""
        self.client_manager = client_manager
        self.conversation_manager = conversation_manager
        
        # Set up shortcuts for cleaner code
        self.clients = client_manager
        self.conv = conversation_manager
        
        # Load model priority configuration
        self.model_config = self._load_model_config()
        
        logger.info("AI Providers initialized")
    
    def _load_model_config(self) -> Dict[str, Any]:
        """Load model priority configuration from JSON file"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), 'model_priority.json')
            with open(config_path, 'r') as f:
                config = json.load(f)
            logger.info(f"Loaded model priority configuration with {len(config['model_priority'])} models")
            return config
        except Exception as e:
            logger.warning(f"Failed to load model priority config: {e}")
            # Return default fallback configuration
            return {
                "model_priority": [],
                "fallback_order": ["openai", "gemini", "grok", "claude", "deepseek", "groq_fast", "perplexity", "huggingface", "chutes", "ollama"],
                "personality_defaults": {}
            }
    
    def _get_best_available_model(self, personality: str = None) -> Optional[tuple]:
        """Get the best available model based on priority configuration"""
        available_clients = self.clients.get_available_clients()
        
        # If personality is specified, try preferred models first
        if personality and personality in self.model_config.get("personality_defaults", {}):
            preferred_models = self.model_config["personality_defaults"][personality]["preferred_models"]
            for model_name in preferred_models:
                for model_info in self.model_config["model_priority"]:
                    if model_info["model"] == model_name and available_clients.get(model_info["platform"], False):
                        logger.info(f"Selected {personality} personality preferred model: {model_info['platform']}/{model_info['model']}")
                        return (model_info["platform"], model_info["model"])
        
        # Fall back to general priority order
        for model_info in self.model_config["model_priority"]:
            platform = model_info["platform"]
            model = model_info["model"]
            
            if available_clients.get(platform, False):
                logger.info(f"Selected best available model: {platform}/{model} (quality score: {model_info['quality_score']})")
                return (platform, model)
        
        # Final fallback using platform order
        for platform in self.model_config["fallback_order"]:
            if available_clients.get(platform, False):
                # Use first available model for this platform
                default_models = {
                    "openai": "gpt-4.1",
                    "gemini": "gemini-2.5-flash-lite-preview-06-17",
                    "grok": "grok-4",
                    "claude": "claude-4-sonnet-20250514",
                    "deepseek": "deepseek-chat",
                    "groq_fast": "llama-3.1-70b-versatile",
                    "perplexity": "llama-3.1-sonar-large-128k-online",
                    "huggingface": "meta-llama/Llama-3.3-70B-Instruct",
                    "chutes": "moonshotai/Kimi-K2-Thinking",
                    "ollama": "llama3.2"
                }
                model = default_models.get(platform, "")
                if model:
                    logger.info(f"Using fallback model: {platform}/{model}")
                    return (platform, model)
        
        return None
    
    async def get_openai_opinion(
        self,
        prompt: str,
        model: str = "gpt-4.1",
        temperature: float = 0.7,
        max_tokens: int = 8000,
        system_prompt: str = "",
        reset_conversation: bool = False,
        personality: str = None
    ) -> Sequence[TextContent]:
        """Get opinion from OpenAI model"""
        if not self.clients.openai_client:
            return [TextContent(type="text", text="OpenAI client not configured. Please set OPENAI_API_KEY environment variable.")]
        
        try:
            conversation_key = self.conv.get_conversation_key("openai", model)
            
            # Reset conversation if requested
            if reset_conversation:
                self.conv.reset_conversation(conversation_key)
            
            # Build messages with conversation history
            messages = self.conv.get_openai_messages(conversation_key, prompt, system_prompt, personality)
            
            # Use max_completion_tokens for o4-mini and other o-series models
            token_param = "max_completion_tokens" if model.startswith("o") else "max_tokens"
            
            kwargs = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                token_param: max_tokens
            }
            
            # Handle "thinking" models
            if ":think" in model:
                kwargs["model"] = model.replace(":think", "")
                kwargs["reasoning_effort"] = "high"

            response = self.clients.openai_client.chat.completions.create(**kwargs)
            response_content = response.choices[0].message.content
            
            # Add to conversation history
            self.conv.add_to_conversation_history(conversation_key, "user", prompt)
            self.conv.add_to_conversation_history(conversation_key, "assistant", response_content)
            
            result = f"**OpenAI {model} Opinion:**\n\n{response_content}"
            return [TextContent(type="text", text=result)]
            
        except Exception as e:
            logger.error(f"OpenAI API Error: {str(e)}")
            return [TextContent(type="text", text=f"OpenAI API Error: {str(e)}")]
    
    async def get_gemini_opinion(
        self,
        prompt: str,
        model: str = "gemini-2.5-flash-lite-preview-06-17",
        temperature: float = 0.7,
        max_output_tokens: int = 8000,
        reset_conversation: bool = False,
        personality: str = None
    ) -> Sequence[TextContent]:
        """Get opinion from Gemini model"""
        if not self.clients.gemini_client:
            return [TextContent(type="text", text="Gemini client not configured. Please set GEMINI_API_KEY environment variable.")]
        
        try:
            conversation_key = self.conv.get_conversation_key("gemini", model)
            
            # Reset conversation if requested
            if reset_conversation:
                self.conv.reset_conversation(conversation_key)
            
            result_text = None
            max_retries = 3
            
            for retry_attempt in range(max_retries):
                try:
                    # Get history and prompt formatted for Gemini
                    history, full_prompt = self.conv.get_gemini_history_and_prompt(
                        conversation_key, prompt, None, personality
                    )
                    
                    # Use the newer SDK or fallback to legacy
                    if hasattr(self.clients, 'USE_NEW_SDK') and self.clients.USE_NEW_SDK:
                        result_text = await self._call_gemini_new_sdk(
                            conversation_key, full_prompt, model, temperature, max_output_tokens, history
                        )
                    else:
                        result_text = await self._call_gemini_old_sdk(
                            conversation_key, full_prompt, model, temperature, max_output_tokens, history
                        )
                    
                    # Validate response
                    if result_text and len(result_text.strip()) > 0:
                        break  # Success!
                    else:
                        logger.warning(f"Gemini returned empty response on attempt {retry_attempt + 1}")
                        if retry_attempt < max_retries - 1:
                            await asyncio.sleep(2 ** retry_attempt)  # Exponential backoff
                        
                except Exception as retry_error:
                    logger.warning(f"Gemini attempt {retry_attempt + 1} failed: {str(retry_error)}")
                    if retry_attempt < max_retries - 1:
                        await asyncio.sleep(2 ** retry_attempt)  # Exponential backoff
                    else:
                        raise retry_error
            
            # Final validation
            if not result_text or len(result_text.strip()) == 0:
                # Try with reset conversation for conversation issues
                if len(self.conv.get_conversation_context(conversation_key)) > 0:
                    logger.info(f"Trying Gemini {model} with reset conversation due to empty response")
                    self.conv.reset_conversation(conversation_key)
                    
                    # Retry once more with clean slate
                    history, full_prompt = self.conv.get_gemini_history_and_prompt(
                        conversation_key, prompt, None, personality
                    )
                    if hasattr(self.clients, 'USE_NEW_SDK') and self.clients.USE_NEW_SDK:
                        result_text = await self._call_gemini_new_sdk(
                            conversation_key, full_prompt, model, temperature, max_output_tokens, history
                        )
                    else:
                        result_text = await self._call_gemini_old_sdk(
                            conversation_key, full_prompt, model, temperature, max_output_tokens, history
                        )
                
                if not result_text or len(result_text.strip()) == 0:
                    result_text = "Error: Gemini model returned empty response after retries"
            
            # Add to conversation history only if we got a valid response
            if result_text and len(result_text.strip()) > 0:
                self.conv.add_to_conversation_history(conversation_key, "user", prompt)
                self.conv.add_to_conversation_history(conversation_key, "assistant", result_text)
            
            result = f"**Google Gemini {model} Opinion:**\n\n{result_text}"
            return [TextContent(type="text", text=result)]
            
        except Exception as e:
            logger.error(f"Gemini API Error: {str(e)}")
            return [TextContent(type="text", text=f"Gemini API Error: {str(e)}")]
    
    async def _call_gemini_new_sdk(self, conversation_key, full_prompt, model, temperature, max_output_tokens, history):
        """Call Gemini using the new SDK"""
        try:
            import google.genai as genai
            
            # Configure generation
            generation_config = genai.types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=max_output_tokens
            )
            
            # Start chat with history
            chat = self.clients.gemini_client.chats.create(
                model=model,
                config=generation_config,
                history=history
            )
            
            # Send message
            response = chat.send_message(full_prompt)
            return response.text
            
        except Exception as e:
            logger.error(f"Gemini new SDK error: {str(e)}")
            raise e
    
    async def _call_gemini_old_sdk(self, conversation_key, full_prompt, model, temperature, max_output_tokens, history):
        """Call Gemini using the legacy SDK"""
        try:
            import google.generativeai as genai
            
            # Configure generation
            generation_config = genai.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_output_tokens
            )
            
            # Create model
            ai_model = genai.GenerativeModel(model, generation_config=generation_config)
            
            # Start chat with history
            chat = ai_model.start_chat(history=history)
            
            # Send message
            response = chat.send_message(full_prompt)
            return response.text
            
        except Exception as e:
            logger.error(f"Gemini legacy SDK error: {str(e)}")
            raise e
    
    async def get_grok_opinion(
        self,
        prompt: str,
        model: str = "grok-3",
        temperature: float = 0.7,
        max_tokens: int = 8000,
        system_prompt: str = "",
        reset_conversation: bool = False,
        personality: str = None,
        reasoning_effort: str = "medium"
    ) -> Sequence[TextContent]:
        """Get opinion from Grok model (xAI)"""
        if not self.clients.grok_client:
            return [TextContent(type="text", text="Grok client not configured. Please set GROK_API_KEY environment variable.")]
        
        try:
            conversation_key = self.conv.get_conversation_key("grok", model)
            
            # Reset conversation if requested
            if reset_conversation:
                self.conv.reset_conversation(conversation_key)
            
            # Build messages with conversation history
            messages = self.conv.get_openai_messages(conversation_key, prompt, system_prompt, personality)
            
            kwargs = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            # Add reasoning effort for thinking models
            if "thinking" in model.lower() or "mini" in model.lower():
                kwargs["reasoning_effort"] = reasoning_effort
            
            response = self.clients.grok_client.chat.completions.create(**kwargs)
            response_content = response.choices[0].message.content
            
            # Add to conversation history
            self.conv.add_to_conversation_history(conversation_key, "user", prompt)
            self.conv.add_to_conversation_history(conversation_key, "assistant", response_content)
            
            result = f"**xAI Grok {model} Opinion:**\n\n{response_content}"
            return [TextContent(type="text", text=result)]
            
        except Exception as e:
            logger.error(f"Grok API Error: {str(e)}")
            return [TextContent(type="text", text=f"Grok API Error: {str(e)}")]
    
    async def get_claude_opinion(
        self,
        prompt: str,
        model: str = "claude-4-sonnet-20250514",
        temperature: float = 0.7,
        max_tokens: int = 8000,
        reset_conversation: bool = False,
        personality: str = None
    ) -> Sequence[TextContent]:
        """Get opinion from Claude model"""
        if not self.clients.claude_client:
            return [TextContent(type="text", text="Claude client not configured. Please set CLAUDE_API_KEY environment variable.")]
        
        try:
            conversation_key = self.conv.get_conversation_key("claude", model)
            
            # Reset conversation if requested
            if reset_conversation:
                self.conv.reset_conversation(conversation_key)
            
            # Build messages and system prompt
            messages, system_prompt = self.conv.get_claude_messages(conversation_key, prompt, None, personality)
            
            response = self.clients.claude_client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=messages
            )
            
            response_content = response.content[0].text
            
            # Add to conversation history
            self.conv.add_to_conversation_history(conversation_key, "user", prompt)
            self.conv.add_to_conversation_history(conversation_key, "assistant", response_content)
            
            result = f"**Anthropic Claude {model} Opinion:**\n\n{response_content}"
            return [TextContent(type="text", text=result)]
            
        except Exception as e:
            logger.error(f"Claude API Error: {str(e)}")
            return [TextContent(type="text", text=f"Claude API Error: {str(e)}")]
    
    async def get_huggingface_opinion(
        self,
        prompt: str,
        model: str = "meta-llama/Llama-3.3-70B-Instruct",
        temperature: float = 0.7,
        max_tokens: int = 8000,
        reset_conversation: bool = False,
        personality: str = None
    ) -> Sequence[TextContent]:
        """Get opinion from HuggingFace model"""
        if not self.clients.huggingface_api_key:
            return [TextContent(type="text", text="HuggingFace API key not configured. Please set HUGGINGFACE_API_KEY environment variable.")]
        
        try:
            conversation_key = self.conv.get_conversation_key("huggingface", model)
            
            # Reset conversation if requested
            if reset_conversation:
                self.conv.reset_conversation(conversation_key)
            
            # Build messages with conversation history
            messages = self.conv.get_openai_messages(conversation_key, prompt, None, personality)
            
            # Format for HuggingFace API
            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": False
            }
            
            headers = {
                "Authorization": f"Bearer {self.clients.huggingface_api_key}",
                "Content-Type": "application/json"
            }
            
            # Make request with retries
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = requests.post(
                        f"https://api-inference.huggingface.co/models/{model}/v1/chat/completions",
                        json=payload,
                        headers=headers,
                        timeout=60
                    )
                    
                    if response.status_code == 200:
                        response_data = response.json()
                        if "choices" in response_data and len(response_data["choices"]) > 0:
                            response_content = response_data["choices"][0]["message"]["content"]
                            
                            # Add to conversation history
                            self.conv.add_to_conversation_history(conversation_key, "user", prompt)
                            self.conv.add_to_conversation_history(conversation_key, "assistant", response_content)
                            
                            result = f"**HuggingFace {model} Opinion:**\n\n{response_content}"
                            return [TextContent(type="text", text=result)]
                    
                    elif response.status_code == 503:
                        # Model loading, wait and retry
                        if attempt < max_retries - 1:
                            wait_time = 10 * (attempt + 1)
                            logger.info(f"HuggingFace model loading, waiting {wait_time}s before retry...")
                            await asyncio.sleep(wait_time)
                            continue
                    
                    # If we get here, there was an error
                    error_msg = f"HuggingFace API returned status {response.status_code}: {response.text}"
                    if attempt == max_retries - 1:
                        return [TextContent(type="text", text=error_msg)]
                    
                except requests.exceptions.Timeout:
                    if attempt == max_retries - 1:
                        return [TextContent(type="text", text="HuggingFace API request timed out")]
                    await asyncio.sleep(5)
                    
        except Exception as e:
            logger.error(f"HuggingFace API Error: {str(e)}")
            return [TextContent(type="text", text=f"HuggingFace API Error: {str(e)}")]
    
    async def get_deepseek_opinion(
        self,
        prompt: str,
        model: str = "deepseek-chat",
        temperature: float = 0.7,
        max_tokens: int = 8000,
        system_prompt: str = "",
        reset_conversation: bool = False,
        personality: str = None
    ) -> Sequence[TextContent]:
        """Get opinion from DeepSeek model"""
        if not self.clients.deepseek_client:
            return [TextContent(type="text", text="DeepSeek client not configured. Please set DEEPSEEK_API_KEY environment variable.")]
        
        try:
            conversation_key = self.conv.get_conversation_key("deepseek", model)
            
            # Reset conversation if requested
            if reset_conversation:
                self.conv.reset_conversation(conversation_key)
            
            # Build messages with conversation history
            messages = self.conv.get_openai_messages(conversation_key, prompt, system_prompt, personality)
            
            response = self.clients.deepseek_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            response_content = response.choices[0].message.content
            
            # Add to conversation history
            self.conv.add_to_conversation_history(conversation_key, "user", prompt)
            self.conv.add_to_conversation_history(conversation_key, "assistant", response_content)
            
            result = f"**DeepSeek {model} Opinion:**\n\n{response_content}"
            return [TextContent(type="text", text=result)]
            
        except Exception as e:
            logger.error(f"DeepSeek API Error: {str(e)}")
            return [TextContent(type="text", text=f"DeepSeek API Error: {str(e)}")]
    
    async def get_default_opinion(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 8000,
        personality: str = None,
        reset_conversation: bool = False
    ) -> Sequence[TextContent]:
        """Get opinion from the best available model based on quality ranking"""
        # Get the best available model using our intelligent selection
        best_model = self._get_best_available_model(personality)
        
        if not best_model:
            return [TextContent(type="text", text="No AI models are currently available. Please configure at least one API key.")]
        
        platform, model = best_model
        
        # Route to appropriate method based on platform
        try:
            if platform == "openai":
                return await self.get_openai_opinion(prompt, model, temperature, max_tokens, "", reset_conversation, personality)
            elif platform == "gemini":
                return await self.get_gemini_opinion(prompt, model, temperature, max_tokens, reset_conversation, personality)
            elif platform == "grok":
                return await self.get_grok_opinion(prompt, model, temperature, max_tokens, "", reset_conversation, personality)
            elif platform == "claude":
                return await self.get_claude_opinion(prompt, model, temperature, max_tokens, reset_conversation, personality)
            elif platform == "deepseek":
                return await self.get_deepseek_opinion(prompt, model, temperature, max_tokens, "", reset_conversation, personality)
            elif platform == "groq_fast":
                return await self.get_groq_fast_opinion(prompt, model, temperature, max_tokens, "", reset_conversation, personality)
            elif platform == "perplexity":
                return await self.get_perplexity_opinion(prompt, model, temperature, max_tokens, "", reset_conversation, personality)
            elif platform == "huggingface":
                return await self.get_huggingface_opinion(prompt, model, temperature, max_tokens, reset_conversation, personality)
            elif platform == "openrouter":
                return await self.get_openrouter_opinion(prompt, model, temperature, max_tokens, "", reset_conversation, personality)
            elif platform == "chutes":
                return await self.get_chutes_opinion(prompt, model, temperature, max_tokens, "", reset_conversation, personality)
            elif platform == "ollama":
                return [TextContent(type="text", text=f"Ollama integration not yet implemented in default selection. Platform: {platform}, Model: {model}")]
            else:
                return [TextContent(type="text", text=f"Platform {platform} not yet supported in default selection.")]
        except Exception as e:
            logger.error(f"Error calling {platform}/{model}: {str(e)}")
            return [TextContent(type="text", text=f"Error using {platform}/{model}: {str(e)}")]
    
    # Additional AI providers (simplified versions for space)
    async def get_groq_fast_opinion(self, prompt: str, model: str = "llama-3.1-70b-versatile", temperature: float = 0.7, max_tokens: int = 8000, system_prompt: str = "", reset_conversation: bool = False, personality: str = None) -> Sequence[TextContent]:
        """Get opinion from Groq Fast model"""
        if not self.clients.groq_client_fast:
            return [TextContent(type="text", text="Groq Fast client not configured. Please set GROQ_FAST_API_KEY environment variable.")]
        
        try:
            conversation_key = self.conv.get_conversation_key("groq_fast", model)
            if reset_conversation:
                self.conv.reset_conversation(conversation_key)
            
            messages = self.conv.get_openai_messages(conversation_key, prompt, system_prompt, personality)
            
            response = self.clients.groq_client_fast.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            response_content = response.choices[0].message.content
            self.conv.add_to_conversation_history(conversation_key, "user", prompt)
            self.conv.add_to_conversation_history(conversation_key, "assistant", response_content)
            
            result = f"**Groq Fast {model} Opinion:**\n\n{response_content}"
            return [TextContent(type="text", text=result)]
            
        except Exception as e:
            logger.error(f"Groq Fast API Error: {str(e)}")
            return [TextContent(type="text", text=f"Groq Fast API Error: {str(e)}")]
    
    async def get_perplexity_opinion(self, prompt: str, model: str = "llama-3.1-sonar-large-128k-online", temperature: float = 0.7, max_tokens: int = 8000, system_prompt: str = "", reset_conversation: bool = False, personality: str = None) -> Sequence[TextContent]:
        """Get opinion from Perplexity model"""
        if not self.clients.perplexity_client:
            return [TextContent(type="text", text="Perplexity client not configured. Please set PERPLEXITY_API_KEY environment variable.")]
        
        try:
            conversation_key = self.conv.get_conversation_key("perplexity", model)
            if reset_conversation:
                self.conv.reset_conversation(conversation_key)
            
            messages = self.conv.get_openai_messages(conversation_key, prompt, system_prompt, personality)
            
            response = self.clients.perplexity_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            response_content = response.choices[0].message.content
            self.conv.add_to_conversation_history(conversation_key, "user", prompt)
            self.conv.add_to_conversation_history(conversation_key, "assistant", response_content)
            
            result = f"**Perplexity {model} Opinion:**\n\n{response_content}"
            return [TextContent(type="text", text=result)]
            
        except Exception as e:
            logger.error(f"Perplexity API Error: {str(e)}")
            return [TextContent(type="text", text=f"Perplexity API Error: {str(e)}")]
    
    async def get_openrouter_opinion(
        self,
        prompt: str,
        model: str = "anthropic/claude-3-5-sonnet-20241022",
        temperature: float = 0.7,
        max_tokens: int = 8000,
        system_prompt: str = "",
        reset_conversation: bool = False,
        personality: str = None
    ) -> Sequence[TextContent]:
        """Get opinion from OpenRouter model"""
        if not self.clients.openrouter_client:
            return [TextContent(type="text", text="OpenRouter client not configured. Please set OPENROUTER_API_KEY environment variable.")]
        
        try:
            conversation_key = self.conv.get_conversation_key("openrouter", model)
            
            # Reset conversation if requested
            if reset_conversation:
                self.conv.reset_conversation(conversation_key)
            
            # Build messages with conversation history
            messages = self.conv.get_openai_messages(conversation_key, prompt, system_prompt, personality)
            
            response = self.clients.openrouter_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            response_content = response.choices[0].message.content
            
            # Add to conversation history
            self.conv.add_to_conversation_history(conversation_key, "user", prompt)
            self.conv.add_to_conversation_history(conversation_key, "assistant", response_content)
            
            result = f"**OpenRouter {model} Opinion:**\n\n{response_content}"
            return [TextContent(type="text", text=result)]
            
        except Exception as e:
            logger.error(f"OpenRouter API Error: {str(e)}")
            return [TextContent(type="text", text=f"OpenRouter API Error: {str(e)}")]
    
    async def get_chutes_opinion(
        self,
        prompt: str,
        model: str = "moonshotai/Kimi-K2-Thinking",
        temperature: float = 0.7,
        max_tokens: int = 8000,
        system_prompt: str = "",
        reset_conversation: bool = False,
        personality: str = None
    ) -> Sequence[TextContent]:
        """Get opinion from Chutes AI model"""
        if not self.clients.chutes_client:
            return [TextContent(type="text", text="Chutes AI client not configured. Please set CHUTES_API_KEY environment variable.")]
        
        try:
            conversation_key = self.conv.get_conversation_key("chutes", model)
            
            # Reset conversation if requested
            if reset_conversation:
                self.conv.reset_conversation(conversation_key)
            
            # Build messages with conversation history
            messages = self.conv.get_openai_messages(conversation_key, prompt, system_prompt, personality)
            
            response = self.clients.chutes_client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            response_content = response.choices[0].message.content
            
            # Add to conversation history
            self.conv.add_to_conversation_history(conversation_key, "user", prompt)
            self.conv.add_to_conversation_history(conversation_key, "assistant", response_content)
            
            result = f"**Chutes AI {model} Opinion:**\n\n{response_content}"
            return [TextContent(type="text", text=result)]
            
        except Exception as e:
            logger.error(f"Chutes AI API Error: {str(e)}")
            return [TextContent(type="text", text=f"Chutes AI API Error: {str(e)}")]