"""
Faceless YouTube - Script Generator Tests

Test suite for script generation functionality.
"""

import pytest
import asyncio
from datetime import datetime

from src.services.script_generator import (
    OllamaClient,
    OllamaConfig,
    ScriptGenerator,
    ScriptConfig,
    GeneratedScript,
    PromptTemplateManager,
    NicheType,
    ContentValidator,
    ValidationResult,
    ValidationIssue,
)


# ============================================
# OLLAMA CLIENT TESTS
# ============================================

def test_ollama_config_defaults():
    """Test default Ollama configuration"""
    config = OllamaConfig()
    
    assert config.host == "localhost"
    assert config.port == 11434
    assert config.model == "mistral"
    assert config.temperature == 0.7
    assert config.base_url == "http://localhost:11434"


def test_ollama_config_custom():
    """Test custom Ollama configuration"""
    config = OllamaConfig(
        host="ai-server",
        port=8080,
        model="llama2",
        temperature=0.9,
    )
    
    assert config.base_url == "http://ai-server:8080"
    assert config.model == "llama2"
    assert config.temperature == 0.9


@pytest.mark.skip(reason="Requires Ollama server running")
@pytest.mark.asyncio
async def test_ollama_health_check():
    """Test Ollama health check"""
    client = OllamaClient()
    is_healthy = await client.health_check()
    await client.close()
    
    assert isinstance(is_healthy, bool)


@pytest.mark.skip(reason="Requires Ollama server running")
@pytest.mark.asyncio
async def test_ollama_generate():
    """Test text generation"""
    client = OllamaClient()
    
    response = await client.generate(
        prompt="Write a short greeting.",
        max_tokens=50,
    )
    
    assert isinstance(response, str)
    assert len(response) > 0
    
    await client.close()


# ============================================
# PROMPT TEMPLATE TESTS
# ============================================

def test_template_manager_initialization():
    """Test template manager creates all niche templates"""
    manager = PromptTemplateManager()
    
    assert len(manager.templates) == 10  # All default niches
    assert NicheType.MEDITATION in manager.templates
    assert NicheType.MOTIVATION in manager.templates
    assert NicheType.FACTS in manager.templates


def test_get_template():
    """Test retrieving specific template"""
    manager = PromptTemplateManager()
    
    meditation_template = manager.get_template(NicheType.MEDITATION)
    
    assert meditation_template is not None
    assert "meditation" in meditation_template.system_prompt.lower()
    assert "{topic}" in meditation_template.user_prompt_template


def test_format_prompt():
    """Test prompt formatting"""
    manager = PromptTemplateManager()
    
    system_prompt, user_prompt = manager.format_prompt(
        NicheType.MEDITATION,
        topic="ocean waves",
        duration=5,
        style="guided",
        context="for beginners"
    )
    
    assert "meditation" in system_prompt.lower()
    assert "ocean waves" in user_prompt
    assert "5" in user_prompt


# ============================================
# CONTENT VALIDATOR TESTS
# ============================================

def test_validator_initialization():
    """Test validator initialization"""
    validator = ContentValidator(
        min_words=100,
        max_words=1000,
        speaking_pace=150,
    )
    
    assert validator.min_words == 100
    assert validator.max_words == 1000
    assert validator.speaking_pace == 150


def test_validate_good_script():
    """Test validation of a good script"""
    validator = ContentValidator(min_words=10, max_words=100)
    
    script = """
    Welcome to this meditation session. Take a deep breath.
    Feel yourself relaxing as you breathe in and out slowly.
    Let go of any tension in your body. You are safe and peaceful.
    Continue breathing deeply as you find your center.
    """
    
    result = validator.validate(script)
    
    assert result.word_count > 10
    assert result.estimated_duration > 0
    assert result.score > 0.5


def test_validate_too_short():
    """Test validation catches too-short scripts"""
    validator = ContentValidator(min_words=100)
    
    script = "This is too short."
    result = validator.validate(script)
    
    assert ValidationIssue.TOO_SHORT in result.issues
    assert result.is_valid is False


def test_validate_too_long():
    """Test validation catches too-long scripts"""
    validator = ContentValidator(max_words=20)
    
    script = " ".join(["word"] * 50)  # 50 words
    result = validator.validate(script)
    
    assert ValidationIssue.TOO_LONG in result.issues


def test_validate_profanity():
    """Test profanity detection"""
    validator = ContentValidator()
    
    script = "This script contains damn profanity that should be detected."
    result = validator.validate(script)
    
    assert ValidationIssue.PROFANITY in result.issues


def test_validate_medical_disclaimer():
    """Test medical advice detection"""
    validator = ContentValidator()
    
    script = """This will help diagnose your condition. 
    Take this medication to treat the disease."""
    result = validator.validate(script)
    
    assert ValidationIssue.MEDICAL_ADVICE in result.issues
    assert any('disclaimer' in s.lower() for s in result.suggestions)


def test_estimate_duration():
    """Test duration estimation"""
    validator = ContentValidator(speaking_pace=150)  # 150 WPM
    
    script = " ".join(["word"] * 150)  # Exactly 150 words
    duration = validator.estimate_duration(script)
    
    assert 58 <= duration <= 62  # Should be ~60 seconds


