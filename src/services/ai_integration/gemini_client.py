"""
Gemini Pro API Integration

Provides access to Google's Gemini Pro API for:
- Multimodal AI (text, images, video analysis)
- Thumbnail generation and optimization
- Asset categorization using vision
- Video content analysis
- SEO optimization suggestions
"""

import os
import asyncio
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path
import base64
import logging

try:
    import google.generativeai as genai
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("Warning: google-generativeai package not installed. Run: pip install google-generativeai")

logger = logging.getLogger(__name__)


@dataclass
class GeminiResponse:
    """Represents a Gemini API response"""
    content: str
    model: str
    finish_reason: str
    safety_ratings: Dict[str, str]
    latency_seconds: float


@dataclass
class ImageAnalysis:
    """Result of image/video analysis"""
    description: str
    objects: List[str]
    colors: List[str]
    mood: str
    suitability_score: float  # 0.0 to 1.0
    recommendations: List[str]


class GeminiClient:
    """
    Client for interacting with Gemini Pro API
    
    Features:
    - Text generation
    - Image analysis and understanding
    - Video content analysis
    - Multimodal reasoning
    - Thumbnail generation prompts
    - Asset categorization
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-1.5-pro-latest",
        temperature: float = 0.9,
        top_p: float = 1.0,
        top_k: int = 1,
        max_output_tokens: int = 2048
    ):
        """
        Initialize Gemini client
        
        Args:
            api_key: Google AI API key (or use GOOGLE_API_KEY env var)
            model: Gemini model to use
            temperature: Sampling temperature (0.0 to 2.0)
            top_p: Top-p sampling
            top_k: Top-k sampling
            max_output_tokens: Maximum tokens in response
        """
        if not GEMINI_AVAILABLE:
            raise ImportError(
                "google-generativeai package required. "
                "Install with: pip install google-generativeai"
            )
        
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Google API key required. Set GOOGLE_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        
        self.model_name = model
        self.temperature = temperature
        self.top_p = top_p
        self.top_k = top_k
        self.max_output_tokens = max_output_tokens
        
        # Initialize model
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config={
                "temperature": self.temperature,
                "top_p": self.top_p,
                "top_k": self.top_k,
                "max_output_tokens": self.max_output_tokens,
            },
            safety_settings={
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            }
        )
        
        logger.info(f"Initialized GeminiClient with model {self.model_name}")
    
    def generate_content(
        self,
        prompt: str,
        image_path: Optional[str] = None
    ) -> GeminiResponse:
        """
        Generate content using Gemini (synchronous)
        
        Args:
            prompt: Text prompt
            image_path: Optional path to image for multimodal input
        
        Returns:
            GeminiResponse with generated content
        """
        start_time = datetime.utcnow()
        
        try:
            # Prepare input
            if image_path:
                # Multimodal: text + image
                from PIL import Image
                img = Image.open(image_path)
                response = self.model.generate_content([prompt, img])
            else:
                # Text only
                response = self.model.generate_content(prompt)
            
            # Extract response
            content = response.text
            
            # Calculate latency
            latency = (datetime.utcnow() - start_time).total_seconds()
            
            # Extract safety ratings
            safety_ratings = {}
            if hasattr(response, 'prompt_feedback'):
                for rating in response.prompt_feedback.safety_ratings:
                    safety_ratings[rating.category.name] = rating.probability.name
            
            return GeminiResponse(
                content=content,
                model=self.model_name,
                finish_reason=response.candidates[0].finish_reason.name if response.candidates else "UNKNOWN",
                safety_ratings=safety_ratings,
                latency_seconds=latency
            )
            
        except Exception as e:
            logger.error(f"Gemini API error: {e}", exc_info=True)
            raise
    
    async def generate_content_async(
        self,
        prompt: str,
        image_path: Optional[str] = None
    ) -> GeminiResponse:
        """
        Generate content using Gemini (asynchronous)
        
        Args:
            prompt: Text prompt
            image_path: Optional path to image
        
        Returns:
            GeminiResponse with generated content
        """
        start_time = datetime.utcnow()
        
        try:
            # Prepare input
            if image_path:
                # Multimodal: text + image
                from PIL import Image
                img = Image.open(image_path)
                response = await self.model.generate_content_async([prompt, img])
            else:
                # Text only
                response = await self.model.generate_content_async(prompt)
            
            # Extract response
            content = response.text
            
            # Calculate latency
            latency = (datetime.utcnow() - start_time).total_seconds()
            
            # Extract safety ratings
            safety_ratings = {}
            if hasattr(response, 'prompt_feedback'):
                for rating in response.prompt_feedback.safety_ratings:
                    safety_ratings[rating.category.name] = rating.probability.name
            
            return GeminiResponse(
                content=content,
                model=self.model_name,
                finish_reason=response.candidates[0].finish_reason.name if response.candidates else "UNKNOWN",
                safety_ratings=safety_ratings,
                latency_seconds=latency
            )
            
        except Exception as e:
            logger.error(f"Gemini async API error: {e}", exc_info=True)
            raise
    
    # ===================================================================
    # Specialized Use Cases
    # ===================================================================
    
    async def analyze_image(
        self,
        image_path: str,
        analysis_type: str = "general"
    ) -> ImageAnalysis:
        """
        Analyze an image using Gemini Vision
        
        Args:
            image_path: Path to image file
            analysis_type: Type of analysis ('general', 'mood', 'objects', 'suitability')
        
        Returns:
            ImageAnalysis with detailed results
        """
        if analysis_type == "general":
            prompt = """Analyze this image and provide:
            1. A detailed description
            2. List of main objects/subjects
            3. Dominant colors
            4. Overall mood/emotion
            5. Suitability score (0-10) for meditation/relaxation videos
            6. Recommendations for improvement
            
            Format as JSON."""
        
        elif analysis_type == "mood":
            prompt = """What is the emotional mood of this image? 
            Describe the feeling it evokes and rate it 0-10 for calmness/relaxation."""
        
        elif analysis_type == "objects":
            prompt = """List all distinct objects, subjects, and elements visible in this image. 
            Be comprehensive and specific."""
        
        elif analysis_type == "suitability":
            prompt = """Rate this image's suitability for a meditation/relaxation video on a scale of 0-10. 
            Explain your rating and suggest improvements."""
        
        else:
            prompt = f"Analyze this image: {analysis_type}"
        
        response = await self.generate_content_async(prompt, image_path=image_path)
        
        # Parse response (simplified - would use JSON parsing in production)
        return ImageAnalysis(
            description=response.content,
            objects=[],  # Would parse from JSON
            colors=[],  # Would parse from JSON
            mood="calm",  # Would parse from response
            suitability_score=0.8,  # Would parse from response
            recommendations=[]  # Would parse from JSON
        )
    
    async def generate_thumbnail_prompt(
        self,
        video_title: str,
        video_description: str,
        niche: str
    ) -> str:
        """
        Generate a detailed prompt for thumbnail creation
        
        Args:
            video_title: Video title
            video_description: Video description
            niche: Video niche (meditation, tutorial, etc.)
        
        Returns:
            Detailed thumbnail generation prompt for AI image generators
        """
        prompt = f"""Create a detailed prompt for generating a YouTube thumbnail image for:

