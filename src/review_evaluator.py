"""
Review evaluator that coordinates the entire code review process.
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from config import settings, get_review_criteria, get_scoring_weights
from gerrit_client import GerritClient, CodeChange
from llm_client import GeminiClient, ReviewAnalyzer
from utils import (
    setup_logger, parse_diff, calculate_cyclomatic_complexity,
    detect_code_smells, extract_security_concerns, validate_naming_conventions,
    check_spelling, calculate_file_metrics, generate_review_id,
    save_review_result, format_timestamp
)

logger = setup_logger(__name__)


class ReviewEvaluator:
    """Main class that orchestrates the code review process."""
    
    def __init__(self, gerrit_client: GerritClient = None, gemini_client: GeminiClient = None):
        """Initialize the review evaluator."""
        self.gerrit_client = gerrit_client or GerritClient()
        self.gemini_client = gemini_client or GeminiClient()
        self.review_analyzer = ReviewAnalyzer(self.gemini_client)
        
        logger.info("Review evaluator initialized")
    
    async def evaluate_change(self, webhook_payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Evaluate a code change from a webhook payload."""
        try:
            # Extract change information
            change_info = self.gerrit_client.extract_change_info(webhook_payload)
            if not change_info:
                logger.error("Failed to extract change info from webhook payload")
                return None
            
            logger.info(f"Starting evaluation for change {change_info['change_id']}")
            
            # Create code change object and load data
            code_change = CodeChange(change_info, self.gerrit_client)
            if not await code_change.load_change_data():
                logger.error("Failed to load change data from Gerrit")
                return None
            
            # Perform comprehensive evaluation
            return await self._perform_comprehensive_review(code_change)
            
        except Exception as e:
            logger.error(f"Error during change evaluation: {e}")
            return None
    
    async def _perform_comprehensive_review(self, code_change: CodeChange) -> Dict[str, Any]:
        """Perform comprehensive review combining AI analysis with rule-based checks."""
        
        # Get review context
        review_context = code_change.get_review_context()
        review_context['timestamp'] = format_timestamp()
        
        # Generate review ID
        review_id = generate_review_id(
            code_change.change_info['change_id'],
            code_change.change_info['revision_id']
        )
        
        # Perform AI-based analysis
        logger.info("Performing AI-based code analysis")
        ai_review = self.review_analyzer.analyze_change(review_context)
        
        if not ai_review:
            logger.error("AI analysis failed")
            return None
        
        # Perform rule-based analysis
        logger.info("Performing rule-based analysis")
        rule_based_analysis = self._perform_rule_based_analysis(code_change)
        
        # Combine results
        comprehensive_review = self._combine_analyses(ai_review, rule_based_analysis)
        
        # Add metadata
        comprehensive_review['review_metadata'] = {
            'review_id': review_id,
            'change_info': code_change.change_info,
            'evaluation_timestamp': review_context['timestamp'],
            'evaluator_version': '1.0.0',
            'ai_model': self.gemini_client.model_name,
            'rule_based_checks': True
        }
        
        # Save review result
        save_review_result(review_id, comprehensive_review)
        
        logger.info(f"Comprehensive review completed for {code_change.change_info['change_id']}")
        
        return comprehensive_review
    
    def _perform_rule_based_analysis(self, code_change: CodeChange) -> Dict[str, Any]:
        """Perform rule-based analysis on the code changes."""
        analysis = {
            'file_analyses': {},
            'overall_metrics': {
                'total_files': len(code_change.files_diff),
                'total_lines_changed': 0,
                'security_concerns': [],
                'code_smells': [],
                'spelling_mistakes': [],
                'naming_violations': [],
                'complexity_metrics': {}
            }
        }
        
        total_complexity = 0
        total_files_with_code = 0
        
        # Analyze each file
        for file_path, diff_content in code_change.files_diff.items():
            file_analysis = self._analyze_file(file_path, diff_content)
            analysis['file_analyses'][file_path] = file_analysis
            
            # Aggregate metrics
            analysis['overall_metrics']['total_lines_changed'] += file_analysis['lines_changed']
            analysis['overall_metrics']['security_concerns'].extend(file_analysis['security_concerns'])
            analysis['overall_metrics']['code_smells'].extend(file_analysis['code_smells'])
            analysis['overall_metrics']['spelling_mistakes'].extend(file_analysis['spelling_mistakes'])
            analysis['overall_metrics']['naming_violations'].extend(file_analysis['naming_violations'])
            
            if file_analysis['complexity'] > 1:
                total_complexity += file_analysis['complexity']
                total_files_with_code += 1
        
        # Calculate overall complexity
        if total_files_with_code > 0:
            analysis['overall_metrics']['complexity_metrics'] = {
                'average_complexity': total_complexity / total_files_with_code,
                'total_complexity': total_complexity,
                'files_analyzed': total_files_with_code
            }
        
        # Analyze commit message
        analysis['commit_analysis'] = self._analyze_commit_message(code_change.commit_message)
        
        return analysis
    
    def _analyze_file(self, file_path: str, diff_content: str) -> Dict[str, Any]:
        """Analyze a single file."""
        
        # Parse diff
        diff_info = parse_diff(diff_content)
        
        # Extract added content for analysis
        added_code = '\n'.join(diff_info['added_content'])
        
        # Determine language
        language = self._determine_language(file_path)
        
        # Calculate complexity
        complexity = calculate_cyclomatic_complexity(added_code)
        
        # Detect issues
        code_smells = detect_code_smells(added_code, file_path)
        security_concerns = extract_security_concerns(added_code)
        naming_violations = validate_naming_conventions(added_code, language)
        spelling_mistakes = check_spelling(added_code)
        
        # Calculate file metrics
        file_metrics = calculate_file_metrics(added_code)
        
        return {
            'file_path': file_path,
            'language': language,
            'lines_changed': diff_info['modified_lines'],
            'lines_added': diff_info['added_lines'],
            'lines_removed': diff_info['removed_lines'],
            'complexity': complexity,
            'complexity_indicators': diff_info['complexity_indicators'],
            'code_smells': code_smells,
            'security_concerns': security_concerns,
            'naming_violations': naming_violations,
            'spelling_mistakes': spelling_mistakes,
            'file_metrics': file_metrics
        }
    
    def _analyze_commit_message(self, commit_message: str) -> Dict[str, Any]:
        """Analyze commit message quality."""
        if not commit_message:
            return {
                'quality_score': 1,
                'issues': ['Commit message is empty'],
                'suggestions': ['Add a descriptive commit message']
            }
        
        issues = []
        suggestions = []
        score = 10
        
        lines = commit_message.strip().split('\n')
        first_line = lines[0] if lines else ""
        
        # Check length of first line
        if len(first_line) > 72:
            issues.append("First line is too long (>72 characters)")
            suggestions.append("Keep the first line under 72 characters")
            score -= 2
        
        if len(first_line) < 10:
            issues.append("First line is too short (<10 characters)")
            suggestions.append("Make the commit message more descriptive")
            score -= 2
        
        # Check for imperative mood (simplified)
        if not first_line.startswith(('Add', 'Fix', 'Update', 'Remove', 'Create', 'Implement', 'Refactor')):
            suggestions.append("Consider using imperative mood (Add, Fix, Update, etc.)")
            score -= 1
        
        # Check for blank line after first line
        if len(lines) > 1 and lines[1].strip():
            issues.append("Missing blank line after first line")
            suggestions.append("Add a blank line after the first line")
            score -= 1
        
        # Check for spelling
        spelling_mistakes = check_spelling(commit_message)
        if spelling_mistakes:
            issues.append(f"Spelling mistakes found: {len(spelling_mistakes)}")
            suggestions.extend([f"Fix spelling: {mistake['word']} -> {mistake['suggestion']}" 
                              for mistake in spelling_mistakes[:3]])
            score -= len(spelling_mistakes)
        
        return {
            'quality_score': max(1, score),
            'message_length': len(commit_message),
            'first_line_length': len(first_line),
            'line_count': len(lines),
            'issues': issues,
            'suggestions': suggestions,
            'spelling_mistakes': spelling_mistakes
        }
    
    def _determine_language(self, file_path: str) -> str:
        """Determine programming language from file extension."""
        extension_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.cs': 'csharp',
            '.php': 'php',
            '.rb': 'ruby',
            '.go': 'go',
            '.rs': 'rust',
            '.kt': 'kotlin',
            '.swift': 'swift',
            '.html': 'html',
            '.css': 'css',
            '.sql': 'sql',
            '.sh': 'shell',
            '.yml': 'yaml',
            '.yaml': 'yaml',
            '.json': 'json',
            '.xml': 'xml'
        }
        
        for ext, lang in extension_map.items():
            if file_path.lower().endswith(ext):
                return lang
        
        return 'unknown'
    
    def _combine_analyses(self, ai_review: Dict[str, Any], rule_based_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Combine AI and rule-based analyses into comprehensive review."""
        
        # Start with AI review as base
        combined_review = ai_review.copy()
        
        # Enhance criteria scores with rule-based insights
        criteria_scores = combined_review.get('criteria_scores', {})
        
        # Enhance cyclomatic complexity score
        if 'cyclomaticComplexityScore' in criteria_scores:
            complexity_metrics = rule_based_analysis['overall_metrics'].get('complexity_metrics', {})
            if complexity_metrics:
                avg_complexity = complexity_metrics.get('average_complexity', 1)
                # Adjust score based on complexity
                if avg_complexity > 10:
                    criteria_scores['cyclomaticComplexityScore']['score'] = min(
                        criteria_scores['cyclomaticComplexityScore']['score'], 
                        3
                    )
                    criteria_scores['cyclomaticComplexityScore']['feedback'] += f" Rule-based analysis found high complexity (avg: {avg_complexity:.1f})."
        
        # Enhance security concerns
        if 'securityConcernsAny' in criteria_scores:
            security_concerns = rule_based_analysis['overall_metrics']['security_concerns']
            if security_concerns:
                criteria_scores['securityConcernsAny']['score'] = min(
                    criteria_scores['securityConcernsAny']['score'], 
                    4
                )
                concern_types = list(set(concern['type'] for concern in security_concerns))
                criteria_scores['securityConcernsAny']['feedback'] += f" Rule-based analysis found {len(security_concerns)} security concerns: {', '.join(concern_types)}."
        
        # Enhance spelling mistakes
        if 'areThereAnySpellingMistakes' in criteria_scores:
            spelling_mistakes = rule_based_analysis['overall_metrics']['spelling_mistakes']
            if spelling_mistakes:
                criteria_scores['areThereAnySpellingMistakes']['score'] = min(
                    criteria_scores['areThereAnySpellingMistakes']['score'], 
                    5
                )
                criteria_scores['areThereAnySpellingMistakes']['feedback'] += f" Rule-based analysis found {len(spelling_mistakes)} spelling mistakes."
        
        # Enhance naming convention score
        if 'isNamingConventionFollowed' in criteria_scores:
            naming_violations = rule_based_analysis['overall_metrics']['naming_violations']
            if naming_violations:
                criteria_scores['isNamingConventionFollowed']['score'] = min(
                    criteria_scores['isNamingConventionFollowed']['score'], 
                    6
                )
                criteria_scores['isNamingConventionFollowed']['feedback'] += f" Rule-based analysis found {len(naming_violations)} naming violations."
        
        # Enhance commit message score
        if 'isCommitMessageWellWritten' in criteria_scores:
            commit_analysis = rule_based_analysis.get('commit_analysis', {})
            commit_score = commit_analysis.get('quality_score', 10)
            if commit_score < 8:
                criteria_scores['isCommitMessageWellWritten']['score'] = min(
                    criteria_scores['isCommitMessageWellWritten']['score'], 
                    commit_score
                )
                issues = commit_analysis.get('issues', [])
                if issues:
                    criteria_scores['isCommitMessageWellWritten']['feedback'] += f" Issues found: {', '.join(issues[:3])}."
        
        # Add detailed rule-based findings
        combined_review['rule_based_analysis'] = rule_based_analysis
        
        # Recalculate overall score if needed
        scores = []
        weights = get_scoring_weights()
        total_weight = 0
        
        for criterion, data in criteria_scores.items():
            if isinstance(data, dict) and 'score' in data:
                weight = weights.get(criterion, 1.0)
                scores.append(data['score'] * weight)
                total_weight += weight
        
        if scores and total_weight > 0:
            combined_review['recalculated_score'] = sum(scores) / total_weight
        
        return combined_review
    
    async def post_review_to_gerrit(self, review_result: Dict[str, Any]) -> bool:
        """Post the review result back to Gerrit."""
        try:
            if not settings.auto_post_review:
                logger.info("Auto-posting disabled, skipping Gerrit posting")
                return True
            
            change_info = review_result['review_metadata']['change_info']
            change_id = change_info['change_id']
            revision_id = change_info['revision_id']
            
            # Generate summary comment
            summary_comment = self.gemini_client.generate_summary_comment(review_result)
            
            # Determine score based on overall rating
            overall_score = review_result.get('overall_score', 0)
            score = 1 if overall_score >= settings.min_review_score else -1
            
            # Prepare review data
            review_data = {
                'message': summary_comment,
                'score': score,
                'labels': {
                    'Code-Review': score
                }
            }
            
            # Post review
            success = self.gerrit_client.post_review(change_id, revision_id, review_data)
            
            if success:
                logger.info(f"Successfully posted review to Gerrit for change {change_id}")
            else:
                logger.error(f"Failed to post review to Gerrit for change {change_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error posting review to Gerrit: {e}")
            return False
