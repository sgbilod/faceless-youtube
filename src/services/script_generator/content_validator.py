"""
Faceless YouTube - Content Validator

Validates generated scripts for quality, safety, and compliance.
"""

import re
from dataclasses import dataclass
from typing import List, Optional, Set
from enum import Enum


class ValidationIssue(str, Enum):
    """Types of validation issues"""
    TOO_SHORT = "too_short"
    TOO_LONG = "too_long"
    PROFANITY = "profanity"
    HATE_SPEECH = "hate_speech"
    MEDICAL_ADVICE = "medical_advice"
    FINANCIAL_ADVICE = "financial_advice"
    COPYRIGHT = "copyright"
    PERSONAL_INFO = "personal_info"
    POOR_QUALITY = "poor_quality"
    INCOMPLETE = "incomplete"


@dataclass
class ValidationResult:
    """Result of content validation"""
    
    is_valid: bool
    score: float  # 0.0-1.0
    issues: List[ValidationIssue]
    warnings: List[str]
    suggestions: List[str]
    word_count: int
    estimated_duration: float  # in seconds
    
    def __str__(self) -> str:
        """String representation"""
        status = "✓ VALID" if self.is_valid else "✗ INVALID"
        return f"{status} (Score: {self.score:.2f}, Issues: {len(self.issues)}, Words: {self.word_count})"


