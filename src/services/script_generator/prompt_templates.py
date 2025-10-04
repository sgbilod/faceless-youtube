"""
Faceless YouTube - Prompt Templates

Niche-specific prompt templates for script generation.
"""

from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass


class NicheType(str, Enum):
    """Supported content niches"""
    MEDITATION = "meditation"
    MOTIVATION = "motivation"
    FACTS = "facts"
    STORIES = "stories"
    EDUCATION = "education"
    TECH = "tech"
    FINANCE = "finance"
    HEALTH = "health"
    PHILOSOPHY = "philosophy"
    HISTORY = "history"


@dataclass
class PromptTemplate:
    """Template for generating scripts"""
    
    system_prompt: str
    user_prompt_template: str
    example_output: Optional[str] = None
    max_tokens: int = 2048
    temperature: float = 0.7


class PromptTemplateManager:
    """
    Manages prompt templates for different content niches.
    
    Provides optimized prompts for:
    - Meditation & relaxation content
    - Motivational speeches
    - Educational facts
    - Storytelling
    - And more...
    """
    
    def __init__(self):
        """Initialize template manager with default templates"""
        self.templates: Dict[NicheType, PromptTemplate] = {
            NicheType.MEDITATION: self._create_meditation_template(),
            NicheType.MOTIVATION: self._create_motivation_template(),
            NicheType.FACTS: self._create_facts_template(),
            NicheType.STORIES: self._create_stories_template(),
            NicheType.EDUCATION: self._create_education_template(),
            NicheType.TECH: self._create_tech_template(),
            NicheType.FINANCE: self._create_finance_template(),
            NicheType.HEALTH: self._create_health_template(),
            NicheType.PHILOSOPHY: self._create_philosophy_template(),
            NicheType.HISTORY: self._create_history_template(),
        }
    
    def get_template(self, niche: NicheType) -> PromptTemplate:
        """Get template for a specific niche"""
        return self.templates[niche]
    
    def _create_meditation_template(self) -> PromptTemplate:
        """Template for meditation and relaxation content"""
        return PromptTemplate(
            system_prompt="""You are an experienced meditation guide and mindfulness coach. 
Your task is to create calming, peaceful meditation scripts that help people relax, 
reduce stress, and find inner peace. Use gentle, soothing language with natural pauses 
and breathing cues. Focus on creating a safe, peaceful mental space.""",
            
            user_prompt_template="""Create a {duration}-minute meditation script about: {topic}

Requirements:
- Duration: Approximately {duration} minutes when spoken slowly
- Style: {style}
- Include: breathing cues, pauses, and gentle guidance
- Language: calming, present-tense, second-person ("you")
- Structure: opening (settle in), main practice, closing (return)

Additional context: {context}

Generate a complete meditation script with natural pauses marked as [PAUSE].""",
            
            example_output="""Welcome... [PAUSE] Find a comfortable position... [PAUSE]
Let your eyes gently close... [PAUSE]
Take a deep breath in... [PAUSE] and slowly release... [PAUSE]
Feel your body beginning to relax... [PAUSE]
...""",
            
            max_tokens=2048,
            temperature=0.6,  # Lower for more consistent, calming output
        )
    
    def _create_motivation_template(self) -> PromptTemplate:
        """Template for motivational content"""
        return PromptTemplate(
            system_prompt="""You are a powerful motivational speaker who inspires people to 
take action and achieve their goals. Your words are energetic, uplifting, and compelling. 
You use storytelling, powerful metaphors, and call-to-action statements to motivate your 
audience. Your content should be authentic, practical, and empowering.""",
            
            user_prompt_template="""Create a {duration}-minute motivational speech about: {topic}

Requirements:
- Duration: Approximately {duration} minutes
- Tone: {tone}
- Target audience: {audience}
- Key message: {message}
- Include: personal anecdotes, actionable advice, powerful quotes
- Structure: hook, problem, solution, call-to-action

Additional context: {context}

Generate a complete motivational script that inspires action.""",
            
            example_output="""Listen... I want to tell you something important today.
You have the power within you to change everything. Yes, EVERYTHING.
But here's the truth most people won't tell you...
Success isn't about being fearless. It's about taking action despite the fear...""",
            
            max_tokens=2048,
            temperature=0.8,  # Higher for more creative, energetic content
        )
    
    def _create_facts_template(self) -> PromptTemplate:
        """Template for educational facts content"""
        return PromptTemplate(
            system_prompt="""You are an engaging educator who makes learning fun and accessible. 
You present fascinating facts in an entertaining way, using clear explanations and interesting 
examples. Your content is accurate, well-researched, and presented in a way that sparks 
curiosity and wonder.""",
            
            user_prompt_template="""Create a {duration}-minute facts video script about: {topic}

Requirements:
- Number of facts: {count}
- Difficulty level: {level}
- Include: surprising facts, clear explanations, interesting context
- Style: engaging, conversational, educational
- Structure: intro, facts (numbered), conclusion

Additional context: {context}

Generate a complete facts script that educates and entertains.""",
            
            example_output="""Did you know? Today we're diving into 10 mind-blowing facts about the ocean.
Fact #1: The ocean covers 71% of Earth's surface, but we've only explored about 5% of it.
That means 95% of our oceans remain a mystery...""",
            
            max_tokens=2048,
            temperature=0.7,
        )
    
    def _create_stories_template(self) -> PromptTemplate:
        """Template for storytelling content"""
        return PromptTemplate(
            system_prompt="""You are a masterful storyteller who captivates audiences with 
compelling narratives. You use vivid descriptions, emotional depth, and engaging pacing 
to create memorable stories. Your narratives have clear structure, relatable characters, 
and meaningful lessons or insights.""",
            
            user_prompt_template="""Create a {duration}-minute story about: {topic}

Requirements:
- Story type: {story_type}
- Setting: {setting}
- Theme: {theme}
- Tone: {tone}
- Include: vivid descriptions, dialogue, emotional moments
- Structure: setup, conflict, climax, resolution

Additional context: {context}

Generate a complete story that captivates and moves the audience.""",
            
            example_output="""Once upon a time, in a small village nestled between mountains...
There lived a young girl named Maya who had an extraordinary gift...
She could hear the whispers of the wind, telling her stories of distant lands...""",
            
            max_tokens=3072,  # Longer for storytelling
            temperature=0.85,  # High creativity for stories
        )
    
    def _create_education_template(self) -> PromptTemplate:
        """Template for educational content"""
        return PromptTemplate(
            system_prompt="""You are an expert educator who breaks down complex topics into 
clear, understandable lessons. You use analogies, examples, and step-by-step explanations 
to make learning accessible to everyone. Your content is accurate, well-structured, and 
designed to build understanding progressively.""",
            
            user_prompt_template="""Create a {duration}-minute educational video script about: {topic}

Requirements:
- Subject: {subject}
- Target audience: {audience}
- Learning objectives: {objectives}
- Include: clear explanations, practical examples, key takeaways
- Structure: intro, main concepts, examples, summary

Additional context: {context}

Generate a complete educational script that teaches effectively.""",
            
            max_tokens=2560,
            temperature=0.6,  # Lower for factual accuracy
        )
    
    def _create_tech_template(self) -> PromptTemplate:
        """Template for technology content"""
        return PromptTemplate(
            system_prompt="""You are a tech expert who makes technology accessible and exciting. 
You explain technical concepts in simple terms without losing accuracy. Your content is 
current, practical, and helps people understand how technology impacts their lives.""",
            
            user_prompt_template="""Create a {duration}-minute tech video script about: {topic}

Requirements:
- Tech level: {level}
- Focus: {focus}
- Include: practical applications, pros/cons, future implications
- Style: accessible but accurate
- Structure: overview, explanation, real-world examples, conclusion

Additional context: {context}

Generate a complete tech script that informs and engages.""",
            
            max_tokens=2048,
            temperature=0.7,
        )
    
    def _create_finance_template(self) -> PromptTemplate:
        """Template for finance content"""
        return PromptTemplate(
            system_prompt="""You are a financial educator who helps people make better money 
decisions. You explain financial concepts clearly, provide practical advice, and emphasize 
responsible money management. Your content is empowering and action-oriented, never 
promising get-rich-quick schemes.""",
            
            user_prompt_template="""Create a {duration}-minute finance video script about: {topic}

Requirements:
- Financial concept: {concept}
- Target audience: {audience}
- Include: practical tips, examples, action steps
- Disclaimer: Always include appropriate disclaimers
- Structure: problem, explanation, solution, action plan

Additional context: {context}

Generate a complete finance script that educates responsibly.""",
            
            max_tokens=2048,
            temperature=0.6,
        )
    
    def _create_health_template(self) -> PromptTemplate:
        """Template for health and wellness content"""
        return PromptTemplate(
            system_prompt="""You are a health and wellness educator who provides evidence-based 
information in an accessible way. You emphasize the importance of consulting healthcare 
professionals and present information that empowers healthy choices. Your content is 
balanced, scientific, and practical.""",
            
            user_prompt_template="""Create a {duration}-minute health video script about: {topic}

Requirements:
- Health topic: {health_topic}
- Target audience: {audience}
- Include: evidence-based info, practical tips, professional disclaimer
- Tone: supportive, informative, encouraging
- Structure: intro, information, practical application, disclaimer

Additional context: {context}

Generate a complete health script with appropriate disclaimers.""",
            
            max_tokens=2048,
            temperature=0.6,
        )
    
    def _create_philosophy_template(self) -> PromptTemplate:
        """Template for philosophical content"""
        return PromptTemplate(
            system_prompt="""You are a philosophy educator who makes deep concepts accessible 
and relevant to everyday life. You explore ideas thoughtfully, present multiple perspectives, 
and encourage critical thinking. Your content connects ancient wisdom with modern life.""",
            
            user_prompt_template="""Create a {duration}-minute philosophy video script about: {topic}

Requirements:
- Philosophical concept: {concept}
- Include: historical context, multiple perspectives, modern relevance
- Style: thoughtful, balanced, accessible
- Structure: question, exploration, perspectives, reflection

Additional context: {context}

Generate a complete philosophy script that provokes thought.""",
            
            max_tokens=2560,
            temperature=0.75,
        )
    
    def _create_history_template(self) -> PromptTemplate:
        """Template for historical content"""
        return PromptTemplate(
            system_prompt="""You are a history educator who brings the past to life through 
engaging narratives and fascinating details. You present historical events accurately while 
making them relatable and interesting. Your content connects historical events to present-day 
relevance.""",
            
            user_prompt_template="""Create a {duration}-minute history video script about: {topic}

Requirements:
- Historical period: {period}
- Focus: {focus}
- Include: key facts, interesting details, historical context, modern relevance
- Style: narrative, engaging, accurate
- Structure: context, main events, significance, legacy

Additional context: {context}

Generate a complete history script that educates and engages.""",
            
            max_tokens=2560,
            temperature=0.7,
        )
    
    def format_prompt(
        self,
        niche: NicheType,
        **kwargs
    ) -> tuple[str, str]:
        """
        Format a prompt template with provided parameters.
        
        Args:
            niche: Content niche
            **kwargs: Parameters to fill in the template
        
        Returns:
            Tuple of (system_prompt, formatted_user_prompt)
        """
        template = self.get_template(niche)
        
        # Fill in template with provided kwargs
        user_prompt = template.user_prompt_template.format(**kwargs)
        
        return template.system_prompt, user_prompt
    
    def add_custom_template(
        self,
        niche_name: str,
        template: PromptTemplate
    ) -> None:
        """
        Add a custom template for a new niche.
        
        Args:
            niche_name: Name of the niche
            template: Template configuration
        """
        # For custom niches, we'd extend the NicheType enum
        # For now, store in templates dict with string key
        self.templates[niche_name] = template  # type: ignore
