"""
AI Integration Module

Premium AI service integrations for Doppelganger Studio:
- Claude Pro (Anthropic): Advanced reasoning, code analysis, architecture review
- Gemini Pro (Google): Multimodal AI, image/video analysis, SEO optimization
- Grok (xAI): Real-time trends, viral potential, niche discovery
"""

from .claude_client import ClaudeClient, ClaudeMessage, ClaudeResponse
from .gemini_client import GeminiClient, GeminiResponse, ImageAnalysis
from .grok_client import GrokClient, GrokResponse, TrendingTopic

__all__ = [
    # Claude Pro
    "ClaudeClient",
    "ClaudeMessage",
    "ClaudeResponse",
    
    # Gemini Pro
    "GeminiClient",
    "GeminiResponse",
    "ImageAnalysis",
    
    # Grok
    "GrokClient",
    "GrokResponse",
    "TrendingTopic",
]
