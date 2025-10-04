"""
Faceless YouTube - Ollama Client

Local AI client for script generation using Ollama.
"""

import asyncio
import aiohttp
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, AsyncIterator
from datetime import datetime

from pydantic import BaseModel, Field


@dataclass
class OllamaConfig:
    """Configuration for Ollama client"""
    
    # Connection settings
    host: str = "localhost"
    port: int = 11434
    timeout: int = 300  # 5 minutes for generation
    
    # Model settings
    model: str = "mistral"  # Default model
    temperature: float = 0.7  # Creativity (0.0-1.0)
    top_p: float = 0.9  # Nucleus sampling
    top_k: int = 40  # Top-k sampling
    num_predict: int = 2048  # Max tokens to generate
    
    # Performance
    num_ctx: int = 4096  # Context window size
    num_thread: Optional[int] = None  # CPU threads (None = auto)
    num_gpu: int = 1  # Number of GPUs to use
    
    # Streaming
    stream: bool = False  # Enable streaming responses
    
    @property
    def base_url(self) -> str:
        """Get base URL for Ollama API"""
        return f"http://{self.host}:{self.port}"


class OllamaResponse(BaseModel):
    """Response from Ollama API"""
    
    model: str
    created_at: str
    response: str
    done: bool
    context: Optional[List[int]] = None
    total_duration: Optional[int] = None
    load_duration: Optional[int] = None
    prompt_eval_count: Optional[int] = None
    prompt_eval_duration: Optional[int] = None
    eval_count: Optional[int] = None
    eval_duration: Optional[int] = None


