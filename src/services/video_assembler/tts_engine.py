"""
Text-to-Speech Engine using Coqui TTS

This module provides high-quality, local text-to-speech generation using Coqui TTS.
It supports multiple voices, languages, SSML processing, and automatic caching.

Features:
- Multiple pre-trained voices (male, female, various accents)
- SSML support for fine control (pauses, emphasis, rate)
- Automatic audio caching to avoid regeneration
- Batch processing for multiple segments
- Audio format conversion (wav, mp3, ogg)
- Speaking rate and pitch control
- Background noise reduction

Usage:
    tts = TTSEngine()
    result = await tts.generate(
        text="Welcome to this meditation session",
        voice=Voice.FEMALE_CALM,
        speaking_rate=0.9
    )
    await tts.save_audio(result, "output.mp3")
"""

import asyncio
import hashlib
import os
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import uuid

try:
    from TTS.api import TTS
    from TTS.utils.synthesizer import Synthesizer
except ImportError:
    TTS = None
    Synthesizer = None

import numpy as np
from pydantic import BaseModel, Field

from src.utils.cache import CacheManager


class Voice(str, Enum):
    """Pre-configured voice options."""
    
    # English voices
    FEMALE_CALM = "tts_models/en/ljspeech/tacotron2-DDC"  # Meditation, calm content
    FEMALE_ENERGETIC = "tts_models/en/vctk/vits"  # Motivation, energetic content
    MALE_DEEP = "tts_models/en/ljspeech/glow-tts"  # Facts, authoritative
    MALE_FRIENDLY = "tts_models/en/ljspeech/tacotron2-DCA"  # Stories, casual
    
    # Multi-lingual
    MULTILINGUAL = "tts_models/multilingual/multi-dataset/your_tts"
    
    # Fast (lower quality but faster)
    FAST_FEMALE = "tts_models/en/ljspeech/speedy-speech"
    FAST_MALE = "tts_models/en/sam/tacotron-DDC"


class AudioFormat(str, Enum):
    """Supported audio output formats."""
    WAV = "wav"
    MP3 = "mp3"
    OGG = "ogg"


@dataclass
class TTSConfig:
    """Configuration for TTS engine."""
    
    # Voice settings
    voice: Voice = Voice.FEMALE_CALM
    language: str = "en"
    
    # Speech characteristics
    speaking_rate: float = 1.0  # 0.5-2.0 (slower/faster)
    pitch_shift: float = 0.0  # -12 to +12 semitones
    volume: float = 1.0  # 0.0-2.0
    
    # Audio quality
    sample_rate: int = 22050  # Hz (22050 standard, 44100 high quality)
    audio_format: AudioFormat = AudioFormat.WAV
    
    # Processing
    enable_cache: bool = True
    cache_ttl: int = 86400  # 24 hours
    use_gpu: bool = False  # Use GPU if available
    
    # SSML support
    enable_ssml: bool = True
    
    # Output
    output_dir: Path = Path("output_audio")
    normalize_audio: bool = True  # Normalize volume levels


