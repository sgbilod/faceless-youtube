"""
Claude Pro API Integration

Provides access to Anthropic's Claude Pro API for:
- Architecture analysis and design discussions
- Long-context code reviews (200k tokens)
- Advanced reasoning tasks
- Documentation generation
- Strategic planning and decision support
"""

import os
import asyncio
from typing import List, Dict, Any, Optional, AsyncIterator
from datetime import datetime
from dataclasses import dataclass
import logging

try:
    from anthropic import Anthropic, AsyncAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    print("Warning: anthropic package not installed. Run: pip install anthropic")

logger = logging.getLogger(__name__)


@dataclass
class ClaudeMessage:
    """Represents a Claude chat message"""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime


@dataclass
class ClaudeResponse:
    """Represents a Claude API response"""
    content: str
    model: str
    tokens_used: int
    finish_reason: str
    latency_seconds: float


class ClaudeClient:
    """
    Client for interacting with Claude Pro API
    
    Features:
    - Synchronous and asynchronous message sending
    - Streaming support for long responses
    - Conversation context management
    - Long-context handling (200k tokens)
    - Retry logic and error handling
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-3-5-sonnet-20241022",  # Latest Claude 3.5 Sonnet
        max_tokens: int = 4096,
        temperature: float = 1.0
    ):
        """
        Initialize Claude client
        
        Args:
            api_key: Anthropic API key (or use ANTHROPIC_API_KEY env var)
            model: Claude model to use
            max_tokens: Maximum tokens in response
            temperature: Randomness (0.0 to 1.0)
        """
        if not ANTHROPIC_AVAILABLE:
            raise ImportError(
                "anthropic package required. Install with: pip install anthropic"
            )
        
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Anthropic API key required. Set ANTHROPIC_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        
        # Initialize clients
        self.client = Anthropic(api_key=self.api_key)
        self.async_client = AsyncAnthropic(api_key=self.api_key)
        
        # Conversation history
        self.conversation_history: List[ClaudeMessage] = []
        
        logger.info(f"Initialized ClaudeClient with model {self.model}")
    
    def add_message(self, role: str, content: str):
        """Add message to conversation history"""
        self.conversation_history.append(
            ClaudeMessage(
                role=role,
                content=content,
                timestamp=datetime.utcnow()
            )
        )
    
    def clear_conversation(self):
        """Clear conversation history"""
        self.conversation_history.clear()
    
    def send_message(
        self,
        message: str,
        system_prompt: Optional[str] = None,
        use_history: bool = True
    ) -> ClaudeResponse:
        """
        Send message to Claude (synchronous)
        
        Args:
            message: User message
            system_prompt: Optional system prompt for context
            use_history: Include conversation history
        
        Returns:
            ClaudeResponse with generated content
        """
        start_time = datetime.utcnow()
        
        # Build messages
        messages = []
        
        if use_history:
            messages.extend([
                {"role": msg.role, "content": msg.content}
                for msg in self.conversation_history
            ])
        
        messages.append({"role": "user", "content": message})
        
        # Make API call
        try:
            kwargs = {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "messages": messages
            }
            
            if system_prompt:
                kwargs["system"] = system_prompt
            
            response = self.client.messages.create(**kwargs)
            
            # Extract response
            content = response.content[0].text
            
            # Update conversation history
            self.add_message("user", message)
            self.add_message("assistant", content)
            
            # Calculate latency
            latency = (datetime.utcnow() - start_time).total_seconds()
            
            return ClaudeResponse(
                content=content,
                model=response.model,
                tokens_used=response.usage.input_tokens + response.usage.output_tokens,
                finish_reason=response.stop_reason,
                latency_seconds=latency
            )
            
        except Exception as e:
            logger.error(f"Claude API error: {e}", exc_info=True)
            raise
    
    async def send_message_async(
        self,
        message: str,
        system_prompt: Optional[str] = None,
        use_history: bool = True
    ) -> ClaudeResponse:
        """
        Send message to Claude (asynchronous)
        
        Args:
            message: User message
            system_prompt: Optional system prompt
            use_history: Include conversation history
        
        Returns:
            ClaudeResponse with generated content
        """
        start_time = datetime.utcnow()
        
        # Build messages
        messages = []
        
        if use_history:
            messages.extend([
                {"role": msg.role, "content": msg.content}
                for msg in self.conversation_history
            ])
        
        messages.append({"role": "user", "content": message})
        
        # Make async API call
        try:
            kwargs = {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "messages": messages
            }
            
            if system_prompt:
                kwargs["system"] = system_prompt
            
            response = await self.async_client.messages.create(**kwargs)
            
            # Extract response
            content = response.content[0].text
            
            # Update conversation history
            self.add_message("user", message)
            self.add_message("assistant", content)
            
            # Calculate latency
            latency = (datetime.utcnow() - start_time).total_seconds()
            
            return ClaudeResponse(
                content=content,
                model=response.model,
                tokens_used=response.usage.input_tokens + response.usage.output_tokens,
                finish_reason=response.stop_reason,
                latency_seconds=latency
            )
            
        except Exception as e:
            logger.error(f"Claude async API error: {e}", exc_info=True)
            raise
    
    async def stream_message(
        self,
        message: str,
        system_prompt: Optional[str] = None,
        use_history: bool = True
    ) -> AsyncIterator[str]:
        """
        Stream message response from Claude (for long responses)
        
        Args:
            message: User message
            system_prompt: Optional system prompt
            use_history: Include conversation history
        
        Yields:
            Text chunks as they arrive
        """
        # Build messages
        messages = []
        
        if use_history:
            messages.extend([
                {"role": msg.role, "content": msg.content}
                for msg in self.conversation_history
            ])
        
        messages.append({"role": "user", "content": message})
        
        # Stream response
        try:
            kwargs = {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "messages": messages
            }
            
            if system_prompt:
                kwargs["system"] = system_prompt
            
            full_response = ""
            
            async with self.async_client.messages.stream(**kwargs) as stream:
                async for text in stream.text_stream:
                    full_response += text
                    yield text
            
            # Update conversation history after streaming completes
            self.add_message("user", message)
            self.add_message("assistant", full_response)
            
        except Exception as e:
            logger.error(f"Claude streaming error: {e}", exc_info=True)
            raise
    
    # ===================================================================
    # Specialized Use Cases
    # ===================================================================
    
    async def analyze_architecture(self, code_or_description: str) -> str:
        """
        Use Claude to analyze system architecture
        
        Args:
            code_or_description: Code or architecture description
        
        Returns:
            Architecture analysis and recommendations
        """
        system_prompt = """You are an expert software architect specializing in 
        microservices, scalability, and clean architecture principles. Analyze the 
        provided architecture and provide detailed feedback on:
        - Design patterns used
        - Potential bottlenecks
        - Scalability concerns
        - Security considerations
        - Recommended improvements"""
        
        response = await self.send_message_async(
            message=f"Analyze this architecture:\n\n{code_or_description}",
            system_prompt=system_prompt,
            use_history=False
        )
        
        return response.content
    
    async def review_code(self, code: str, context: Optional[str] = None) -> str:
        """
        Use Claude to perform code review
        
        Args:
            code: Code to review
            context: Optional context about the code's purpose
        
        Returns:
            Code review with suggestions
        """
        system_prompt = """You are an expert code reviewer. Provide detailed feedback on:
        - Code quality and readability
        - Potential bugs or security issues
        - Performance optimizations
        - Best practices adherence
        - Testing recommendations"""
        
        message = f"Review this code:\n\n{code}"
        if context:
            message += f"\n\nContext: {context}"
        
        response = await self.send_message_async(
            message=message,
            system_prompt=system_prompt,
            use_history=False
        )
        
        return response.content
    
    async def generate_documentation(
        self,
        code: str,
        doc_type: str = "README"
    ) -> str:
        """
        Generate documentation using Claude
        
        Args:
            code: Code to document
            doc_type: Type of documentation (README, API, CONTRIBUTING, etc.)
        
        Returns:
            Generated documentation
        """
        system_prompt = f"""You are a technical writer expert in creating clear, 
        comprehensive documentation. Generate a {doc_type} document that is:
        - Clear and easy to understand
        - Well-structured with proper sections
        - Includes code examples where appropriate
        - Follows Markdown best practices"""
        
        response = await self.send_message_async(
            message=f"Generate {doc_type} documentation for this code:\n\n{code}",
            system_prompt=system_prompt,
            use_history=False
        )
        
        return response.content
    
    async def brainstorm_solutions(self, problem: str) -> str:
        """
        Brainstorm solutions to a technical problem
        
        Args:
            problem: Problem description
        
        Returns:
            Multiple solution approaches
        """
        system_prompt = """You are a creative problem solver with deep technical expertise. 
        For the given problem, provide multiple solution approaches with:
        - Pros and cons of each approach
        - Implementation complexity estimates
        - Recommended approach and reasoning"""
        
        response = await self.send_message_async(
            message=f"Help me solve this problem:\n\n{problem}",
            system_prompt=system_prompt,
            use_history=False
        )
        
        return response.content


# Example usage
if __name__ == "__main__":
    async def main():
        # Initialize Claude client
        client = ClaudeClient()
        
        # Example 1: Architecture analysis
        print("Example 1: Architecture Analysis")
        print("=" * 50)
        
        architecture = """
        I have a microservices architecture with:
        - FastAPI backend
        - PostgreSQL, MongoDB, Redis databases
        - Ollama for local LLM
        - Docker containerization
        - Planned Kubernetes deployment
        
        Is this a good approach for a YouTube automation platform?
        """
        
        analysis = await client.analyze_architecture(architecture)
        print(analysis)
        print("\n")
        
        # Example 2: Code review
        print("Example 2: Code Review")
        print("=" * 50)
        
        code = """
        def process_video(video_path):
            file = open(video_path, 'rb')
            data = file.read()
            result = analyze(data)
            return result
        """
        
        review = await client.review_code(code)
        print(review)
        print("\n")
        
        # Example 3: Streaming response
        print("Example 3: Streaming Response")
        print("=" * 50)
        
        print("Streaming: ", end="", flush=True)
        async for chunk in client.stream_message(
            "Explain the benefits of microservices in 3 paragraphs."
        ):
            print(chunk, end="", flush=True)
        print("\n")
    
    asyncio.run(main())
