"""
MCP Server for YouTube Analytics

Exposes YouTube analytics data to Claude Desktop via Model Context Protocol.
Enables AI-driven insights and analysis of video performance.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import json

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    EmptyResult,
)

# Import internal services
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.services.youtube_uploader.analytics import YouTubeAnalytics
from src.database.models import Video, YouTubeAccount
from src.database.database import SessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("youtube-analytics-mcp")


class YouTubeAnalyticsMCPServer:
    """
    MCP Server for YouTube Analytics
    
    Exposes:
    - Resources: Video performance data, channel analytics
    - Tools: Query analytics, generate reports, compare videos
    - Prompts: Analysis templates for common queries
    """
    
    def __init__(self):
        self.server = Server("youtube-analytics-server")
        self.analytics = None
        self.db = SessionLocal()
        
        # Register handlers
        self._register_handlers()
        
        logger.info("YouTube Analytics MCP Server initialized")
    
    def _register_handlers(self):
        """Register MCP protocol handlers"""
        
        @self.server.list_resources()
        async def handle_list_resources() -> List[Resource]:
            """List available analytics resources"""
            resources = []
            
            # Get all videos with analytics
            videos = self.db.query(Video).all()
            
            for video in videos:
                if video.youtube_video_id:
                    resources.append(
                        Resource(
                            uri=f"youtube://video/{video.youtube_video_id}/analytics",
                            name=f"Analytics: {video.title}",
                            description=f"Performance metrics for {video.title}",
                            mimeType="application/json"
                        )
                    )
            
            # Add channel-level resource
            resources.append(
                Resource(
                    uri="youtube://channel/analytics",
                    name="Channel Analytics",
                    description="Overall channel performance metrics",
                    mimeType="application/json"
                )
            )
            
            return resources
        
        @self.server.read_resource()
        async def handle_read_resource(uri: str) -> str:
            """Read analytics data for a resource"""
            
            if uri.startswith("youtube://video/"):
                # Extract video ID
                video_id = uri.split("/")[3]
                
                # Get analytics
                analytics_data = await self._get_video_analytics(video_id)
                return json.dumps(analytics_data, indent=2)
            
            elif uri == "youtube://channel/analytics":
                # Get channel analytics
                channel_data = await self._get_channel_analytics()
                return json.dumps(channel_data, indent=2)
            
            else:
                raise ValueError(f"Unknown resource URI: {uri}")
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """List available analytics tools"""
            return [
                Tool(
                    name="get_video_performance",
                    description="Get detailed performance metrics for a specific video",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "video_id": {
                                "type": "string",
                                "description": "YouTube video ID"
                            },
                            "days": {
                                "type": "integer",
                                "description": "Number of days to analyze (default: 30)",
                                "default": 30
                            }
                        },
                        "required": ["video_id"]
                    }
                ),
                Tool(
                    name="compare_videos",
                    description="Compare performance of multiple videos",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "video_ids": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of YouTube video IDs to compare"
                            },
                            "metrics": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Metrics to compare (views, watch_time, engagement)",
                                "default": ["views", "watch_time", "likes"]
                            }
                        },
                        "required": ["video_ids"]
                    }
                ),
                Tool(
                    name="get_trending_content",
                    description="Get trending videos from the channel",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "limit": {
                                "type": "integer",
                                "description": "Number of trending videos to return",
                                "default": 10
                            },
                            "metric": {
                                "type": "string",
                                "description": "Metric to sort by (views, engagement, ctr)",
                                "default": "views"
                            }
                        }
                    }
                ),
                Tool(
                    name="analyze_audience",
                    description="Analyze audience demographics and behavior",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "video_id": {
                                "type": "string",
                                "description": "Optional specific video ID"
                            }
                        }
                    }
                ),
                Tool(
                    name="generate_insights",
                    description="Generate AI insights from analytics data",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "timeframe": {
                                "type": "string",
                                "description": "Timeframe for analysis (7d, 30d, 90d)",
                                "default": "30d"
                            }
                        }
                    }
                ),
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> List[TextContent]:
            """Handle tool execution"""
            
            if name == "get_video_performance":
                result = await self._tool_get_video_performance(arguments)
            
            elif name == "compare_videos":
                result = await self._tool_compare_videos(arguments)
            
            elif name == "get_trending_content":
                result = await self._tool_get_trending_content(arguments)
            
            elif name == "analyze_audience":
                result = await self._tool_analyze_audience(arguments)
            
            elif name == "generate_insights":
                result = await self._tool_generate_insights(arguments)
            
            else:
                raise ValueError(f"Unknown tool: {name}")
            
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    # ===================================================================
    # Tool Implementations
    # ===================================================================
    
    async def _tool_get_video_performance(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get video performance metrics"""
        video_id = args["video_id"]
        days = args.get("days", 30)
        
        analytics_data = await self._get_video_analytics(video_id, days)
        
        return {
            "video_id": video_id,
            "timeframe_days": days,
            "analytics": analytics_data
        }
    
    async def _tool_compare_videos(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Compare multiple videos"""
        video_ids = args["video_ids"]
        metrics = args.get("metrics", ["views", "watch_time", "likes"])
        
        comparison = {}
        
        for video_id in video_ids:
            analytics = await self._get_video_analytics(video_id)
            comparison[video_id] = {
                metric: analytics.get(metric, 0)
                for metric in metrics
            }
        
        return {
            "videos": comparison,
            "metrics": metrics,
            "winner": self._determine_winner(comparison, metrics[0])
        }
    
    async def _tool_get_trending_content(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get trending videos"""
        limit = args.get("limit", 10)
        metric = args.get("metric", "views")
        
        videos = self.db.query(Video).filter(
            Video.youtube_video_id.isnot(None)
        ).all()
        
        # Get analytics for each video
        video_metrics = []
        for video in videos:
            analytics = await self._get_video_analytics(video.youtube_video_id)
            video_metrics.append({
                "video_id": video.youtube_video_id,
                "title": video.title,
                "metric_value": analytics.get(metric, 0),
                "analytics": analytics
            })
        
        # Sort by metric
        sorted_videos = sorted(
            video_metrics,
            key=lambda x: x["metric_value"],
            reverse=True
        )[:limit]
        
        return {
            "trending_videos": sorted_videos,
            "sorted_by": metric,
            "count": len(sorted_videos)
        }
    
    async def _tool_analyze_audience(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze audience demographics"""
        video_id = args.get("video_id")
        
        if video_id:
            # Specific video audience
            analytics = await self._get_video_analytics(video_id)
            return {
                "video_id": video_id,
                "audience": analytics.get("demographics", {}),
                "engagement_rate": analytics.get("engagement_rate", 0)
            }
        else:
            # Channel-wide audience
            channel_data = await self._get_channel_analytics()
            return {
                "channel_audience": channel_data.get("demographics", {}),
                "total_subscribers": channel_data.get("subscriber_count", 0)
            }
    
    async def _tool_generate_insights(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI insights from data"""
        timeframe = args.get("timeframe", "30d")
        
        # Get channel analytics
        channel_data = await self._get_channel_analytics()
        
        # Get top videos
        trending = await self._tool_get_trending_content({"limit": 5})
        
        # Generate insights
        insights = {
            "timeframe": timeframe,
            "summary": {
                "total_videos": len(channel_data.get("videos", [])),
                "total_views": channel_data.get("total_views", 0),
                "avg_views_per_video": channel_data.get("avg_views", 0),
            },
            "top_performers": trending["trending_videos"],
            "recommendations": [
                "Focus on topics similar to top-performing videos",
                "Improve CTR by optimizing thumbnails",
                "Increase watch time with better video structure",
            ]
        }
        
        return insights
    
    # ===================================================================
    # Helper Methods
    # ===================================================================
    
    async def _get_video_analytics(
        self,
        video_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Fetch analytics for a specific video"""
        
        # Get video from database
        video = self.db.query(Video).filter(
            Video.youtube_video_id == video_id
        ).first()
        
        if not video:
            return {"error": "Video not found"}
        
        # Get YouTube account
        if not video.youtube_account_id:
            return {"error": "No YouTube account associated"}
        
        account = self.db.query(YouTubeAccount).filter(
            YouTubeAccount.id == video.youtube_account_id
        ).first()
        
        if not account:
            return {"error": "YouTube account not found"}
        
        # Initialize analytics service
        if not self.analytics:
            self.analytics = YouTubeAnalytics(self.db)
        
        # Fetch analytics
        try:
            analytics = await self.analytics.get_video_analytics(
                video_id=video_id,
                days=days
            )
            return analytics
        except Exception as e:
            logger.error(f"Error fetching analytics: {e}")
            return {"error": str(e)}
    
    async def _get_channel_analytics(self) -> Dict[str, Any]:
        """Fetch channel-level analytics"""
        
        if not self.analytics:
            self.analytics = YouTubeAnalytics(self.db)
        
        try:
            # Get first YouTube account (assuming single account for now)
            account = self.db.query(YouTubeAccount).first()
            
            if not account:
                return {"error": "No YouTube account found"}
            
            analytics = await self.analytics.get_channel_analytics(
                account.channel_id
            )
            return analytics
        except Exception as e:
            logger.error(f"Error fetching channel analytics: {e}")
            return {"error": str(e)}
    
    def _determine_winner(
        self,
        comparison: Dict[str, Dict[str, Any]],
        metric: str
    ) -> str:
        """Determine which video performs best"""
        winner_id = max(
            comparison.items(),
            key=lambda x: x[1].get(metric, 0)
        )[0]
        return winner_id
    
    async def run(self):
        """Run the MCP server"""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="youtube-analytics",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )


# ===================================================================
# Main Execution
# ===================================================================

async def main():
    """Main execution"""
    server = YouTubeAnalyticsMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
