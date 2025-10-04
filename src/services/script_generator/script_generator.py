"""
Faceless YouTube - Script Generator

Main service for generating video scripts using AI.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import uuid4

from pydantic import BaseModel, Field

from .ollama_client import OllamaClient, OllamaConfig
from .prompt_templates import PromptTemplateManager, NicheType, PromptTemplate
from .content_validator import ContentValidator, ValidationResult
from src.utils.cache import CacheManager, cached


@dataclass
class ScriptConfig:
    """Configuration for script generation"""
    
    # Content settings
    duration_minutes: int = 5
    niche: NicheType = NicheType.MEDITATION
    tone: str = "calm and soothing"
    target_audience: str = "general audience"
    
    # AI settings
    model: str = "mistral"
    temperature: float = 0.7
    max_retries: int = 3
    
    # Validation settings
    validate: bool = True
    min_quality_score: float = 0.7
    
    # Caching
    cache_enabled: bool = True
    cache_ttl: int = 3600  # 1 hour


class GeneratedScript(BaseModel):
    """A generated video script"""
    
    # Identifiers
    id: str = Field(default_factory=lambda: str(uuid4()))
    niche: str
    
    # Content
    title: str
    script: str
    hook: Optional[str] = None  # Opening hook/intro
    call_to_action: Optional[str] = None  # Closing CTA
    
    # Metadata
    word_count: int
    estimated_duration: float  # seconds
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # AI info
    model_used: str
    temperature: float
    prompt_tokens: Optional[int] = None
    
    # Validation
    validation: Optional[Dict[str, Any]] = None
    quality_score: Optional[float] = None
    
    # Tags and categorization
    tags: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class ScriptGenerator:
    """
    Main service for generating video scripts.
    
    Features:
    - Multiple niche support (meditation, motivation, facts, etc.)
    - AI-powered generation using Ollama
    - Automatic validation and quality checks
    - Caching for performance
    - Retry logic for robustness
    - Extractable components (hook, CTA)
    """
    
    def __init__(
        self,
        ollama_client: Optional[OllamaClient] = None,
        cache_manager: Optional[CacheManager] = None,
        validator: Optional[ContentValidator] = None,
    ):
        """
        Initialize script generator.
        
        Args:
            ollama_client: Optional Ollama client (creates default if None)
            cache_manager: Optional cache manager
            validator: Optional content validator
        """
        self.ollama = ollama_client or OllamaClient()
        self.cache = cache_manager or CacheManager()
        self.validator = validator or ContentValidator()
        self.template_manager = PromptTemplateManager()
    
    async def generate(
        self,
        topic: str,
        config: Optional[ScriptConfig] = None,
        **kwargs
    ) -> GeneratedScript:
        """
        Generate a video script on the given topic.
        
        Args:
            topic: Main topic/subject for the script
            config: Optional configuration (uses defaults if None)
            **kwargs: Additional parameters for prompt formatting
        
        Returns:
            GeneratedScript with content and metadata
        
        Raises:
            ValueError: If generation fails after all retries
        """
        config = config or ScriptConfig()
        
        # Try to get from cache
        if config.cache_enabled:
            cached_script = await self._get_from_cache(topic, config)
            if cached_script:
                return cached_script
        
        # Generate script with retry logic
        for attempt in range(config.max_retries):
            try:
                script_text = await self._generate_script(topic, config, **kwargs)
                
                # Validate if enabled
                validation_result = None
                if config.validate:
                    validation_result = self.validator.validate(
                        script_text,
                        niche=config.niche.value
                    )
                    
                    # Check quality threshold
                    if validation_result.score < config.min_quality_score:
                        if attempt < config.max_retries - 1:
                            # Try again with adjusted temperature
                            config.temperature = min(config.temperature + 0.1, 1.0)
                            continue
                
                # Extract components
                hook = self._extract_hook(script_text)
                cta = self._extract_cta(script_text)
                
                # Generate title
                title = await self._generate_title(topic, config)
                
                # Create GeneratedScript object
                generated_script = GeneratedScript(
                    niche=config.niche.value,
                    title=title,
                    script=script_text,
                    hook=hook,
                    call_to_action=cta,
                    word_count=len(script_text.split()),
                    estimated_duration=self.validator.estimate_duration(script_text),
                    model_used=config.model,
                    temperature=config.temperature,
                    validation=validation_result.dict() if validation_result else None,
                    quality_score=validation_result.score if validation_result else None,
                    tags=self._extract_tags(topic, config.niche),
                    keywords=self._extract_keywords(script_text),
                )
                
                # Cache if enabled
                if config.cache_enabled:
                    await self._save_to_cache(topic, config, generated_script)
                
                return generated_script
            
            except Exception as e:
                if attempt == config.max_retries - 1:
                    raise ValueError(f"Script generation failed after {config.max_retries} attempts: {e}")
                await asyncio.sleep(1 * (attempt + 1))  # Exponential backoff
        
        raise ValueError("Script generation failed")
    
    async def _generate_script(
        self,
        topic: str,
        config: ScriptConfig,
        **kwargs
    ) -> str:
        """
        Generate script text using AI.
        
        Args:
            topic: Script topic
            config: Generation configuration
            **kwargs: Additional prompt parameters
        
        Returns:
            Generated script text
        """
        # Get template for niche
        template = self.template_manager.get_template(config.niche)
        
        # Prepare prompt parameters
        prompt_params = {
            'topic': topic,
            'duration': config.duration_minutes,
            'tone': config.tone,
            'audience': config.target_audience,
            'context': kwargs.get('context', ''),
            **kwargs
        }
        
        # Format prompts
        system_prompt, user_prompt = self.template_manager.format_prompt(
            config.niche,
            **prompt_params
        )
        
        # Generate with Ollama
        script_text = await self.ollama.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            model=config.model,
            temperature=config.temperature,
            max_tokens=template.max_tokens,
        )
        
        return script_text.strip()
    
    async def _generate_title(
        self,
        topic: str,
        config: ScriptConfig
    ) -> str:
        """
        Generate an engaging title for the video.
        
        Args:
            topic: Script topic
            config: Configuration
        
        Returns:
            Video title
        """
        title_prompt = f"""Generate a compelling, SEO-friendly YouTube video title for a {config.niche.value} video about: {topic}