class OllamaClient:
    """
    Client for interacting with Ollama local AI models.
    
    Features:
    - Generate text completions
    - Stream responses
    - Model management (list, pull, delete)
    - Context preservation for conversations
    - Automatic retry logic
    """
    
    def __init__(self, config: Optional[OllamaConfig] = None):
        """
        Initialize Ollama client.
        
        Args:
            config: Optional configuration (uses defaults if None)
        """
        self.config = config or OllamaConfig()
        self._session: Optional[aiohttp.ClientSession] = None
        self._context: Optional[List[int]] = None  # For conversation context
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session
    
    async def close(self) -> None:
        """Close HTTP session"""
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        preserve_context: bool = False,
        **kwargs
    ) -> str:
        """
        Generate text completion from prompt.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system instructions
            model: Model to use (defaults to config model)
            temperature: Temperature for generation (defaults to config)
            max_tokens: Max tokens to generate (defaults to config)
            preserve_context: Keep context for follow-up prompts
            **kwargs: Additional Ollama parameters
        
        Returns:
            Generated text
        
        Raises:
            aiohttp.ClientError: If request fails
        """
        session = await self._get_session()
        
        # Build request payload
        payload = {
            "model": model or self.config.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature or self.config.temperature,
                "top_p": self.config.top_p,
                "top_k": self.config.top_k,
                "num_predict": max_tokens or self.config.num_predict,
                "num_ctx": self.config.num_ctx,
            }
        }
        
        # Add system prompt if provided
        if system_prompt:
            payload["system"] = system_prompt
        
        # Add context for conversation continuity
        if preserve_context and self._context:
            payload["context"] = self._context
        
        # Add any custom parameters
        payload["options"].update(kwargs)
        
        # Make request
        url = f"{self.config.base_url}/api/generate"
        
        async with session.post(url, json=payload) as response:
            response.raise_for_status()
            data = await response.json()
            
            # Parse response
            ollama_response = OllamaResponse(**data)
            
            # Save context if requested
            if preserve_context and ollama_response.context:
                self._context = ollama_response.context
            
            return ollama_response.response
    
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Generate text with streaming responses.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system instructions
            model: Model to use
            temperature: Temperature for generation
            **kwargs: Additional parameters
        
        Yields:
            Text chunks as they're generated
        """
        session = await self._get_session()
        
        payload = {
            "model": model or self.config.model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": temperature or self.config.temperature,
                "top_p": self.config.top_p,
                "top_k": self.config.top_k,
                "num_predict": self.config.num_predict,
                "num_ctx": self.config.num_ctx,
            }
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        url = f"{self.config.base_url}/api/generate"
        
        async with session.post(url, json=payload) as response:
            response.raise_for_status()
            
            async for line in response.content:
                if line:
                    import json
                    data = json.loads(line.decode('utf-8'))
                    if 'response' in data:
                        yield data['response']
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> str:
        """
        Chat completion with message history.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
                     Example: [{"role": "user", "content": "Hello"}]
            model: Model to use
            temperature: Temperature for generation
            **kwargs: Additional parameters
        
        Returns:
            Generated response
        """
        session = await self._get_session()
        
        payload = {
            "model": model or self.config.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature or self.config.temperature,
                "top_p": self.config.top_p,
                "top_k": self.config.top_k,
                "num_predict": self.config.num_predict,
                "num_ctx": self.config.num_ctx,
            }
        }
        
        url = f"{self.config.base_url}/api/chat"
        
        async with session.post(url, json=payload) as response:
            response.raise_for_status()
            data = await response.json()
            
            return data['message']['content']
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """
        List available models.
        
        Returns:
            List of model information dicts
        """
        session = await self._get_session()
        url = f"{self.config.base_url}/api/tags"
        
        async with session.get(url) as response:
            response.raise_for_status()
            data = await response.json()
            return data.get('models', [])
    
    async def pull_model(self, model_name: str) -> None:
        """
        Pull/download a model from Ollama library.
        
        Args:
            model_name: Name of model to pull (e.g., 'mistral', 'llama2')
        """
        session = await self._get_session()
        url = f"{self.config.base_url}/api/pull"
        
        payload = {"name": model_name}
        
        async with session.post(url, json=payload) as response:
            response.raise_for_status()
            
            # Stream progress updates
            async for line in response.content:
                if line:
                    import json
                    data = json.loads(line.decode('utf-8'))
                    if 'status' in data:
                        print(f"Pull status: {data['status']}")
    
    async def delete_model(self, model_name: str) -> None:
        """
        Delete a model.
        
        Args:
            model_name: Name of model to delete
        """
        session = await self._get_session()
        url = f"{self.config.base_url}/api/delete"
        
        payload = {"name": model_name}
        
        async with session.delete(url, json=payload) as response:
            response.raise_for_status()
    
    async def show_model_info(self, model_name: str) -> Dict[str, Any]:
        """
        Get detailed information about a model.
        
        Args:
            model_name: Name of model
        
        Returns:
            Model information dict
        """
        session = await self._get_session()
        url = f"{self.config.base_url}/api/show"
        
        payload = {"name": model_name}
        
        async with session.post(url, json=payload) as response:
            response.raise_for_status()
            return await response.json()
    
    async def health_check(self) -> bool:
        """
        Check if Ollama server is running.
        
        Returns:
            True if server is healthy
        """
        try:
            session = await self._get_session()
            url = f"{self.config.base_url}/"
            
            async with session.get(url) as response:
                return response.status == 200
        except Exception:
            return False
    
    def reset_context(self) -> None:
        """Reset conversation context"""
        self._context = None
    
    async def embeddings(
        self,
        text: str,
        model: Optional[str] = None
    ) -> List[float]:
        """
        Generate embeddings for text.
        
        Args:
            text: Text to embed
            model: Model to use (must support embeddings)
        
        Returns:
            Embedding vector
        """
        session = await self._get_session()
        url = f"{self.config.base_url}/api/embeddings"
        
        payload = {
            "model": model or self.config.model,
            "prompt": text
        }
        
        async with session.post(url, json=payload) as response:
            response.raise_for_status()
            data = await response.json()
            return data.get('embedding', [])
