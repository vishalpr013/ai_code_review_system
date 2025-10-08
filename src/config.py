"""
Configuration module for the automated code review system.
"""
import os
from typing import Dict, Any, List
from pydantic_settings import BaseSettings


class ReviewCriteria:
    """Configuration for review criteria and their labels."""
    
    CRITERIA = {
        "areCodeChangesOptimized": {
            "label": "Are Code Changes Optimized",
            "description": "Evaluates if the code changes are optimized for performance and efficiency",
            "weight": 1.0
        },
        "areCodeChangesRelative": {
            "label": "Are Code Changes Relative",
            "description": "Checks if code changes are relevant to the intended functionality",
            "weight": 1.0
        },
        "isCodeFormatted": {
            "label": "Is Code Formatted",
            "description": "Verifies proper code formatting and style consistency",
            "weight": 0.8
        },
        "isCodeWellWritten": {
            "label": "Is Code Well Written",
            "description": "Assesses overall code quality and readability",
            "weight": 1.2
        },
        "areCommentsWritten": {
            "label": "Are Comments Written",
            "description": "Checks for adequate and meaningful comments",
            "weight": 0.9
        },
        "cyclomaticComplexityScore": {
            "label": "Cyclomatic Complexity Score",
            "description": "Measures code complexity using cyclomatic complexity",
            "weight": 1.1
        },
        "missingElements": {
            "label": "Missing Elements",
            "description": "Identifies missing components like error handling, validation",
            "weight": 1.0
        },
        "loopholes": {
            "label": "Loopholes",
            "description": "Identifies potential logic gaps or edge cases",
            "weight": 1.2
        },
        "isCommitMessageWellWritten": {
            "label": "Is Commit Message Well Written",
            "description": "Evaluates commit message quality and informativeness",
            "weight": 0.7
        },
        "isNamingConventionFollowed": {
            "label": "Is Naming Convention Followed",
            "description": "Checks adherence to naming conventions",
            "weight": 0.8
        },
        "areThereAnySpellingMistakes": {
            "label": "Are There Any Spelling Mistakes",
            "description": "Identifies spelling errors in code and comments",
            "weight": 0.6
        },
        "securityConcernsAny": {
            "label": "Security Concerns Any",
            "description": "Identifies potential security vulnerabilities",
            "weight": 1.5
        },
        "isCodeDuplicated": {
            "label": "Is Code Duplicated",
            "description": "Detects code duplication and suggests refactoring",
            "weight": 1.0
        },
        "areConstantsDefinedCentrally": {
            "label": "Are Constants Defined Centrally",
            "description": "Checks if constants are properly centralized",
            "weight": 0.8
        },
        "isCodeModular": {
            "label": "Is Code Modular",
            "description": "Evaluates code modularity and separation of concerns",
            "weight": 1.1
        },
        "isLoggingDoneProperly": {
            "label": "Is Logging Done Properly",
            "description": "Checks for proper logging implementation",
            "weight": 0.9
        }
    }


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Gemini API Configuration
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash-latest"
    gemini_temperature: float = 0.3
    gemini_max_tokens: int = 4000
    
    # Gerrit Configuration
    gerrit_host: str = ""
    gerrit_port: int = 8080
    gerrit_username: str = ""
    gerrit_password: str = ""
    gerrit_project: str = ""
    
    # Application Configuration
    app_host: str = "0.0.0.0"
    app_port: int = 5000
    app_debug: bool = False
    webhook_secret: str = ""
    
    # Review Configuration
    min_review_score: float = 7.0
    auto_post_review: bool = True
    review_timeout_seconds: int = 300
    
    # Logging Configuration
    log_level: str = "INFO"
    log_file: str = "logs/code_review.log"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()


def get_review_criteria() -> Dict[str, Any]:
    """Get review criteria configuration."""
    return ReviewCriteria.CRITERIA


def get_scoring_weights() -> Dict[str, float]:
    """Get scoring weights for each criteria."""
    return {
        criterion: config["weight"] 
        for criterion, config in ReviewCriteria.CRITERIA.items()
    }


# Initialize settings instance
settings = get_settings()
