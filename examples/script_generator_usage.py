"""
Script Generator Usage Examples

This file demonstrates how to use the AI-powered script generation service
for creating content across different niches.

Prerequisites:
1. Install Ollama: https://ollama.ai/install
2. Pull a model: ollama pull mistral
3. Start Ollama service: ollama serve
4. Configure .env with OLLAMA_HOST and OLLAMA_MODEL
"""

import asyncio
from src.services.script_generator import (
    OllamaClient,
    OllamaConfig,
    ScriptGenerator,
    PromptTemplateManager,
    ContentValidator,
    ScriptConfig,
    NicheType,
)


# ============================
# Example 1: Simple Script Generation
# ============================
async def example_1_simple_generation():
    """Generate a basic meditation script."""
    print("\n=== Example 1: Simple Meditation Script ===\n")
    
    # Initialize generator with defaults
    generator = ScriptGenerator()
    
    # Generate a 5-minute meditation script
    config = ScriptConfig(
        duration_minutes=5,
        niche=NicheType.MEDITATION,
        tone="calm and soothing",
        target_audience="beginners",
    )
    
    script = await generator.generate(
        topic="Morning Mindfulness Meditation",
        config=config
    )
    
    print(f"Title: {script.title}")
    print(f"Word Count: {script.word_count}")
    print(f"Estimated Duration: {script.estimated_duration:.1f} seconds")
    print(f"Quality Score: {script.quality_score:.2f}")
    print(f"\nHook: {script.hook}")
    print(f"\nScript Preview:\n{script.script[:300]}...")
    print(f"\nCall to Action: {script.call_to_action}")
    print(f"Tags: {', '.join(script.tags)}")


# ============================
# Example 2: Multiple Niches
# ============================
async def example_2_multiple_niches():
    """Generate scripts for different content types."""
    print("\n=== Example 2: Multiple Niches ===\n")
    
    generator = ScriptGenerator()
    
    # Different niche examples
    topics = [
        ("The Power of Consistency", NicheType.MOTIVATION, "energetic and inspiring"),
        ("5 Fascinating Space Facts", NicheType.FACTS, "informative and engaging"),
        ("The Hero's Journey", NicheType.STORIES, "dramatic and emotional"),
    ]
    
    for topic, niche, tone in topics:
        config = ScriptConfig(
            duration_minutes=3,
            niche=niche,
            tone=tone,
            target_audience="general audience",
        )
        
        script = await generator.generate(topic, config)
        print(f"\n{niche.value.upper()}: {script.title}")
        print(f"Words: {script.word_count} | Quality: {script.quality_score:.2f}")
        print(f"Hook: {script.hook}")


# ============================
# Example 3: Batch Generation
# ============================
async def example_3_batch_generation():
    """Generate multiple scripts in parallel."""
    print("\n=== Example 3: Batch Generation ===\n")
    
    generator = ScriptGenerator()
    
    # Generate scripts for a content series
    topics = [
        "Introduction to Stoicism",
        "Marcus Aurelius and Meditation",
        "The Dichotomy of Control",
        "Amor Fati: Loving Your Fate",
    ]
    
    config = ScriptConfig(
        duration_minutes=4,
        niche=NicheType.PHILOSOPHY,
        tone="wise and contemplative",
        target_audience="philosophy enthusiasts",
    )
    
    print(f"Generating {len(topics)} scripts in parallel...")
    scripts = await generator.generate_batch(topics, config)
    
    print(f"\nGenerated {len(scripts)} scripts:")
    for i, script in enumerate(scripts, 1):
        print(f"{i}. {script.title}")
        print(f"   Quality: {script.quality_score:.2f} | Words: {script.word_count}")