Title: {video_title}
Description: {video_description}
Niche: {niche}

The prompt should include:
- Visual elements that attract clicks
- Color scheme optimized for {niche}
- Text overlay suggestions
- Composition guidelines
- Emotional appeal factors
- Niche-specific elements

Generate a comprehensive prompt suitable for DALL-E, Midjourney, or Stable Diffusion."""
        
        response = await self.generate_content_async(prompt)
        return response.content
    
    async def categorize_asset(
        self,
        asset_path: str,
        asset_type: str = "video"
    ) -> Dict[str, Any]:
        """
        Categorize an asset (video, image, audio) for better organization
        
        Args:
            asset_path: Path to asset file
            asset_type: Type of asset ('video', 'image', 'audio')
        
        Returns:
            Categorization data with tags, themes, suggested uses
        """
        if asset_type == "image":
            prompt = """Analyze this image and categorize it:
            
            Provide:
            1. Primary category (nature, abstract, people, etc.)
            2. Sub-categories (tags)
            3. Suitable video niches (meditation, tutorial, vlog, etc.)
            4. Mood/theme
            5. Time of day (if applicable)
            6. Season (if applicable)
            7. Color palette
            
            Format as JSON."""
            
            response = await self.generate_content_async(prompt, image_path=asset_path)
        
        else:
            # For video, audio would need different approach
            prompt = f"Categorize this {asset_type} asset for a content library."
            response = await self.generate_content_async(prompt)
        
        # Parse response into structured data
        return {
            "primary_category": "nature",  # Would parse from response
            "tags": ["calm", "water", "forest"],  # Would parse from response
            "suitable_niches": ["meditation", "relaxation"],
            "mood": "peaceful",
            "confidence": 0.85
        }
    
    async def optimize_seo(
        self,
        title: str,
        description: str,
        niche: str
    ) -> Dict[str, Any]:
        """
        Generate SEO-optimized metadata for YouTube videos
        
        Args:
            title: Current video title
            description: Current description
            niche: Video niche
        
        Returns:
            Optimized title, description, tags, and recommendations
        """
        prompt = f"""You are a YouTube SEO expert. Optimize this video metadata:

