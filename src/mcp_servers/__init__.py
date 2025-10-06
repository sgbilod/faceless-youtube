"""
MCP Servers for Doppelganger Studio

Model Context Protocol servers exposing:
- YouTube Analytics data for AI-driven insights
- Video Generation Pipeline for workflow management
"""

from .youtube_analytics_server import YouTubeAnalyticsMCPServer
from .video_pipeline_server import VideoPipelineMCPServer

__all__ = [
    "YouTubeAnalyticsMCPServer",
    "VideoPipelineMCPServer",
]
