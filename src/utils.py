"""
Utility functions for the automated code review system.
"""
import logging
import sys
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import re
import hashlib
import json

from config import settings


def setup_logger(name: str, level: str = None) -> logging.Logger:
    """Set up logger with proper formatting and handlers."""
    logger = logging.getLogger(name)
    
    if logger.handlers:
        return logger  # Logger already configured
    
    log_level = getattr(logging, (level or settings.log_level).upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)
    
    # File handler
    if settings.log_file:
        try:
            os.makedirs(os.path.dirname(settings.log_file), exist_ok=True)
            file_handler = logging.FileHandler(settings.log_file)
            file_handler.setLevel(log_level)
            file_handler.setFormatter(detailed_formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"Could not create file handler: {e}")
    
    return logger


def parse_diff(diff_text: str) -> Dict[str, Any]:
    """Parse diff text and extract meaningful information."""
    if not diff_text:
        return {
            'added_lines': 0,
            'removed_lines': 0,
            'modified_lines': 0,
            'added_content': [],
            'removed_content': [],
            'complexity_indicators': []
        }
    
    lines = diff_text.split('\n')
    added_lines = []
    removed_lines = []
    added_count = 0
    removed_count = 0
    
    # Complexity indicators
    complexity_patterns = [
        r'\bif\b', r'\belse\b', r'\belif\b', r'\bwhile\b', r'\bfor\b',
        r'\btry\b', r'\bcatch\b', r'\bexcept\b', r'\bswitch\b', r'\bcase\b'
    ]
    
    complexity_indicators = []
    
    for line in lines:
        if line.startswith('+') and not line.startswith('+++'):
            added_lines.append(line[1:].strip())
            added_count += 1
            
            # Check for complexity
            for pattern in complexity_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    complexity_indicators.append(line.strip())
                    
        elif line.startswith('-') and not line.startswith('---'):
            removed_lines.append(line[1:].strip())
            removed_count += 1
    
    return {
        'added_lines': added_count,
        'removed_lines': removed_count,
        'modified_lines': added_count + removed_count,
        'added_content': added_lines,
        'removed_content': removed_lines,
        'complexity_indicators': complexity_indicators
    }


def calculate_cyclomatic_complexity(code_text: str) -> int:
    """Calculate approximate cyclomatic complexity of code."""
    if not code_text:
        return 1
    
    # Patterns that increase complexity
    complexity_patterns = [
        r'\bif\b',
        r'\belse\s+if\b',
        r'\belif\b',
        r'\bwhile\b',
        r'\bfor\b',
        r'\btry\b',
        r'\bcatch\b',
        r'\bexcept\b',
        r'\bswitch\b',
        r'\bcase\b',
        r'\b\?\s*.*\s*:\s*.*\b',  # Ternary operator
        r'\b&&\b',  # Logical AND
        r'\b\|\|\b',  # Logical OR
    ]
    
    complexity = 1  # Base complexity
    
    for pattern in complexity_patterns:
        matches = re.findall(pattern, code_text, re.IGNORECASE | re.MULTILINE)
        complexity += len(matches)
    
    return complexity