Current Title: {title}
Current Description: {description}
Niche: {niche}

Provide:
1. Optimized title (under 60 characters, includes keywords)
2. Optimized description (first 150 characters are critical)
3. 15-20 relevant tags
4. Suggested hashtags
5. Category recommendation
6. Thumbnail text suggestions
7. Best posting time
8. Trending keywords in this niche

Format as JSON."""
        
        response = await self.generate_content_async(prompt)
        
        # Would parse JSON response
        return {
            "optimized_title": title,  # Placeholder
            "optimized_description": description,  # Placeholder
            "tags": [],
            "hashtags": [],
            "recommendations": response.content
        }
    
    async def analyze_video_frame(
        self,
        frame_path: str,
        timestamp: float
    ) -> str:
        """
        Analyze a video frame at specific timestamp
        
        Args:
            frame_path: Path to extracted frame
            timestamp: Timestamp in video
        
        Returns:
            Frame analysis description
        """
        prompt = f"""Analyze this video frame from timestamp {timestamp}s:
        
        Describe:
        - What's happening in the scene
        - Visual elements and composition
        - Suitability for video thumbnail
        - Recommended caption text
        """
        
        response = await self.generate_content_async(prompt, image_path=frame_path)
        return response.content
    
    async def suggest_video_improvements(
        self,
        video_metadata: Dict[str, Any],
        performance_data: Dict[str, Any]
    ) -> str:
        """
        Suggest improvements based on video performance
        
        Args:
            video_metadata: Video title, description, tags, etc.
            performance_data: Views, CTR, watch time, etc.
        
        Returns:
            Detailed improvement suggestions
        """
        prompt = f"""You are a YouTube growth strategist. Analyze this video performance:

Metadata: {video_metadata}
Performance: {performance_data}

Provide actionable suggestions for:
1. Improving click-through rate (CTR)
2. Increasing watch time
3. Better engagement
4. SEO optimization
5. Thumbnail improvements
6. Title optimization
7. Description improvements

Be specific and data-driven."""
        
        response = await self.generate_content_async(prompt)
        return response.content


# Example usage
if __name__ == "__main__":
    async def main():
        # Initialize Gemini client
        client = GeminiClient()
        
        # Example 1: Text generation
        print("Example 1: Text Generation")
        print("=" * 50)
        
        response = await client.generate_content_async(
            "Write a 30-second meditation script about ocean waves."
        )
        print(response.content)
        print(f"Latency: {response.latency_seconds:.2f}s\n")
        
        # Example 2: SEO optimization
        print("Example 2: SEO Optimization")
        print("=" * 50)
        
        seo_result = await client.optimize_seo(
            title="Meditation Video",
            description="A calming meditation video",
            niche="meditation"
        )
        print(seo_result["recommendations"])
        print("\n")
        
        # Example 3: Thumbnail prompt generation
        print("Example 3: Thumbnail Prompt")
        print("=" * 50)
        
        thumbnail_prompt = await client.generate_thumbnail_prompt(
            video_title="10 Minute Morning Meditation",
            video_description="Start your day with peaceful meditation",
            niche="meditation"
        )
        print(thumbnail_prompt)
    
    asyncio.run(main())