Requirements:
- Length: 50-60 characters
- Include keywords: {topic}
- Make it engaging and click-worthy
- Don't use clickbait or misleading language
- Format: Title Case

Generate ONLY the title, nothing else."""
        
        title = await self.ollama.generate(
            prompt=title_prompt,
            temperature=0.8,
            max_tokens=100,
        )
        
        # Clean up title
        title = title.strip().strip('"').strip("'")
        
        # Ensure reasonable length
        if len(title) > 100:
            title = title[:97] + "..."
        
        return title
    
    def _extract_hook(self, script: str) -> Optional[str]:
        """
        Extract the opening hook from the script.
        
        Args:
            script: Full script text
        
        Returns:
            Hook text (first 1-2 sentences)
        """
        # Get first 2 sentences
        import re
        sentences = re.split(r'[.!?]+', script.strip())
        hook_sentences = [s.strip() for s in sentences[:2] if s.strip()]
        
        if hook_sentences:
            return '. '.join(hook_sentences) + '.'
        
        return None
    
    def _extract_cta(self, script: str) -> Optional[str]:
        """
        Extract call-to-action from the script.
        
        Args:
            script: Full script text
        
        Returns:
            CTA text (last few sentences)
        """
        import re
        sentences = re.split(r'[.!?]+', script.strip())
        
        # Look for CTA keywords in last 3 sentences
        cta_keywords = ['subscribe', 'like', 'comment', 'share', 'follow', 'join']
        last_sentences = [s.strip() for s in sentences[-3:] if s.strip()]
        
        cta_sentences = [
            s for s in last_sentences
            if any(keyword in s.lower() for keyword in cta_keywords)
        ]
        
        if cta_sentences:
            return '. '.join(cta_sentences) + '.'
        
        return None
    
    def _extract_tags(self, topic: str, niche: NicheType) -> List[str]:
        """Extract relevant tags"""
        tags = [niche.value, topic.lower()]
        
        # Add niche-specific tags
        niche_tags = {
            NicheType.MEDITATION: ['relaxation', 'mindfulness', 'calm'],
            NicheType.MOTIVATION: ['inspiration', 'success', 'goals'],
            NicheType.FACTS: ['educational', 'learning', 'knowledge'],
            NicheType.STORIES: ['storytelling', 'narrative', 'tale'],
            NicheType.EDUCATION: ['learning', 'tutorial', 'educational'],
        }
        
        tags.extend(niche_tags.get(niche, []))
        return list(set(tags))[:10]  # Max 10 unique tags
    
    def _extract_keywords(self, script: str) -> List[str]:
        """Extract keywords from script"""
        import re
        from collections import Counter
        
        # Get words (exclude common words)
        words = re.findall(r'\b[a-z]{4,}\b', script.lower())
        
        # Common words to exclude
        stop_words = {
            'this', 'that', 'with', 'from', 'have', 'will', 'your',
            'more', 'about', 'into', 'through', 'when', 'there', 'them'
        }
        
        # Count word frequency
        word_freq = Counter(w for w in words if w not in stop_words)
        
        # Return top 10 keywords
        return [word for word, _ in word_freq.most_common(10)]
    
    async def _get_from_cache(
        self,
        topic: str,
        config: ScriptConfig
    ) -> Optional[GeneratedScript]:
        """Try to get script from cache"""
        cache_key = f"script:{config.niche.value}:{topic}:{config.duration_minutes}"
        
        cached_data = await self.cache.get(cache_key)
        if cached_data:
            return GeneratedScript(**cached_data)
        
        return None
    
    async def _save_to_cache(
        self,
        topic: str,
        config: ScriptConfig,
        script: GeneratedScript
    ) -> None:
        """Save generated script to cache"""
        cache_key = f"script:{config.niche.value}:{topic}:{config.duration_minutes}"
        
        await self.cache.set(
            cache_key,
            script.dict(),
            ttl=config.cache_ttl
        )
    
    async def generate_batch(
        self,
        topics: List[str],
        config: Optional[ScriptConfig] = None,
        **kwargs
    ) -> List[GeneratedScript]:
        """
        Generate multiple scripts in parallel.
        
        Args:
            topics: List of topics
            config: Optional configuration
            **kwargs: Additional parameters
        
        Returns:
            List of generated scripts
        """
        tasks = [
            self.generate(topic, config, **kwargs)
            for topic in topics
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        scripts = [
            result for result in results
            if isinstance(result, GeneratedScript)
        ]
        
        return scripts
    
    async def regenerate_with_feedback(
        self,
        original_script: GeneratedScript,
        feedback: str,
        config: Optional[ScriptConfig] = None
    ) -> GeneratedScript:
        """
        Regenerate script with user feedback.
        
        Args:
            original_script: Original generated script
            feedback: User feedback/improvements
            config: Optional configuration
        
        Returns:
            Improved script
        """
        config = config or ScriptConfig(niche=NicheType(original_script.niche))
        
        # Create improvement prompt
        improve_prompt = f"""Here is a {original_script.niche} script:

{original_script.script}

User feedback: {feedback}

Please regenerate the script incorporating this feedback while maintaining the same topic and style.
Make specific improvements based on the feedback."""
        
        improved_text = await self.ollama.generate(
            prompt=improve_prompt,
            temperature=config.temperature,
            max_tokens=3072,
        )
        
        # Create new script object
        validation_result = self.validator.validate(improved_text)
        
        return GeneratedScript(
            niche=original_script.niche,
            title=original_script.title + " (Improved)",
            script=improved_text,
            word_count=len(improved_text.split()),
            estimated_duration=self.validator.estimate_duration(improved_text),
            model_used=config.model,
            temperature=config.temperature,
            validation=validation_result.dict(),
            quality_score=validation_result.score,
            tags=original_script.tags,
            keywords=self._extract_keywords(improved_text),
        )
    
    async def close(self) -> None:
        """Close connections"""
        await self.ollama.close()