def detect_code_smells(code_text: str, file_path: str = "") -> List[Dict[str, str]]:
    """Detect common code smells."""
    smells = []
    
    if not code_text:
        return smells
    
    lines = code_text.split('\n')
    
    # Long method/function detection
    function_patterns = [
        r'def\s+\w+\s*\(',  # Python
        r'function\s+\w+\s*\(',  # JavaScript
        r'(public|private|protected)?\s*(static)?\s*\w+\s+\w+\s*\(',  # Java/C#
    ]
    
    in_function = False
    function_line_count = 0
    function_start = 0
    
    for i, line in enumerate(lines):
        # Check if we're starting a function
        for pattern in function_patterns:
            if re.search(pattern, line):
                in_function = True
                function_start = i
                function_line_count = 0
                break
        
        if in_function:
            function_line_count += 1
            
            # Simple heuristic: function ends when indentation returns to original level
            # or we hit another function definition
            if function_line_count > 50:  # Long method threshold
                smells.append({
                    'type': 'Long Method',
                    'line': str(function_start + 1),
                    'description': f'Method/function is {function_line_count} lines long, consider breaking it down'
                })
                in_function = False
    
    # Magic numbers detection
    magic_number_pattern = r'\b(?<![\w.])\d{2,}\b(?![\w.])'
    for i, line in enumerate(lines):
        if re.search(magic_number_pattern, line):
            smells.append({
                'type': 'Magic Number',
                'line': str(i + 1),
                'description': 'Consider extracting magic numbers into named constants'
            })
    
    # Duplicate code detection (simple)
    line_hashes = {}
    for i, line in enumerate(lines):
        stripped = line.strip()
        if len(stripped) > 10:  # Ignore short lines
            line_hash = hashlib.md5(stripped.encode()).hexdigest()
            if line_hash in line_hashes:
                smells.append({
                    'type': 'Duplicate Code',
                    'line': str(i + 1),
                    'description': f'Similar to line {line_hashes[line_hash] + 1}'
                })
            else:
                line_hashes[line_hash] = i
    
    return smells


def extract_security_concerns(code_text: str) -> List[Dict[str, str]]:
    """Extract potential security concerns from code."""
    concerns = []
    
    if not code_text:
        return concerns
    
    # Security patterns to look for
    security_patterns = [
        (r'eval\s*\(', 'Code Injection', 'Use of eval() can lead to code injection'),
        (r'exec\s*\(', 'Code Injection', 'Use of exec() can lead to code injection'),
        (r'system\s*\(', 'Command Injection', 'Direct system calls can be dangerous'),
        (r'shell_exec\s*\(', 'Command Injection', 'Shell execution can be dangerous'),
        (r'password\s*=\s*["\'][^"\']*["\']', 'Hardcoded Credentials', 'Hardcoded password detected'),
        (r'api_key\s*=\s*["\'][^"\']*["\']', 'Hardcoded Credentials', 'Hardcoded API key detected'),
        (r'secret\s*=\s*["\'][^"\']*["\']', 'Hardcoded Credentials', 'Hardcoded secret detected'),
        (r'md5\s*\(', 'Weak Cryptography', 'MD5 is cryptographically broken'),
        (r'sha1\s*\(', 'Weak Cryptography', 'SHA1 is deprecated for security purposes'),
        (r'http://', 'Insecure Communication', 'Use HTTPS instead of HTTP'),
        (r'INSERT\s+INTO.*VALUES.*\+', 'SQL Injection', 'Potential SQL injection vulnerability'),
        (r'SELECT.*FROM.*WHERE.*\+', 'SQL Injection', 'Potential SQL injection vulnerability'),
    ]
    
    lines = code_text.split('\n')
    
    for i, line in enumerate(lines):
        for pattern, concern_type, description in security_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                concerns.append({
                    'type': concern_type,
                    'line': str(i + 1),
                    'description': description,
                    'code_snippet': line.strip()
                })
    
    return concerns


def validate_naming_conventions(code_text: str, language: str = "python") -> List[Dict[str, str]]:
    """Validate naming conventions based on language."""
    violations = []
    
    if not code_text:
        return violations
    
    lines = code_text.split('\n')
    
    if language.lower() == "python":
        # Python naming conventions
        patterns = [
            (r'def\s+([A-Z][a-zA-Z0-9_]*)\s*\(', 'Function names should be lowercase with underscores'),
            (r'class\s+([a-z][a-zA-Z0-9_]*)', 'Class names should use PascalCase'),
            (r'([A-Z][A-Z_]+)\s*=', 'Constants should be UPPERCASE_WITH_UNDERSCORES'),
        ]
    elif language.lower() in ["javascript", "typescript"]:
        # JavaScript/TypeScript naming conventions
        patterns = [
            (r'function\s+([A-Z][a-zA-Z0-9]*)\s*\(', 'Function names should be camelCase'),
            (r'class\s+([a-z][a-zA-Z0-9]*)', 'Class names should use PascalCase'),
            (r'const\s+([a-z_][a-zA-Z0-9_]*)\s*=', 'Constants should be UPPERCASE_WITH_UNDERSCORES'),
        ]
    else:
        return violations  # Unsupported language
    
    for i, line in enumerate(lines):
        for pattern, message in patterns:
            matches = re.findall(pattern, line)
            if matches:
                violations.append({
                    'type': 'Naming Convention',
                    'line': str(i + 1),
                    'description': message,
                    'violating_name': matches[0] if matches else 'unknown'
                })
    
    return violations