class ContentValidator:
    """
    Validates generated scripts for quality and compliance.
    
    Checks for:
    - Appropriate length
    - Profanity and hate speech
    - Medical/financial advice (requires disclaimers)
    - Copyright issues
    - Personal information
    - Content quality
    """
    
    # Words per minute for average speaking pace
    WPM_SLOW = 120  # Meditation, relaxed content
    WPM_NORMAL = 150  # Standard pace
    WPM_FAST = 180  # Energetic, motivational
    
    def __init__(
        self,
        min_words: int = 100,
        max_words: int = 3000,
        speaking_pace: int = WPM_NORMAL,
    ):
        """
        Initialize validator.
        
        Args:
            min_words: Minimum word count
            max_words: Maximum word count
            speaking_pace: Words per minute for duration estimation
        """
        self.min_words = min_words
        self.max_words = max_words
        self.speaking_pace = speaking_pace
        
        # Load profanity list (basic - expand as needed)
        self.profanity_list = self._load_profanity_list()
        
        # Patterns for detecting issues
        self.hate_speech_patterns = [
            r'\b(hate|attack|inferior|superior)\s+(race|religion|ethnicity|gender)',
            r'\b(all|every)\s+\w+\s+(are|deserve)',
        ]
        
        self.medical_keywords = [
            'diagnose', 'cure', 'treat', 'prescription', 'medication',
            'disease', 'illness', 'medical condition', 'disorder'
        ]
        
        self.financial_keywords = [
            'guaranteed profit', 'get rich', 'investment advice',
            'financial advice', 'buy stocks', 'sell stocks',
            'guaranteed returns', 'no risk'
        ]
        
        self.copyright_patterns = [
            r'(lyrics|song)\s+by\s+\w+',
            r'(quote|excerpt)\s+from\s+["\']',
            r'(copyright|©|®|™)',
        ]
        
        self.personal_info_patterns = [
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
            r'\b\d{3}-\d{3}-\d{4}\b',  # Phone
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
            r'\b\d{16}\b',  # Credit card
        ]
    
    def _load_profanity_list(self) -> Set[str]:
        """Load profanity word list"""
        # Basic list - expand as needed
        return {
            'damn', 'hell', 'crap', 'shit', 'fuck', 'ass', 'bitch',
            # Add more as needed - this is just a starter
        }
    
    def validate(self, script: str, niche: Optional[str] = None) -> ValidationResult:
        """
        Validate a generated script.
        
        Args:
            script: Script text to validate
            niche: Optional niche for context-specific validation
        
        Returns:
            ValidationResult with detailed feedback
        """
        issues: List[ValidationIssue] = []
        warnings: List[str] = []
        suggestions: List[str] = []
        
        # Clean script
        script_clean = script.strip()
        
        # Count words (excluding pause markers)
        words = re.findall(r'\b\w+\b', script_clean)
        word_count = len(words)
        
        # Estimate duration
        estimated_duration = (word_count / self.speaking_pace) * 60  # in seconds
        
        # Check length
        if word_count < self.min_words:
            issues.append(ValidationIssue.TOO_SHORT)
            warnings.append(f"Script is too short ({word_count} words, minimum {self.min_words})")
            suggestions.append("Add more detail or expand on key points")
        
        if word_count > self.max_words:
            issues.append(ValidationIssue.TOO_LONG)
            warnings.append(f"Script is too long ({word_count} words, maximum {self.max_words})")
            suggestions.append("Condense content or split into multiple videos")
        
        # Check for profanity
        script_lower = script_clean.lower()
        found_profanity = [word for word in self.profanity_list if word in script_lower]
        if found_profanity:
            issues.append(ValidationIssue.PROFANITY)
            warnings.append(f"Contains profanity: {', '.join(found_profanity[:3])}")
            suggestions.append("Remove or replace profane language")
        
        # Check for hate speech patterns
        for pattern in self.hate_speech_patterns:
            if re.search(pattern, script_lower, re.IGNORECASE):
                issues.append(ValidationIssue.HATE_SPEECH)
                warnings.append("Potentially contains hate speech or discriminatory language")
                suggestions.append("Review and remove any discriminatory content")
                break
        
        # Check for medical advice (context-dependent)
        medical_matches = [kw for kw in self.medical_keywords if kw in script_lower]
        if medical_matches and 'disclaimer' not in script_lower:
            issues.append(ValidationIssue.MEDICAL_ADVICE)
            warnings.append("Contains medical terminology without disclaimer")
            suggestions.append("Add medical disclaimer: 'Consult a healthcare professional...'")
        
        # Check for financial advice
        financial_matches = [kw for kw in self.financial_keywords if kw in script_lower]
        if financial_matches and 'not financial advice' not in script_lower:
            issues.append(ValidationIssue.FINANCIAL_ADVICE)
            warnings.append("Contains financial content without disclaimer")
            suggestions.append("Add disclaimer: 'Not financial advice. Consult a professional...'")
        
        # Check for copyright issues
        for pattern in self.copyright_patterns:
            if re.search(pattern, script_clean, re.IGNORECASE):
                issues.append(ValidationIssue.COPYRIGHT)
                warnings.append("May contain copyrighted content")
                suggestions.append("Remove or properly attribute copyrighted material")
                break
        
        # Check for personal information
        for pattern in self.personal_info_patterns:
            if re.search(pattern, script_clean):
                issues.append(ValidationIssue.PERSONAL_INFO)
                warnings.append("Contains what appears to be personal information")
                suggestions.append("Remove any personal information")
                break
        
        # Quality checks
        if word_count > 0:
            # Check for incomplete sentences
            sentences = re.split(r'[.!?]+', script_clean)
            incomplete_count = sum(1 for s in sentences if len(s.strip().split()) < 3)
            if incomplete_count > len(sentences) * 0.3:  # More than 30% incomplete
                issues.append(ValidationIssue.INCOMPLETE)
                warnings.append("Script contains many incomplete sentences")
                suggestions.append("Review and complete unfinished thoughts")
            
            # Check for repetition
            unique_words = set(w.lower() for w in words)
            repetition_ratio = len(unique_words) / word_count if word_count > 0 else 0
            if repetition_ratio < 0.3:  # Less than 30% unique words
                issues.append(ValidationIssue.POOR_QUALITY)
                warnings.append("Script has excessive word repetition")
                suggestions.append("Vary vocabulary and sentence structure")
        
        # Calculate quality score
        score = self._calculate_score(
            word_count=word_count,
            issues=issues,
            repetition_ratio=repetition_ratio if word_count > 0 else 0
        )
        
        # Determine if valid
        is_valid = len(issues) == 0 and score >= 0.7
        
        return ValidationResult(
            is_valid=is_valid,
            score=score,
            issues=issues,
            warnings=warnings,
            suggestions=suggestions,
            word_count=word_count,
            estimated_duration=estimated_duration,
        )
    
    def _calculate_score(
        self,
        word_count: int,
        issues: List[ValidationIssue],
        repetition_ratio: float
    ) -> float:
        """
        Calculate quality score (0.0-1.0).
        
        Args:
            word_count: Number of words
            issues: List of validation issues
            repetition_ratio: Ratio of unique words
        
        Returns:
            Score from 0.0 to 1.0
        """
        score = 1.0
        
        # Length penalty
        if word_count < self.min_words:
            score -= 0.3 * (1 - word_count / self.min_words)
        elif word_count > self.max_words:
            score -= 0.2 * (word_count / self.max_words - 1)
        
        # Issue penalties
        issue_penalties = {
            ValidationIssue.TOO_SHORT: 0.2,
            ValidationIssue.TOO_LONG: 0.1,
            ValidationIssue.PROFANITY: 0.3,
            ValidationIssue.HATE_SPEECH: 0.5,
            ValidationIssue.MEDICAL_ADVICE: 0.2,
            ValidationIssue.FINANCIAL_ADVICE: 0.2,
            ValidationIssue.COPYRIGHT: 0.4,
            ValidationIssue.PERSONAL_INFO: 0.5,
            ValidationIssue.POOR_QUALITY: 0.3,
            ValidationIssue.INCOMPLETE: 0.2,
        }
        
        for issue in issues:
            score -= issue_penalties.get(issue, 0.1)
        
        # Quality bonus for good repetition ratio
        if 0.4 <= repetition_ratio <= 0.7:
            score += 0.1
        
        return max(0.0, min(1.0, score))
    
    def suggest_improvements(self, script: str) -> List[str]:
        """
        Provide specific improvement suggestions.
        
        Args:
            script: Script text
        
        Returns:
            List of actionable suggestions
        """
        result = self.validate(script)
        return result.suggestions
    
    def estimate_duration(self, script: str, wpm: Optional[int] = None) -> float:
        """
        Estimate speaking duration in seconds.
        
        Args:
            script: Script text
            wpm: Words per minute (uses instance default if None)
        
        Returns:
            Estimated duration in seconds
        """
        words = len(re.findall(r'\b\w+\b', script))
        pace = wpm or self.speaking_pace
        return (words / pace) * 60