# ============================
# Example 4: Custom Configuration
# ============================
async def example_4_custom_config():
    """Use custom AI model settings."""
    print("\n=== Example 4: Custom Configuration ===\n")
    
    # Custom Ollama configuration
    ollama_config = OllamaConfig(
        host="localhost",
        port=11434,
        model="llama2",  # Use different model
        default_temperature=0.85,  # Higher creativity
        timeout=120,
    )
    
    # Custom generator with specific settings
    generator = ScriptGenerator(ollama_config=ollama_config)
    
    # Generate creative story with custom settings
    config = ScriptConfig(
        duration_minutes=7,
        niche=NicheType.STORIES,
        tone="mysterious and suspenseful",
        target_audience="thriller fans",
        temperature=0.9,  # Very creative
        max_tokens=3000,
        max_retries=5,
    )
    
    script = await generator.generate(
        topic="The Last Light in the Tower",
        config=config
    )
    
    print(f"Generated with {script.model_used}")
    print(f"Temperature: {script.temperature}")
    print(f"Tokens: {script.prompt_tokens}")
    print(f"\nTitle: {script.title}")
    print(f"Quality: {script.quality_score:.2f}")


# ============================
# Example 5: Validation Details
# ============================
async def example_5_validation():
    """Examine validation results in detail."""
    print("\n=== Example 5: Content Validation ===\n")
    
    generator = ScriptGenerator()
    
    # Generate health content (will check for disclaimers)
    config = ScriptConfig(
        duration_minutes=5,
        niche=NicheType.HEALTH,
        tone="informative and careful",
        target_audience="health-conscious adults",
        validate=True,
        min_quality_score=0.75,
    )
    
    script = await generator.generate(
        topic="Benefits of Morning Exercise",
        config=config
    )
    
    # Check validation details
    validation = script.validation
    print(f"Validation Status: {'✓ PASSED' if validation['is_valid'] else '✗ FAILED'}")
    print(f"Quality Score: {validation['score']:.2f}")
    print(f"Word Count: {validation['word_count']}")
    print(f"Duration: {validation['estimated_duration']:.1f}s")
    
    if validation['issues']:
        print(f"\nIssues: {', '.join(validation['issues'])}")
    
    if validation['warnings']:
        print(f"Warnings: {', '.join(validation['warnings'])}")
    
    if validation['suggestions']:
        print(f"\nSuggestions:")
        for suggestion in validation['suggestions']:
            print(f"  - {suggestion}")


# ============================
# Example 6: Regeneration with Feedback
# ============================
async def example_6_regeneration():
    """Improve a script based on feedback."""
    print("\n=== Example 6: Regeneration with Feedback ===\n")
    
    generator = ScriptGenerator()
    
    config = ScriptConfig(
        duration_minutes=4,
        niche=NicheType.TECH,
        tone="accessible and explanatory",
        target_audience="tech beginners",
    )
    
    # Generate initial script
    script_v1 = await generator.generate(
        topic="Understanding Artificial Intelligence",
        config=config
    )
    
    print(f"Version 1 Quality: {script_v1.quality_score:.2f}")
    print(f"V1 Hook: {script_v1.hook}\n")
    
    # Regenerate with feedback
    feedback = "Make the introduction more engaging with a real-world example. Add more analogies to explain complex concepts."
    
    script_v2 = await generator.regenerate_with_feedback(
        script_v1.script,
        feedback,
        config
    )
    
    print(f"Version 2 Quality: {script_v2.quality_score:.2f}")
    print(f"V2 Hook: {script_v2.hook}")
    print(f"\nImprovement: {((script_v2.quality_score - script_v1.quality_score) / script_v1.quality_score * 100):.1f}%")