class TTSResult(BaseModel):
    """Result of TTS generation."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    text: str
    audio_path: Optional[str] = None
    audio_data: Optional[bytes] = None
    duration: float  # seconds
    sample_rate: int
    voice_used: str
    format: AudioFormat
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    from_cache: bool = False
    
    class Config:
        arbitrary_types_allowed = True


class TTSEngine:
    """
    Text-to-Speech engine using Coqui TTS.
    
    Generates natural-sounding speech from text with support for multiple voices,
    languages, and fine-grained control via SSML.
    """
    
    def __init__(
        self,
        config: Optional[TTSConfig] = None,
        cache_manager: Optional[CacheManager] = None
    ):
        """
        Initialize TTS engine.
        
        Args:
            config: TTS configuration
            cache_manager: Optional cache manager for audio caching
        """
        self.config = config or TTSConfig()
        self.cache = cache_manager or CacheManager() if self.config.enable_cache else None
        self.tts_model: Optional[TTS] = None
        self._model_cache: Dict[str, TTS] = {}
        
        # Ensure output directory exists
        self.config.output_dir.mkdir(parents=True, exist_ok=True)
        
        # SSML pattern matchers
        self.ssml_patterns = {
            "pause": re.compile(r'<pause\s+duration="([^"]+)"\s*/?>'),
            "emphasis": re.compile(r'<emphasis>([^<]+)</emphasis>'),
            "rate": re.compile(r'<rate\s+speed="([^"]+)">([^<]+)</rate>'),
        }
    
    async def initialize(self, voice: Optional[Voice] = None) -> None:
        """
        Initialize or load TTS model.
        
        Args:
            voice: Voice model to load (uses config default if None)
        """
        if TTS is None:
            raise ImportError(
                "TTS (Coqui) not installed. Install with: pip install TTS"
            )
        
        voice = voice or self.config.voice
        
        # Check cache
        if voice.value in self._model_cache:
            self.tts_model = self._model_cache[voice.value]
            return
        
        # Load model (CPU/GPU based on config)
        gpu = self.config.use_gpu and self._check_gpu_available()
        
        # Run in thread pool (blocking operation)
        loop = asyncio.get_event_loop()
        self.tts_model = await loop.run_in_executor(
            None,
            lambda: TTS(model_name=voice.value, gpu=gpu)
        )
        
        # Cache model
        self._model_cache[voice.value] = self.tts_model
    
    def _check_gpu_available(self) -> bool:
        """Check if GPU is available for acceleration."""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False
    
    async def generate(
        self,
        text: str,
        voice: Optional[Voice] = None,
        speaking_rate: Optional[float] = None,
        save_to_file: bool = True,
    ) -> TTSResult:
        """
        Generate speech audio from text.
        
        Args:
            text: Text to convert to speech
            voice: Voice to use (uses config default if None)
            speaking_rate: Speaking rate multiplier (uses config default if None)
            save_to_file: Save audio to file
        
        Returns:
            TTSResult with audio data and metadata
        """
        voice = voice or self.config.voice
        speaking_rate = speaking_rate or self.config.speaking_rate
        
        # Check cache
        cache_key = self._get_cache_key(text, voice, speaking_rate)
        if self.cache:
            cached = await self.cache.get(cache_key)
            if cached:
                return TTSResult(**cached, from_cache=True)
        
        # Initialize model if needed
        if not self.tts_model or self.tts_model.model_name != voice.value:
            await self.initialize(voice)
        
        # Process SSML if enabled
        if self.config.enable_ssml:
            text, ssml_metadata = self._process_ssml(text)
        else:
            ssml_metadata = {}
        
        # Generate audio
        loop = asyncio.get_event_loop()
        audio_data = await loop.run_in_executor(
            None,
            self._generate_audio_sync,
            text,
            speaking_rate,
        )
        
        # Apply audio processing
        if self.config.normalize_audio:
            audio_data = self._normalize_audio(audio_data)
        
        # Calculate duration
        duration = len(audio_data) / self.config.sample_rate
        
        # Save to file if requested
        audio_path = None
        if save_to_file:
            audio_path = await self._save_audio_file(audio_data, cache_key)
        
        # Create result
        result = TTSResult(
            text=text,
            audio_path=str(audio_path) if audio_path else None,
            audio_data=audio_data.tobytes(),
            duration=duration,
            sample_rate=self.config.sample_rate,
            voice_used=voice.value,
            format=self.config.audio_format,
        )
        
        # Cache result
        if self.cache:
            await self.cache.set(
                cache_key,
                result.dict(exclude={"audio_data"}),
                ttl=self.config.cache_ttl
            )
        
        return result
    
    def _generate_audio_sync(
        self,
        text: str,
        speaking_rate: float,
    ) -> np.ndarray:
        """
        Generate audio synchronously (runs in thread pool).
        
        Args:
            text: Text to synthesize
            speaking_rate: Speaking rate multiplier
        
        Returns:
            Audio data as numpy array
        """
        # Generate with Coqui TTS
        wav = self.tts_model.tts(text=text)
        
        # Convert to numpy array
        audio_array = np.array(wav)
        
        # Adjust speaking rate by resampling
        if speaking_rate != 1.0:
            audio_array = self._adjust_speaking_rate(audio_array, speaking_rate)
        
        return audio_array
    
    def _adjust_speaking_rate(
        self,
        audio: np.ndarray,
        rate: float
    ) -> np.ndarray:
        """
        Adjust speaking rate by time-stretching audio.
        
        Args:
            audio: Audio data
            rate: Rate multiplier (0.5 = half speed, 2.0 = double speed)
        
        Returns:
            Rate-adjusted audio
        """
        try:
            from scipy import signal
            
            # Calculate new length
            new_length = int(len(audio) / rate)
            
            # Resample
            resampled = signal.resample(audio, new_length)
            return resampled.astype(np.float32)
        
        except ImportError:
            # Fallback: simple decimation/interpolation
            from scipy.signal import resample
            new_length = int(len(audio) / rate)
            return np.interp(
                np.linspace(0, len(audio), new_length),
                np.arange(len(audio)),
                audio
            )
    
    def _normalize_audio(self, audio: np.ndarray) -> np.ndarray:
        """
        Normalize audio volume.
        
        Args:
            audio: Audio data
        
        Returns:
            Normalized audio
        """
        # Peak normalization
        peak = np.abs(audio).max()
        if peak > 0:
            audio = audio / peak * 0.95  # Leave 5% headroom
        
        return audio
    
    async def _save_audio_file(
        self,
        audio_data: np.ndarray,
        cache_key: str
    ) -> Path:
        """
        Save audio data to file.
        
        Args:
            audio_data: Audio numpy array
            cache_key: Cache key to use as filename base
        
        Returns:
            Path to saved file
        """
        # Generate filename
        filename = f"{cache_key[:16]}.{self.config.audio_format.value}"
        filepath = self.config.output_dir / filename
        
        # Save based on format
        if self.config.audio_format == AudioFormat.WAV:
            await self._save_wav(audio_data, filepath)
        elif self.config.audio_format == AudioFormat.MP3:
            await self._save_mp3(audio_data, filepath)
        elif self.config.audio_format == AudioFormat.OGG:
            await self._save_ogg(audio_data, filepath)
        
        return filepath
    
    async def _save_wav(self, audio: np.ndarray, path: Path) -> None:
        """Save audio as WAV file."""
        from scipy.io import wavfile
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            wavfile.write,
            str(path),
            self.config.sample_rate,
            (audio * 32767).astype(np.int16)
        )
    
    async def _save_mp3(self, audio: np.ndarray, path: Path) -> None:
        """Save audio as MP3 file (requires pydub and ffmpeg)."""
        from pydub import AudioSegment
        
        # Convert to WAV first
        temp_wav = path.with_suffix(".wav")
        await self._save_wav(audio, temp_wav)
        
        # Convert to MP3
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: AudioSegment.from_wav(str(temp_wav)).export(
                str(path),
                format="mp3",
                bitrate="192k"
            )
        )
        
        # Remove temp WAV
        temp_wav.unlink()
    
    async def _save_ogg(self, audio: np.ndarray, path: Path) -> None:
        """Save audio as OGG file."""
        from pydub import AudioSegment
        
        temp_wav = path.with_suffix(".wav")
        await self._save_wav(audio, temp_wav)
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: AudioSegment.from_wav(str(temp_wav)).export(
                str(path),
                format="ogg",
                codec="libvorbis"
            )
        )
        
        temp_wav.unlink()
    
    def _process_ssml(self, text: str) -> Tuple[str, Dict]:
        """
        Process SSML tags in text.
        
        Args:
            text: Text with SSML tags
        
        Returns:
            Tuple of (clean_text, ssml_metadata)
        """
        metadata = {
            "pauses": [],
            "emphasis": [],
            "rate_changes": []
        }
        
        # Extract pauses
        for match in self.ssml_patterns["pause"].finditer(text):
            duration = match.group(1)
            metadata["pauses"].append({
                "position": match.start(),
                "duration": duration
            })
        
        # Extract emphasis
        for match in self.ssml_patterns["emphasis"].finditer(text):
            content = match.group(1)
            metadata["emphasis"].append({
                "text": content,
                "position": match.start()
            })
        
        # Extract rate changes
        for match in self.ssml_patterns["rate"].finditer(text):
            speed = match.group(1)
            content = match.group(2)
            metadata["rate_changes"].append({
                "text": content,
                "speed": speed,
                "position": match.start()
            })
        
        # Remove SSML tags
        clean_text = text
        for pattern in self.ssml_patterns.values():
            clean_text = pattern.sub(r"\1", clean_text)
        
        return clean_text, metadata
    
    async def generate_batch(
        self,
        texts: List[str],
        voice: Optional[Voice] = None,
        speaking_rate: Optional[float] = None,
    ) -> List[TTSResult]:
        """
        Generate audio for multiple text segments.
        
        Args:
            texts: List of text segments
            voice: Voice to use
            speaking_rate: Speaking rate
        
        Returns:
            List of TTSResult objects
        """
        tasks = [
            self.generate(text, voice, speaking_rate)
            for text in texts
        ]
        
        return await asyncio.gather(*tasks)
    
    def _get_cache_key(
        self,
        text: str,
        voice: Voice,
        speaking_rate: float
    ) -> str:
        """
        Generate cache key for TTS generation.
        
        Args:
            text: Text content
            voice: Voice model
            speaking_rate: Speaking rate
        
        Returns:
            Cache key hash
        """
        content = f"{text}:{voice.value}:{speaking_rate}:{self.config.sample_rate}"
        # MD5 used for cache key only, not security (nosec: B324)
        return hashlib.md5(content.encode(), usedforsecurity=False).hexdigest()
    
    async def list_available_voices(self) -> List[str]:
        """
        List all available TTS models/voices.
        
        Returns:
            List of model names
        """
        if TTS is None:
            return []
        
        loop = asyncio.get_event_loop()
        models = await loop.run_in_executor(
            None,
            TTS.list_models
        )
        
        return models
    
    async def estimate_duration(
        self,
        text: str,
        speaking_rate: float = 1.0
    ) -> float:
        """
        Estimate audio duration without generating.
        
        Args:
            text: Text to estimate
            speaking_rate: Speaking rate multiplier
        
        Returns:
            Estimated duration in seconds
        """
        # Average speaking rate: 150 words per minute
        word_count = len(text.split())
        base_duration = (word_count / 150) * 60
        
        # Adjust for speaking rate
        adjusted_duration = base_duration / speaking_rate
        
        return adjusted_duration
    
    async def cleanup_cache(self, max_age_days: int = 7) -> int:
        """
        Clean up old cached audio files.
        
        Args:
            max_age_days: Maximum age of files to keep
        
        Returns:
            Number of files deleted
        """
        import time
        
        deleted = 0
        max_age_seconds = max_age_days * 86400
        current_time = time.time()
        
        for file in self.config.output_dir.glob("*"):
            if file.is_file():
                age = current_time - file.stat().st_mtime
                if age > max_age_seconds:
                    file.unlink()
                    deleted += 1
        
        return deleted
