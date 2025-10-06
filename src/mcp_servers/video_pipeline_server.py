"""
MCP Server for Video Generation Pipeline

Exposes video generation pipeline data and controls to Claude Desktop.
Enables AI-driven workflow management and optimization.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
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

from src.services.script_generator import ScriptGenerator
from src.services.video_assembler import VideoAssembler
from src.services.tts_engine import TTSEngine
from src.services.asset_scraper import ScraperManager
from src.database.models import Video, VideoAsset, VideoJob
from src.database.database import SessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("video-pipeline-mcp")


class VideoPipelineMCPServer:
    """
    MCP Server for Video Generation Pipeline
    
    Exposes:
    - Resources: Video jobs, generated scripts, asset collections
    - Tools: Generate videos, manage pipeline, optimize workflows
    - Prompts: Templates for video creation
    """
    
    def __init__(self):
        self.server = Server("video-pipeline-server")
        self.db = SessionLocal()
        
        # Initialize services
        self.script_generator = ScriptGenerator()
        self.video_assembler = VideoAssembler()
        self.tts_engine = TTSEngine()
        self.scraper = ScraperManager()
        
        # Register handlers
        self._register_handlers()
        
        logger.info("Video Pipeline MCP Server initialized")
    
    def _register_handlers(self):
        """Register MCP protocol handlers"""
        
        @self.server.list_resources()
        async def handle_list_resources() -> List[Resource]:
            """List available pipeline resources"""
            resources = []
            
            # Get all video jobs
            jobs = self.db.query(VideoJob).order_by(
                VideoJob.created_at.desc()
            ).limit(50).all()
            
            for job in jobs:
                resources.append(
                    Resource(
                        uri=f"pipeline://job/{job.id}",
                        name=f"Job {job.id}: {job.status}",
                        description=f"Video generation job - {job.status}",
                        mimeType="application/json"
                    )
                )
            
            # Get all generated videos
            videos = self.db.query(Video).order_by(
                Video.created_at.desc()
            ).limit(50).all()
            
            for video in videos:
                resources.append(
                    Resource(
                        uri=f"pipeline://video/{video.id}",
                        name=f"Video: {video.title}",
                        description=f"Generated video - {video.status}",
                        mimeType="application/json"
                    )
                )
            
            return resources
        
        @self.server.read_resource()
        async def handle_read_resource(uri: str) -> str:
            """Read pipeline resource data"""
            
            if uri.startswith("pipeline://job/"):
                # Get job details
                job_id = int(uri.split("/")[-1])
                job_data = await self._get_job_details(job_id)
                return json.dumps(job_data, indent=2)
            
            elif uri.startswith("pipeline://video/"):
                # Get video details
                video_id = int(uri.split("/")[-1])
                video_data = await self._get_video_details(video_id)
                return json.dumps(video_data, indent=2)
            
            else:
                raise ValueError(f"Unknown resource URI: {uri}")
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """List available pipeline tools"""
            return [
                Tool(
                    name="create_video",
                    description="Create a new video with AI-generated script and assets",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "topic": {
                                "type": "string",
                                "description": "Video topic or theme"
                            },
                            "duration": {
                                "type": "integer",
                                "description": "Target duration in seconds",
                                "default": 60
                            },
                            "niche": {
                                "type": "string",
                                "description": "Video niche (meditation, tutorial, etc.)",
                                "default": "meditation"
                            },
                            "voice": {
                                "type": "string",
                                "description": "Voice to use for narration",
                                "default": "alloy"
                            }
                        },
                        "required": ["topic"]
                    }
                ),
                Tool(
                    name="get_job_status",
                    description="Get status and progress of a video generation job",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "job_id": {
                                "type": "integer",
                                "description": "Job ID to check"
                            }
                        },
                        "required": ["job_id"]
                    }
                ),
                Tool(
                    name="generate_script",
                    description="Generate AI script without creating full video",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "topic": {
                                "type": "string",
                                "description": "Script topic"
                            },
                            "duration": {
                                "type": "integer",
                                "description": "Target duration in seconds",
                                "default": 60
                            },
                            "style": {
                                "type": "string",
                                "description": "Script style (calm, energetic, etc.)",
                                "default": "calm"
                            }
                        },
                        "required": ["topic"]
                    }
                ),
                Tool(
                    name="search_assets",
                    description="Search for video/audio assets matching criteria",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query"
                            },
                            "asset_type": {
                                "type": "string",
                                "description": "Asset type (video, audio, image)",
                                "default": "video"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum results",
                                "default": 10
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="optimize_pipeline",
                    description="Analyze and suggest pipeline optimizations",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "analysis_type": {
                                "type": "string",
                                "description": "Type of analysis (performance, quality, cost)",
                                "default": "performance"
                            }
                        }
                    }
                ),
                Tool(
                    name="get_pipeline_stats",
                    description="Get overall pipeline statistics and metrics",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "days": {
                                "type": "integer",
                                "description": "Number of days to analyze",
                                "default": 30
                            }
                        }
                    }
                ),
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> List[TextContent]:
            """Handle tool execution"""
            
            if name == "create_video":
                result = await self._tool_create_video(arguments)
            
            elif name == "get_job_status":
                result = await self._tool_get_job_status(arguments)
            
            elif name == "generate_script":
                result = await self._tool_generate_script(arguments)
            
            elif name == "search_assets":
                result = await self._tool_search_assets(arguments)
            
            elif name == "optimize_pipeline":
                result = await self._tool_optimize_pipeline(arguments)
            
            elif name == "get_pipeline_stats":
                result = await self._tool_get_pipeline_stats(arguments)
            
            else:
                raise ValueError(f"Unknown tool: {name}")
            
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    # ===================================================================
    # Tool Implementations
    # ===================================================================
    
    async def _tool_create_video(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new video"""
        topic = args["topic"]
        duration = args.get("duration", 60)
        niche = args.get("niche", "meditation")
        voice = args.get("voice", "alloy")
        
        try:
            # Generate script
            logger.info(f"Generating script for topic: {topic}")
            script = await self.script_generator.generate(
                topic=topic,
                duration=duration,
                style=niche
            )
            
            # Create video record
            video = Video(
                title=f"{topic} - {niche.title()}",
                script=script["text"],
                niche=niche,
                target_duration=duration,
                status="pending",
                voice=voice
            )
            self.db.add(video)
            self.db.commit()
            
            # Create video job
            job = VideoJob(
                video_id=video.id,
                status="queued",
                progress=0
            )
            self.db.add(job)
            self.db.commit()
            
            return {
                "success": True,
                "video_id": video.id,
                "job_id": job.id,
                "script": script["text"][:200] + "...",
                "message": "Video generation queued"
            }
            
        except Exception as e:
            logger.error(f"Error creating video: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _tool_get_job_status(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get job status"""
        job_id = args["job_id"]
        
        job = self.db.query(VideoJob).filter(VideoJob.id == job_id).first()
        
        if not job:
            return {"error": "Job not found"}
        
        return {
            "job_id": job.id,
            "status": job.status,
            "progress": job.progress,
            "video_id": job.video_id,
            "created_at": job.created_at.isoformat(),
            "updated_at": job.updated_at.isoformat() if job.updated_at else None
        }
    
    async def _tool_generate_script(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Generate script only"""
        topic = args["topic"]
        duration = args.get("duration", 60)
        style = args.get("style", "calm")
        
        try:
            script = await self.script_generator.generate(
                topic=topic,
                duration=duration,
                style=style
            )
            
            return {
                "success": True,
                "script": script["text"],
                "word_count": len(script["text"].split()),
                "estimated_duration": script.get("estimated_duration", duration)
            }
            
        except Exception as e:
            logger.error(f"Error generating script: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _tool_search_assets(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Search for assets"""
        query = args["query"]
        asset_type = args.get("asset_type", "video")
        limit = args.get("limit", 10)
        
        try:
            if asset_type == "video":
                assets = await self.scraper.search_videos(query, limit=limit)
            elif asset_type == "audio":
                assets = await self.scraper.search_audio(query, limit=limit)
            else:
                return {"error": f"Unsupported asset type: {asset_type}"}
            
            return {
                "success": True,
                "query": query,
                "asset_type": asset_type,
                "count": len(assets),
                "assets": assets[:limit]
            }
            
        except Exception as e:
            logger.error(f"Error searching assets: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _tool_optimize_pipeline(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze pipeline and suggest optimizations"""
        analysis_type = args.get("analysis_type", "performance")
        
        # Get pipeline statistics
        stats = await self._tool_get_pipeline_stats({"days": 30})
        
        recommendations = []
        
        if analysis_type == "performance":
            avg_time = stats.get("avg_generation_time", 0)
            if avg_time > 300:  # 5 minutes
                recommendations.append(
                    "Consider parallelizing asset downloads to reduce generation time"
                )
            
            success_rate = stats.get("success_rate", 0)
            if success_rate < 0.9:
                recommendations.append(
                    "Improve error handling and retry logic to increase success rate"
                )
        
        elif analysis_type == "quality":
            recommendations.extend([
                "Implement quality checks for generated assets",
                "Add user feedback collection for continuous improvement",
                "Consider A/B testing different script styles"
            ])
        
        elif analysis_type == "cost":
            recommendations.extend([
                "Cache frequently used assets to reduce API calls",
                "Optimize video encoding settings for smaller file sizes",
                "Consider batching TTS requests for cost efficiency"
            ])
        
        return {
            "analysis_type": analysis_type,
            "current_stats": stats,
            "recommendations": recommendations
        }
    
    async def _tool_get_pipeline_stats(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get pipeline statistics"""
        days = args.get("days", 30)
        
        from datetime import datetime, timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Query statistics
        total_jobs = self.db.query(VideoJob).filter(
            VideoJob.created_at >= cutoff_date
        ).count()
        
        completed_jobs = self.db.query(VideoJob).filter(
            VideoJob.created_at >= cutoff_date,
            VideoJob.status == "completed"
        ).count()
        
        failed_jobs = self.db.query(VideoJob).filter(
            VideoJob.created_at >= cutoff_date,
            VideoJob.status == "failed"
        ).count()
        
        return {
            "timeframe_days": days,
            "total_jobs": total_jobs,
            "completed_jobs": completed_jobs,
            "failed_jobs": failed_jobs,
            "success_rate": completed_jobs / total_jobs if total_jobs > 0 else 0,
            "avg_generation_time": 180,  # Would calculate from actual data
            "total_videos_generated": completed_jobs
        }
    
    # ===================================================================
    # Helper Methods
    # ===================================================================
    
    async def _get_job_details(self, job_id: int) -> Dict[str, Any]:
        """Get detailed job information"""
        job = self.db.query(VideoJob).filter(VideoJob.id == job_id).first()
        
        if not job:
            return {"error": "Job not found"}
        
        video = self.db.query(Video).filter(Video.id == job.video_id).first()
        
        return {
            "job": {
                "id": job.id,
                "status": job.status,
                "progress": job.progress,
                "created_at": job.created_at.isoformat(),
            },
            "video": {
                "id": video.id,
                "title": video.title,
                "niche": video.niche,
                "status": video.status
            } if video else None
        }
    
    async def _get_video_details(self, video_id: int) -> Dict[str, Any]:
        """Get detailed video information"""
        video = self.db.query(Video).filter(Video.id == video_id).first()
        
        if not video:
            return {"error": "Video not found"}
        
        # Get associated assets
        assets = self.db.query(VideoAsset).filter(
            VideoAsset.video_id == video_id
        ).all()
        
        return {
            "video": {
                "id": video.id,
                "title": video.title,
                "script": video.script,
                "niche": video.niche,
                "status": video.status,
                "file_path": video.file_path,
                "duration": video.duration,
                "created_at": video.created_at.isoformat()
            },
            "assets": [
                {
                    "type": asset.asset_type,
                    "url": asset.asset_url,
                    "source": asset.source
                }
                for asset in assets
            ]
        }
    
    async def run(self):
        """Run the MCP server"""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="video-pipeline",
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
    server = VideoPipelineMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