# ============================
# Example 7: Cache Benefits
# ============================
async def example_7_caching():
    """Demonstrate caching performance benefits."""
    print("\n=== Example 7: Cache Performance ===\n")
    
    import time
    
    generator = ScriptGenerator()
    
    config = ScriptConfig(
        duration_minutes=3,
        niche=NicheType.FACTS,
        cache_enabled=True,
        cache_ttl=3600,  # 1 hour
    )
    
    topic = "10 Mind-Blowing Ocean Facts"
    
    # First generation (cache miss)
    print("First generation (cache miss)...")
    start = time.time()
    script_1 = await generator.generate(topic, config)
    duration_1 = time.time() - start
    print(f"Time: {duration_1:.2f}s")
    
    # Second generation (cache hit)
    print("\nSecond generation (cache hit)...")
    start = time.time()
    script_2 = await generator.generate(topic, config)
    duration_2 = time.time() - start
    print(f"Time: {duration_2:.2f}s")
    
    print(f"\nSpeedup: {duration_1 / duration_2:.1f}x faster")
    print(f"Same content: {script_1.id == script_2.id}")


# ============================
# Example 8: Direct Ollama Usage
# ============================
async def example_8_ollama_direct():
    """Use Ollama client directly for custom prompts."""
    print("\n=== Example 8: Direct Ollama Usage ===\n")
    
    client = OllamaClient()
    
    # Check health
    healthy = await client.health_check()
    print(f"Ollama Status: {'✓ Online' if healthy else '✗ Offline'}")
    
    if healthy:
        # List available models
        models = await client.list_models()
        print(f"\nAvailable Models: {', '.join(models)}")
        
        # Generate custom content
        prompt = "Write a 30-second script about the beauty of sunrise in 2 sentences."
        response = await client.generate(prompt, temperature=0.8, max_tokens=100)
        print(f"\nCustom Generation:\n{response}")


# ============================
# Example 9: Template Customization
# ============================
async def example_9_custom_template():
    """Add and use a custom prompt template."""
    print("\n=== Example 9: Custom Template ===\n")
    
    template_manager = PromptTemplateManager()
    
    # Add custom template for "comedy" niche
    from src.services.script_generator.prompt_templates import PromptTemplate
    
    comedy_template = PromptTemplate(
        system_prompt=(
            "You are a comedy writer creating hilarious, observational humor scripts. "
            "Use relatable situations, clever wordplay, and perfect timing. "
            "Keep it clean and universally funny."
        ),
        user_prompt_template=(
            "Write a {duration_minutes}-minute comedy script about: {topic}\n"
            "Tone: {tone}\n"
            "Target audience: {target_audience}\n\n"
            "Include setup, punchlines, and callbacks. Make it memorable!"
        ),
        max_tokens=2048,
        temperature=0.85,
    )
    
    # Custom niche value
    custom_niche = "comedy"
    template_manager.add_custom_template(custom_niche, comedy_template)
    
    # Format and use the template
    formatted = template_manager.format_prompt(
        custom_niche,
        topic="Online Shopping Expectations vs Reality",
        duration_minutes=5,
        tone="witty and relatable",
        target_audience="millennials and gen-z",
    )
    
    print("Custom Template System Prompt:")
    print(formatted["system_prompt"][:200] + "...\n")
    print("Custom Template User Prompt:")
    print(formatted["user_prompt"][:200] + "...")


# ============================
# Main Runner
# ============================
async def main():
    """Run all examples."""
    examples = [
        ("Simple Generation", example_1_simple_generation),
        ("Multiple Niches", example_2_multiple_niches),
        ("Batch Generation", example_3_batch_generation),
        ("Custom Configuration", example_4_custom_config),
        ("Validation Details", example_5_validation),
        ("Regeneration with Feedback", example_6_regeneration),
        ("Cache Performance", example_7_caching),
        ("Direct Ollama Usage", example_8_ollama_direct),
        ("Custom Template", example_9_custom_template),
    ]
    
    print("=" * 60)
    print("SCRIPT GENERATOR USAGE EXAMPLES")
    print("=" * 60)
    
    for name, example_func in examples:
        try:
            await example_func()
        except Exception as e:
            print(f"\n⚠ {name} failed: {e}")
        
        print("\n" + "-" * 60)
    
    print("\n✓ All examples completed!")


if __name__ == "__main__":
    # Run examples
    asyncio.run(main())