# ============================================
# SCRIPT CONFIG TESTS
# ============================================

def test_script_config_defaults():
    """Test default script configuration"""
    config = ScriptConfig()
    
    assert config.duration_minutes == 5
    assert config.niche == NicheType.MEDITATION
    assert config.validate is True
    assert config.cache_enabled is True


def test_script_config_custom():
    """Test custom script configuration"""
    config = ScriptConfig(
        duration_minutes=10,
        niche=NicheType.MOTIVATION,
        temperature=0.8,
        validate=False,
    )
    
    assert config.duration_minutes == 10
    assert config.niche == NicheType.MOTIVATION
    assert config.temperature == 0.8
    assert config.validate is False


# ============================================
# GENERATED SCRIPT TESTS
# ============================================

def test_generated_script_creation():
    """Test creating a GeneratedScript"""
    script = GeneratedScript(
        niche="meditation",
        title="Peaceful Ocean Meditation",
        script="Breathe in... breathe out...",
        word_count=100,
        estimated_duration=40.0,
        model_used="mistral",
        temperature=0.7,
    )
    
    assert script.id is not None
    assert script.niche == "meditation"
    assert script.word_count == 100
    assert isinstance(script.generated_at, datetime)


def test_generated_script_serialization():
    """Test script serialization"""
    script = GeneratedScript(
        niche="meditation",
        title="Test",
        script="Content",
        word_count=10,
        estimated_duration=5.0,
        model_used="mistral",
        temperature=0.7,
    )
    
    # Convert to dict
    data = script.dict()
    assert isinstance(data, dict)
    assert data['niche'] == "meditation"
    
    # Reconstruct
    script2 = GeneratedScript(**data)
    assert script2.title == script.title


# ============================================
# SCRIPT GENERATOR TESTS
# ============================================

@pytest.mark.skip(reason="Requires Ollama server running")
@pytest.mark.asyncio
async def test_script_generator_initialization():
    """Test script generator initialization"""
    generator = ScriptGenerator()
    
    assert generator.ollama is not None
    assert generator.cache is not None
    assert generator.validator is not None
    assert generator.template_manager is not None
    
    await generator.close()


@pytest.mark.skip(reason="Requires Ollama server running")
@pytest.mark.asyncio
async def test_generate_meditation_script():
    """Test generating a meditation script"""
    generator = ScriptGenerator()
    
    config = ScriptConfig(
        duration_minutes=3,
        niche=NicheType.MEDITATION,
        validate=True,
    )
    
    script = await generator.generate(
        topic="ocean waves",
        config=config,
        style="guided",
        context="for stress relief"
    )
    
    assert script is not None
    assert script.niche == "meditation"
    assert "ocean" in script.script.lower() or "wave" in script.script.lower()
    assert script.word_count > 0
    assert script.estimated_duration > 0
    
    await generator.close()


@pytest.mark.skip(reason="Requires Ollama server running")
@pytest.mark.asyncio
async def test_generate_multiple_niches():
    """Test generating scripts for different niches"""
    generator = ScriptGenerator()
    
    niches = [NicheType.MEDITATION, NicheType.MOTIVATION, NicheType.FACTS]
    
    for niche in niches:
        config = ScriptConfig(
            duration_minutes=2,
            niche=niche,
            validate=False,  # Skip validation for speed
        )
        
        script = await generator.generate(
            topic="success",
            config=config,
        )
        
        assert script.niche == niche.value
        assert len(script.script) > 0
    
    await generator.close()


@pytest.mark.skip(reason="Requires Ollama server running")
@pytest.mark.asyncio
async def test_generate_batch():
    """Test batch script generation"""
    generator = ScriptGenerator()
    
    topics = ["peace", "focus", "gratitude"]
    config = ScriptConfig(
        duration_minutes=2,
        niche=NicheType.MEDITATION,
        validate=False,
    )
    
    scripts = await generator.generate_batch(topics, config)
    
    assert len(scripts) == len(topics)
    assert all(isinstance(s, GeneratedScript) for s in scripts)
    
    await generator.close()


# ============================================
# INTEGRATION TESTS
# ============================================

@pytest.mark.skip(reason="Requires Ollama server running")
@pytest.mark.asyncio
async def test_full_generation_pipeline():
    """Test complete script generation with validation"""
    generator = ScriptGenerator()
    
    config = ScriptConfig(
        duration_minutes=3,
        niche=NicheType.MEDITATION,
        tone="calm and peaceful",
        validate=True,
        min_quality_score=0.5,  # Lower threshold for testing
        cache_enabled=False,  # Disable cache for testing
    )
    
    # Generate script
    script = await generator.generate(
        topic="mountain sunrise",
        config=config,
        style="guided visualization",
    )
    
    # Verify script
    assert script is not None
    assert script.title is not None
    assert len(script.script) > 100
    assert script.validation is not None
    assert script.quality_score is not None
    
    # Verify components
    if script.hook:
        assert len(script.hook) > 0
    
    # Verify tags
    assert len(script.tags) > 0
    assert "meditation" in script.tags
    
    await generator.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
