#!/usr/bin/env python3
"""
MCP Server Infrastructure for Second Opinion
Handles tool definitions, request routing, and MCP protocol implementation
"""

import asyncio
import json
import logging
from typing import List, Any, Dict, Sequence

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.types import Tool, TextContent

logger = logging.getLogger(__name__)


class MCPServer:
    """Handles MCP server infrastructure and tool management"""
    
    def __init__(self, client_manager, conversation_manager, ai_providers):
        """Initialize MCP server with component dependencies"""
        self.app = Server("second-opinion")
        self.client_manager = client_manager
        self.conversation_manager = conversation_manager
        self.ai_providers = ai_providers
        
        # Set up all MCP handlers
        self._setup_handlers()
        
        logger.info("MCP Server initialized")
    
    def _setup_handlers(self):
        """Set up MCP handlers and tool definitions"""
        
        @self.app.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """Return list of available tools based on configured clients"""
            tools = []
            
            # Core AI service tools
            if self.client_manager.openai_client:
                tools.extend(self._get_openai_tools())
            
            if self.client_manager.gemini_client:
                tools.extend(self._get_gemini_tools())
            
            if self.client_manager.grok_client:
                tools.extend(self._get_grok_tools())
            
            if self.client_manager.claude_client:
                tools.extend(self._get_claude_tools())
            
            if self.client_manager.huggingface_api_key:
                tools.extend(self._get_huggingface_tools())
            
            if self.client_manager.deepseek_client:
                tools.extend(self._get_deepseek_tools())
            
            if self.client_manager.openrouter_client:
                tools.extend(self._get_openrouter_tools())
            
            if self.client_manager.groq_client_fast:
                tools.extend(self._get_groq_fast_tools())
            
            if self.client_manager.perplexity_client:
                tools.extend(self._get_perplexity_tools())
            
            # Always add management tools
            tools.extend(self._get_management_tools())
            
            # Always add personality and default tools
            tools.extend(self._get_personality_tools())
            tools.extend(self._get_default_tools())
            
            logger.info(f"Listed {len(tools)} available tools")
            return tools
        
        @self.app.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> Sequence[TextContent]:
            """Route tool calls to appropriate handlers"""
            try:
                logger.info(f"Handling tool call: {name}")
                
                # OpenAI tools
                if name == "get_openai_opinion":
                    return await self.ai_providers.get_openai_opinion(**arguments)
                
                # Gemini tools
                elif name == "get_gemini_opinion":
                    return await self.ai_providers.get_gemini_opinion(**arguments)
                
                # Grok tools
                elif name == "get_grok_opinion":
                    return await self.ai_providers.get_grok_opinion(**arguments)
                
                # Claude tools
                elif name == "get_claude_opinion":
                    return await self.ai_providers.get_claude_opinion(**arguments)
                
                # HuggingFace tools
                elif name == "get_huggingface_opinion":
                    return await self.ai_providers.get_huggingface_opinion(**arguments)
                
                # DeepSeek tools
                elif name == "get_deepseek_opinion":
                    return await self.ai_providers.get_deepseek_opinion(**arguments)
                
                # OpenRouter tools
                elif name == "get_openrouter_opinion":
                    return await self.ai_providers.get_openrouter_opinion(**arguments)
                
                # Groq Fast tools
                elif name == "get_groq_fast_opinion":
                    return await self.ai_providers.get_groq_fast_opinion(**arguments)
                
                # Perplexity tools
                elif name == "get_perplexity_opinion":
                    return await self.ai_providers.get_perplexity_opinion(**arguments)
                
                # Default model tool
                elif name == "get_default_opinion":
                    return await self.ai_providers.get_default_opinion(**arguments)
                
                # Personality tools
                elif name == "get_personality_opinion":
                    return await self._handle_personality_opinion(**arguments)
                
                elif name == "list_personalities":
                    return await self._handle_list_personalities()
                
                # Conversation management tools
                elif name == "list_conversation_histories":
                    return await self._handle_list_conversations()
                
                elif name == "clear_conversation_history":
                    return await self._handle_clear_conversation(**arguments)
                
                else:
                    return [TextContent(type="text", text=f"Unknown tool: {name}")]
                    
            except Exception as e:
                logger.error(f"Error handling tool {name}: {str(e)}")
                return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    def _get_openai_tools(self) -> List[Tool]:
        """Get OpenAI tool definitions"""
        return [
            Tool(
                name="get_openai_opinion",
                description="Get a second opinion from an OpenAI model",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "The question or prompt to get an opinion on"
                        },
                        "model": {
                            "type": "string",
                            "description": "OpenAI model to use",
                            "enum": ["gpt-5:think", "gpt-5", "gpt-5-mini:think", "gpt-5-mini", "gpt-5-nano:think", "gpt-5-nano", "o4-mini", "gpt-4.1", "gpt-4o", "gpt-4o-mini"],
                            "default": "gpt-5"
                        },
                        "temperature": {
                            "type": "number",
                            "description": "Temperature for response randomness (0.0-2.0)",
                            "minimum": 0.0,
                            "maximum": 2.0,
                            "default": 0.7
                        },
                        "max_tokens": {
                            "type": "integer",
                            "description": "Maximum tokens in response",
                            "default": 8000
                        },
                        "system_prompt": {
                            "type": "string",
                            "description": "Optional system prompt to guide the response",
                            "default": ""
                        },
                        "reset_conversation": {
                            "type": "boolean",
                            "description": "Reset conversation history for this model",
                            "default": False
                        },
                        "personality": {
                            "type": "string",
                            "description": "Personality type for the AI response",
                            "enum": ["honest", "friend", "coach", "wise", "creative"],
                            "default": None
                        }
                    },
                    "required": ["prompt"]
                }
            )
        ]
    
    def _get_gemini_tools(self) -> List[Tool]:
        """Get Gemini tool definitions"""
        return [
            Tool(
                name="get_gemini_opinion",
                description="Get a second opinion from a Gemini model",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "The question or prompt to get an opinion on"
                        },
                        "model": {
                            "type": "string",
                            "description": "Gemini model to use",
                            "enum": ["gemini-2.5-flash-lite-preview-06-17", "gemini-2.5-flash", "gemini-2.5-pro"],
                            "default": "gemini-2.5-flash-lite-preview-06-17"
                        },
                        "temperature": {
                            "type": "number",
                            "description": "Temperature for response randomness (0.0-2.0)",
                            "minimum": 0.0,
                            "maximum": 2.0,
                            "default": 0.7
                        },
                        "max_output_tokens": {
                            "type": "integer",
                            "description": "Maximum tokens in response",
                            "default": 8000
                        },
                        "reset_conversation": {
                            "type": "boolean",
                            "description": "Reset conversation history for this model",
                            "default": False
                        },
                        "personality": {
                            "type": "string",
                            "description": "Personality type for the AI response",
                            "enum": ["honest", "friend", "coach", "wise", "creative"],
                            "default": None
                        }
                    },
                    "required": ["prompt"]
                }
            )
        ]
    
    def _get_grok_tools(self) -> List[Tool]:
        """Get Grok tool definitions"""
        return [
            Tool(
                name="get_grok_opinion",
                description="Get a second opinion from a Grok model (xAI)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "The question or prompt to get an opinion on"
                        },
                        "model": {
                            "type": "string",
                            "description": "Grok model to use",
                            "enum": ["grok-4", "grok-3", "grok-3-thinking", "grok-3-mini", "grok-2", "grok-beta"],
                            "default": "grok-4"
                        },
                        "temperature": {
                            "type": "number",
                            "description": "Temperature for response randomness (0.0-2.0)",
                            "minimum": 0.0,
                            "maximum": 2.0,
                            "default": 0.7
                        },
                        "max_tokens": {
                            "type": "integer",
                            "description": "Maximum tokens in response",
                            "default": 8000
                        },
                        "system_prompt": {
                            "type": "string",
                            "description": "Optional system prompt to guide the response",
                            "default": ""
                        },
                        "reset_conversation": {
                            "type": "boolean",
                            "description": "Reset conversation history for this model",
                            "default": False
                        },
                        "personality": {
                            "type": "string",
                            "description": "Personality type for the AI response",
                            "enum": ["honest", "friend", "coach", "wise", "creative"],
                            "default": None
                        },
                        "reasoning_effort": {
                            "type": "string",
                            "description": "Reasoning effort for thinking models",
                            "enum": ["low", "medium", "high"],
                            "default": "medium"
                        }
                    },
                    "required": ["prompt"]
                }
            )
        ]
    
    def _get_claude_tools(self) -> List[Tool]:
        """Get Claude tool definitions"""
        return [
            Tool(
                name="get_claude_opinion",
                description="Get a second opinion from a Claude model",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "The question or prompt to get an opinion on"
                        },
                        "model": {
                            "type": "string",
                            "description": "Claude model to use",
                            "enum": [
                                "claude-sonnet-4-20250514",
                                "claude-sonnet-4-5-20250929",
                                "claude-opus-4-20250514",
                                "claude-opus-4-1-20250805",
                                "claude-opus-4-5-20251101",
                                "claude-3-7-sonnet-20250219",
                                "claude-3-5-sonnet-20241022"
                            ],
                            "default": "claude-sonnet-4-20250514"
                        },
                        "temperature": {
                            "type": "number",
                            "description": "Temperature for response randomness (0.0-2.0)",
                            "minimum": 0.0,
                            "maximum": 2.0,
                            "default": 0.7
                        },
                        "max_tokens": {
                            "type": "integer",
                            "description": "Maximum tokens in response",
                            "default": 8000
                        },
                        "reset_conversation": {
                            "type": "boolean",
                            "description": "Reset conversation history for this model",
                            "default": False
                        },
                        "personality": {
                            "type": "string",
                            "description": "Personality type for the AI response",
                            "enum": ["honest", "friend", "coach", "wise", "creative"],
                            "default": None
                        }
                    },
                    "required": ["prompt"]
                }
            )
        ]
    
    def _get_huggingface_tools(self) -> List[Tool]:
        """Get HuggingFace tool definitions"""
        return [
            Tool(
                name="get_huggingface_opinion",
                description="Get a second opinion from any HuggingFace model",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "The question or prompt to get an opinion on"
                        },
                        "model": {
                            "type": "string",
                            "description": "HuggingFace model to use (e.g., 'meta-llama/Llama-3.3-70B-Instruct')",
                            "default": "meta-llama/Llama-3.3-70B-Instruct"
                        },
                        "temperature": {
                            "type": "number",
                            "description": "Temperature for response randomness (0.0-2.0)",
                            "minimum": 0.0,
                            "maximum": 2.0,
                            "default": 0.7
                        },
                        "max_tokens": {
                            "type": "integer",
                            "description": "Maximum tokens in response",
                            "default": 8000
                        },
                        "reset_conversation": {
                            "type": "boolean",
                            "description": "Reset conversation history for this model",
                            "default": False
                        },
                        "personality": {
                            "type": "string",
                            "description": "Personality type for the AI response",
                            "enum": ["honest", "friend", "coach", "wise", "creative"],
                            "default": None
                        }
                    },
                    "required": ["prompt", "model"]
                }
            )
        ]
    
    def _get_deepseek_tools(self) -> List[Tool]:
        """Get DeepSeek tool definitions"""
        return [
            Tool(
                name="get_deepseek_opinion",
                description="Get a second opinion from a DeepSeek model",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "The question or prompt to get an opinion on"
                        },
                        "model": {
                            "type": "string",
                            "description": "DeepSeek model to use",
                            "enum": ["deepseek-chat", "deepseek-reasoner"],
                            "default": "deepseek-chat"
                        },
                        "temperature": {
                            "type": "number",
                            "description": "Temperature for response randomness (0.0-2.0)",
                            "minimum": 0.0,
                            "maximum": 2.0,
                            "default": 0.7
                        },
                        "max_tokens": {
                            "type": "integer",
                            "description": "Maximum tokens in response",
                            "default": 8000
                        },
                        "system_prompt": {
                            "type": "string",
                            "description": "Optional system prompt to guide the response",
                            "default": ""
                        },
                        "reset_conversation": {
                            "type": "boolean",
                            "description": "Reset conversation history for this model",
                            "default": False
                        },
                        "personality": {
                            "type": "string",
                            "description": "Personality type for the AI response",
                            "enum": ["honest", "friend", "coach", "wise", "creative"],
                            "default": None
                        }
                    },
                    "required": ["prompt"]
                }
            )
        ]
    
    def _get_openrouter_tools(self) -> List[Tool]:
        """Get OpenRouter tool definitions"""
        return [
            Tool(
                name="get_openrouter_opinion",
                description="Get opinions from 200+ models via OpenRouter - Access to Claude, GPT, Llama, Gemini, and many more through one API",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "The question or prompt to get an opinion on"
                        },
                        "model": {
                            "type": "string",
                            "description": "OpenRouter model to use",
                            "default": "anthropic/claude-3-5-sonnet-20241022"
                        },
                        "temperature": {
                            "type": "number",
                            "description": "Temperature for response randomness (0.0-2.0)",
                            "minimum": 0.0,
                            "maximum": 2.0,
                            "default": 0.7
                        },
                        "max_tokens": {
                            "type": "integer",
                            "description": "Maximum tokens in response",
                            "default": 8000
                        },
                        "system_prompt": {
                            "type": "string",
                            "description": "Optional system prompt to guide the response",
                            "default": ""
                        },
                        "reset_conversation": {
                            "type": "boolean",
                            "description": "Reset conversation history for this model",
                            "default": False
                        },
                        "personality": {
                            "type": "string",
                            "description": "Personality type for the AI response",
                            "enum": ["honest", "friend", "coach", "wise", "creative"],
                            "default": None
                        }
                    },
                    "required": ["prompt"]
                }
            )
        ]
    
    def _get_groq_fast_tools(self) -> List[Tool]:
        """Get Groq Fast tool definitions"""
        return [
            Tool(
                name="get_groq_fast_opinion",
                description="Get ultra-fast responses from Groq",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "The question or prompt to get an opinion on"
                        },
                        "model": {
                            "type": "string",
                            "description": "Groq model to use",
                            "enum": ["llama-3.1-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768", "gemma2-9b-it"],
                            "default": "llama-3.1-70b-versatile"
                        },
                        "temperature": {
                            "type": "number",
                            "description": "Temperature for response randomness (0.0-2.0)",
                            "minimum": 0.0,
                            "maximum": 2.0,
                            "default": 0.7
                        },
                        "max_tokens": {
                            "type": "integer",
                            "description": "Maximum tokens in response",
                            "default": 8000
                        },
                        "system_prompt": {
                            "type": "string",
                            "description": "Optional system prompt to guide the response",
                            "default": ""
                        },
                        "reset_conversation": {
                            "type": "boolean",
                            "description": "Reset conversation history for this model",
                            "default": False
                        },
                        "personality": {
                            "type": "string",
                            "description": "Personality type for the AI response",
                            "enum": ["honest", "friend", "coach", "wise", "creative"],
                            "default": None
                        }
                    },
                    "required": ["prompt"]
                }
            )
        ]
    
    def _get_perplexity_tools(self) -> List[Tool]:
        """Get Perplexity tool definitions"""
        return [
            Tool(
                name="get_perplexity_opinion",
                description="Get web-connected AI responses from Perplexity",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "The question or prompt to get an opinion on"
                        },
                        "model": {
                            "type": "string",
                            "description": "Perplexity model to use",
                            "enum": ["llama-3.1-sonar-large-128k-online", "llama-3.1-sonar-small-128k-online", "llama-3.1-sonar-large-128k-chat", "llama-3.1-sonar-small-128k-chat"],
                            "default": "llama-3.1-sonar-large-128k-online"
                        },
                        "temperature": {
                            "type": "number",
                            "description": "Temperature for response randomness (0.0-2.0)",
                            "minimum": 0.0,
                            "maximum": 2.0,
                            "default": 0.7
                        },
                        "max_tokens": {
                            "type": "integer",
                            "description": "Maximum tokens in response",
                            "default": 8000
                        },
                        "system_prompt": {
                            "type": "string",
                            "description": "Optional system prompt to guide the response",
                            "default": ""
                        },
                        "reset_conversation": {
                            "type": "boolean",
                            "description": "Reset conversation history for this model",
                            "default": False
                        },
                        "personality": {
                            "type": "string",
                            "description": "Personality type for the AI response",
                            "enum": ["honest", "friend", "coach", "wise", "creative"],
                            "default": None
                        }
                    },
                    "required": ["prompt"]
                }
            )
        ]
    
    def _get_personality_tools(self) -> List[Tool]:
        """Get personality-related tool definitions"""
        return [
            Tool(
                name="get_personality_opinion",
                description="Get an AI opinion with a specific personality using the default available model",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "The question or prompt to get an opinion on"
                        },
                        "personality": {
                            "type": "string",
                            "description": "Personality type for the AI response",
                            "enum": ["honest", "friend", "coach", "wise", "creative"],
                            "default": "honest"
                        },
                        "temperature": {
                            "type": "number",
                            "description": "Temperature for response randomness (0.0-2.0)",
                            "minimum": 0.0,
                            "maximum": 2.0,
                            "default": 0.7
                        },
                        "max_tokens": {
                            "type": "integer",
                            "description": "Maximum tokens in response",
                            "default": 8000
                        },
                        "reset_conversation": {
                            "type": "boolean",
                            "description": "Reset conversation history for this model",
                            "default": False
                        }
                    },
                    "required": ["prompt", "personality"]
                }
            ),
            Tool(
                name="list_personalities",
                description="List all available personality types with descriptions",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            )
        ]
    
    def _get_default_tools(self) -> List[Tool]:
        """Get default model tool definitions"""
        return [
            Tool(
                name="get_default_opinion",
                description="Get an opinion from the default available AI model (automatically selects best available service)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "prompt": {
                            "type": "string",
                            "description": "The question or prompt to get an opinion on"
                        },
                        "temperature": {
                            "type": "number",
                            "description": "Temperature for response randomness (0.0-2.0)",
                            "minimum": 0.0,
                            "maximum": 2.0,
                            "default": 0.7
                        },
                        "max_tokens": {
                            "type": "integer",
                            "description": "Maximum tokens in response",
                            "default": 8000
                        },
                        "personality": {
                            "type": "string",
                            "description": "Personality type for the AI response",
                            "enum": ["honest", "friend", "coach", "wise", "creative"],
                            "default": None
                        },
                        "reset_conversation": {
                            "type": "boolean",
                            "description": "Reset conversation history for this model",
                            "default": False
                        }
                    },
                    "required": ["prompt"]
                }
            )
        ]
    
    def _get_management_tools(self) -> List[Tool]:
        """Get conversation management tool definitions"""
        return [
            Tool(
                name="list_conversation_histories",
                description="List all active conversation histories",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            ),
            Tool(
                name="clear_conversation_history",
                description="Clear conversation history for a specific AI model or all models",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "platform": {
                            "type": "string",
                            "description": "Platform to clear (openai, gemini, grok, claude, huggingface, deepseek, groq_fast, perplexity, or 'all')",
                            "enum": ["openai", "gemini", "grok", "claude", "huggingface", "deepseek", "groq_fast", "perplexity", "all"]
                        },
                        "model": {
                            "type": "string",
                            "description": "Specific model to clear (optional, clears all models for platform if not specified)"
                        }
                    },
                    "required": ["platform"]
                }
            )
        ]
    
    async def _handle_personality_opinion(self, **kwargs) -> Sequence[TextContent]:
        """Handle personality opinion requests"""
        return await self.ai_providers.get_default_opinion(**kwargs)
    
    async def _handle_list_personalities(self) -> Sequence[TextContent]:
        """Handle list personalities requests"""
        personalities = self.conversation_manager.get_available_personalities()
        personality_info = []
        
        for personality in personalities:
            description = self.conversation_manager.get_personality_description(personality)
            personality_info.append(f"**{personality}**: {description}")
        
        result = "Available AI Personalities:\n\n" + "\n\n".join(personality_info)
        return [TextContent(type="text", text=result)]
    
    async def _handle_list_conversations(self) -> Sequence[TextContent]:
        """Handle list conversation histories requests"""
        histories = self.conversation_manager.list_conversation_histories()
        
        if histories["total_conversations"] == 0:
            return [TextContent(type="text", text="No active conversation histories found.")]
        
        result = f"**Active Conversation Histories ({histories['total_conversations']} total):**\n\n"
        
        for key, info in histories["conversations"].items():
            result += f"**{info['platform']}/{info['model']}** ({info['message_count']} messages)\n"
            result += f"Last message: {info['last_message']}\n\n"
        
        return [TextContent(type="text", text=result)]
    
    async def _handle_clear_conversation(self, **kwargs) -> Sequence[TextContent]:
        """Handle clear conversation history requests"""
        result = self.conversation_manager.clear_conversation_history(**kwargs)
        return [TextContent(type="text", text=result["message"])]
    
    def get_app(self):
        """Return the MCP server app instance"""
        return self.app