def check_spelling(text: str) -> List[Dict[str, str]]:
    """Basic spelling check for comments and strings."""
    # This is a simple implementation. In production, you might want to use
    # a proper spell checking library like pyspellchecker
    
    common_misspellings = {
        'recieve': 'receive',
        'occured': 'occurred',
        'seperate': 'separate',
        'definately': 'definitely',
        'befor': 'before',
        'afte': 'after',
        'lenght': 'length',
        'widht': 'width',
        'heigth': 'height',
        'paramater': 'parameter',
        'paramters': 'parameters',
        'retrun': 'return',
        'calback': 'callback',
        'sucessful': 'successful',
        'sucessfully': 'successfully',
    }
    
    mistakes = []
    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    
    for word in words:
        if word in common_misspellings:
            mistakes.append({
                'type': 'Spelling Mistake',
                'word': word,
                'suggestion': common_misspellings[word],
                'description': f'"{word}" should be "{common_misspellings[word]}"'
            })
    
    return mistakes


def format_timestamp(dt: datetime = None) -> str:
    """Format timestamp for logging and reports."""
    if dt is None:
        dt = datetime.now()
    return dt.strftime('%Y-%m-%d %H:%M:%S UTC')


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage."""
    # Remove or replace invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip(' .')
    # Limit length
    if len(sanitized) > 200:
        sanitized = sanitized[:200]
    return sanitized


def calculate_file_metrics(file_content: str) -> Dict[str, Any]:
    """Calculate various metrics for a file."""
    if not file_content:
        return {
            'lines_of_code': 0,
            'blank_lines': 0,
            'comment_lines': 0,
            'total_lines': 0,
            'complexity': 1
        }
    
    lines = file_content.split('\n')
    total_lines = len(lines)
    blank_lines = 0
    comment_lines = 0
    code_lines = 0
    
    comment_patterns = [
        r'^\s*#',  # Python, Shell
        r'^\s*//',  # JavaScript, Java, C++
        r'^\s*/\*',  # C-style block comments
        r'^\s*\*',  # C-style block comments continuation
        r'^\s*\*/',  # C-style block comments end
    ]
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            blank_lines += 1
        elif any(re.match(pattern, line) for pattern in comment_patterns):
            comment_lines += 1
        else:
            code_lines += 1
    
    complexity = calculate_cyclomatic_complexity(file_content)
    
    return {
        'lines_of_code': code_lines,
        'blank_lines': blank_lines,
        'comment_lines': comment_lines,
        'total_lines': total_lines,
        'complexity': complexity,
        'comment_ratio': comment_lines / max(code_lines, 1)
    }


def generate_review_id(change_id: str, revision_id: str) -> str:
    """Generate unique review ID."""
    combined = f"{change_id}_{revision_id}_{datetime.now().isoformat()}"
    return hashlib.sha256(combined.encode()).hexdigest()[:16]


def save_review_result(review_id: str, review_data: Dict[str, Any], output_dir: str = "logs") -> bool:
    """Save review result to file."""
    try:
        os.makedirs(output_dir, exist_ok=True)
        filename = f"review_{review_id}.json"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(review_data, f, indent=2, ensure_ascii=False)
        
        return True
    except Exception as e:
        logger = setup_logger(__name__)
        logger.error(f"Failed to save review result: {e}")
        return False


def load_review_result(review_id: str, output_dir: str = "logs") -> Optional[Dict[str, Any]]:
    """Load review result from file."""
    try:
        filename = f"review_{review_id}.json"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger = setup_logger(__name__)
        logger.error(f"Failed to load review result: {e}")
        return None
