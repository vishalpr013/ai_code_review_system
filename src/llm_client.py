"""
Google Gemini LLM client for code review analysis.
"""
import json
import logging
from typing import Dict, List, Optional, Any
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from config import settings, get_review_criteria
from utils import setup_logger

logger = setup_logger(__name__)


class GeminiClient:
    """Client for interacting with Google Gemini API."""
    
    def __init__(self, api_key: str = None, model_name: str = None):
        """Initialize Gemini client."""
        self.api_key = api_key or settings.gemini_api_key
        self.model_name = model_name or settings.gemini_model
        
        if not self.api_key:
            raise ValueError("Gemini API key is required")
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        
        # Initialize model
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config=genai.types.GenerationConfig(
                temperature=settings.gemini_temperature,
                max_output_tokens=settings.gemini_max_tokens,
                top_p=0.95,
                top_k=64,
            ),
            safety_settings={
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            }
        )
        
        logger.info(f"Initialized Gemini client with model {self.model_name}")
    
    def analyze_code_changes(self, review_context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze code changes and provide comprehensive review."""
        try:
            prompt = self._build_review_prompt(review_context)
            logger.info("Sending code review request to Gemini")
            
            response = self.model.generate_content(prompt)
            
            if not response or not response.text:
                logger.error("Empty response from Gemini")
                return None
            
            # Parse the JSON response
            review_result = json.loads(response.text)
            logger.info("Successfully received code review from Gemini")
            
            return review_result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response as JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"Error during Gemini analysis: {e}")
            return None
    
    def _build_review_prompt(self, review_context: Dict[str, Any]) -> str:
        """Build comprehensive prompt for code review."""
        criteria = get_review_criteria()
        
        prompt = f"""
You are an expert code reviewer with extensive experience in software development, security, and best practices. 
Analyze the following code changes and provide a comprehensive review based on the specified criteria.

## Code Change Information
**Project**: {review_context['change_info']['project']}
**Branch**: {review_context['change_info']['branch']}
**Author**: {review_context['change_info']['owner']}
**Subject**: {review_context['change_info']['subject']}
**Files Changed**: {review_context['file_count']}
**Lines Changed**: {review_context['total_lines_changed']}

## Commit Message
```
{review_context['commit_message']}
```

## Code Changes (Diffs)
"""
        
        # Add file diffs
        for file_path, diff in review_context['files_diff'].items():
            prompt += f"\n### File: `{file_path}`\n```diff\n{diff}\n```\n"
        
        prompt += f"""

## Review Criteria
Please analyze the code changes against each of the following criteria and provide:
1. A score from 1-10 (10 being excellent, 1 being poor)
2. Detailed feedback explaining your assessment
3. Specific suggestions for improvement

"""
        
        # Add each criterion with description
        for criterion_key, criterion_info in criteria.items():
            prompt += f"**{criterion_info['label']}**: {criterion_info['description']}\n"
        
        prompt += """

## Response Format
Respond with a valid JSON object following this exact structure:

```json
{
  "overall_score": <float between 1-10>,
  "overall_feedback": "<comprehensive summary of the review>",
  "criteria_scores": {
"""
        
        # Add criteria scores structure
        criteria_list = []
        for criterion_key in criteria.keys():
            criteria_list.append(f'    "{criterion_key}": {{"score": <1-10>, "feedback": "<detailed feedback>", "suggestions": ["<suggestion1>", "<suggestion2>"]}}')
        
        prompt += ",\n".join(criteria_list)
        
        prompt += """
  },
  "summary": {
    "strengths": ["<strength1>", "<strength2>", ...],
    "weaknesses": ["<weakness1>", "<weakness2>", ...],
    "critical_issues": ["<issue1>", "<issue2>", ...],
    "recommendations": ["<recommendation1>", "<recommendation2>", ...]
  },
  "approval_recommendation": "<APPROVE|NEEDS_WORK|REJECT>",
  "confidence_level": <float between 0-1>
}
```

## Important Guidelines
- Be thorough but concise in your feedback
- Focus on actionable suggestions
- Consider security implications carefully
- Evaluate code maintainability and readability
- Check for adherence to best practices
- Identify potential performance issues
- Look for proper error handling
- Assess test coverage implications
- Consider the broader impact of changes

Provide your analysis now:
"""
        
        return prompt
    
    def generate_summary_comment(self, review_result: Dict[str, Any]) -> str:
        """Generate a summary comment for posting to Gerrit."""
        if not review_result:
            return "Automated code review failed to complete."
        
        overall_score = review_result.get('overall_score', 0)
        approval = review_result.get('approval_recommendation', 'NEEDS_WORK')
        
        # Score-based emoji
        score_emoji = "🔴" if overall_score < 5 else "🟡" if overall_score < 7 else "🟢"
        
        comment = f"""
## 🤖 Automated Code Review {score_emoji}

**Overall Score**: {overall_score:.1f}/10
**Recommendation**: {approval}

### Summary
{review_result.get('overall_feedback', 'No feedback available')}

### Key Findings
"""
        
        # Add strengths and weaknesses
        summary = review_result.get('summary', {})
        
        if summary.get('strengths'):
            comment += "\n**✅ Strengths:**\n"
            for strength in summary['strengths'][:3]:  # Limit to top 3
                comment += f"- {strength}\n"
        
        if summary.get('weaknesses'):
            comment += "\n**⚠️ Areas for Improvement:**\n"
            for weakness in summary['weaknesses'][:3]:  # Limit to top 3
                comment += f"- {weakness}\n"
        
        if summary.get('critical_issues'):
            comment += "\n**🚨 Critical Issues:**\n"
            for issue in summary['critical_issues']:
                comment += f"- {issue}\n"
        
        # Add top failing criteria
        criteria_scores = review_result.get('criteria_scores', {})
        low_scores = []
        
        for criterion, data in criteria_scores.items():
            if isinstance(data, dict) and data.get('score', 10) < 6:
                criterion_info = get_review_criteria().get(criterion, {})
                label = criterion_info.get('label', criterion)
                score = data.get('score', 0)
                low_scores.append((label, score, data.get('feedback', '')))
        
        if low_scores:
            comment += "\n### Low Scoring Areas\n"
            # Sort by score (lowest first)
            low_scores.sort(key=lambda x: x[1])
            
            for label, score, feedback in low_scores[:5]:  # Top 5 issues
                comment += f"**{label}** ({score}/10): {feedback[:100]}...\n"
        
        if summary.get('recommendations'):
            comment += "\n### Recommendations\n"
            for rec in summary['recommendations'][:3]:  # Top 3 recommendations
                comment += f"- {rec}\n"
        
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
        comment += f"\n---\n*Automated review generated at {timestamp}*"
        
        return comment
    
    def test_connection(self) -> bool:
        """Test connection to Gemini API."""
        try:
            response = self.model.generate_content("Hello, this is a test message.")
            return response and response.text is not None
        except Exception as e:
            logger.error(f"Gemini connection test failed: {e}")
            return False


class ReviewAnalyzer:
    """High-level analyzer that coordinates the review process."""
    
    def __init__(self, gemini_client: GeminiClient = None):
        """Initialize review analyzer."""
        self.gemini_client = gemini_client or GeminiClient()
    
    def analyze_change(self, review_context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Perform complete analysis of a code change."""
        logger.info(f"Starting analysis for change {review_context['change_info']['change_id']}")
        
        # Get AI analysis
        review_result = self.gemini_client.analyze_code_changes(review_context)
        
        if not review_result:
            return None
        
        # Add metadata
        review_result['metadata'] = {
            'analyzer_version': '1.0.0',
            'model_used': self.gemini_client.model_name,
            'analysis_timestamp': review_context.get('timestamp'),
            'change_info': review_context['change_info']
        }
        
        # Calculate weighted score if needed
        review_result['weighted_score'] = self._calculate_weighted_score(review_result)
        
        logger.info(f"Analysis completed with overall score: {review_result.get('overall_score', 'N/A')}")
        
        return review_result
    
    def _calculate_weighted_score(self, review_result: Dict[str, Any]) -> float:
        """Calculate weighted score based on criteria importance."""
        from .config import get_scoring_weights
        
        criteria_scores = review_result.get('criteria_scores', {})
        weights = get_scoring_weights()
        
        total_weighted_score = 0
        total_weight = 0
        
        for criterion, weight in weights.items():
            if criterion in criteria_scores:
                score_data = criteria_scores[criterion]
                if isinstance(score_data, dict) and 'score' in score_data:
                    total_weighted_score += score_data['score'] * weight
                    total_weight += weight
        
        if total_weight > 0:
            return round(total_weighted_score / total_weight, 2)
        
        return review_result.get('overall_score', 0)
