"""
AI Code Review Assistant - API Only Version
Provides REST API endpoints for code analysis
"""

import os
import sys
import time
import json
import traceback
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

from flask import Flask, request, jsonify
from flask_cors import CORS
import logging

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config import Settings
from llm_client import GeminiClient, ReviewAnalyzer
from review_evaluator import ReviewEvaluator
from utils import setup_logger

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Setup logging
logger = setup_logger(__name__)
logging.basicConfig(level=logging.INFO)

# Global instances
settings = Settings()
gemini_client = GeminiClient()
review_analyzer = ReviewAnalyzer(gemini_client)

def parse_git_diff(diff_text: str) -> Dict[str, Any]:
    """
    Parse git diff format and extract structured information
    """
    try:
        lines = diff_text.strip().split('\n')
        files = []
        current_file = None
        current_hunk = None
        
        for line in lines:
            if line.startswith('diff --git'):
                # New file
                if current_file:
                    files.append(current_file)
                
                parts = line.split()
                if len(parts) >= 4:
                    file_path = parts[3][2:]  # Remove 'b/' prefix
                    current_file = {
                        'file_path': file_path,
                        'change_type': 'modified',
                        'lines_added': 0,
                        'lines_removed': 0,
                        'hunks': []
                    }
                    
            elif line.startswith('new file mode'):
                if current_file:
                    current_file['change_type'] = 'added'
                    
            elif line.startswith('deleted file mode'):
                if current_file:
                    current_file['change_type'] = 'deleted'
                    
            elif line.startswith('@@'):
                # New hunk
                if current_file:
                    # Parse hunk header: @@ -old_start,old_lines +new_start,new_lines @@
                    parts = line.split()
                    if len(parts) >= 3:
                        old_range = parts[1][1:]  # Remove '-' prefix
                        new_range = parts[2][1:]  # Remove '+' prefix
                        
                        old_start, old_lines = map(int, old_range.split(',')) if ',' in old_range else (int(old_range), 1)
                        new_start, new_lines = map(int, new_range.split(',')) if ',' in new_range else (int(new_range), 1)
                        
                        current_hunk = {
                            'old_start': old_start,
                            'old_lines': old_lines,
                            'new_start': new_start,
                            'new_lines': new_lines,
                            'lines': []
                        }
                        current_file['hunks'].append(current_hunk)
                        
            elif current_hunk and (line.startswith(' ') or line.startswith('+') or line.startswith('-')):
                # Diff line
                line_type = 'context' if line.startswith(' ') else ('added' if line.startswith('+') else 'removed')
                content = line[1:]  # Remove prefix
                
                diff_line = {
                    'type': line_type,
                    'content': content
                }
                
                if line_type == 'added':
                    current_file['lines_added'] += 1
                elif line_type == 'removed':
                    current_file['lines_removed'] += 1
                    
                current_hunk['lines'].append(diff_line)
        
        # Add last file
        if current_file:
            files.append(current_file)
            
        return {
            'format': 'git-diff',
            'files': files,
            'total_files': len(files),
            'total_lines_added': sum(f['lines_added'] for f in files),
            'total_lines_removed': sum(f['lines_removed'] for f in files)
        }
        
    except Exception as e:
        logger.error(f"Error parsing git diff: {e}")
        return {
            'format': 'raw-text',
            'content': diff_text,
            'error': str(e)
        }

def detect_programming_language(code: str) -> Optional[str]:
    """
    Detect programming language from code content
    """
    # Simple heuristics for language detection
    if 'def ' in code and 'import ' in code:
        return 'python'
    elif 'function ' in code and '{' in code:
        return 'javascript'
    elif 'public class ' in code or 'private ' in code:
        return 'java'
    elif '#include' in code and 'int main' in code:
        return 'cpp'
    elif 'SELECT ' in code.upper() and 'FROM ' in code.upper():
        return 'sql'
    elif '<html' in code.lower() or '<div' in code.lower():
        return 'html'
    elif 'const ' in code and '=>' in code:
        return 'typescript'
    
    return None

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0',
        'services': {
            'gemini_api': 'connected' if gemini_client else 'disconnected',
            'review_analyzer': 'ready' if review_analyzer else 'not_ready'
        }
    })

@app.route('/api/analyze', methods=['POST'])
def analyze_code():
    """
    Analyze code or git diff and return comprehensive feedback
    """
    try:
        start_time = time.time()
        
        # Get request data
        data = request.get_json()
        if not data or 'code' not in data:
            return jsonify({'error': 'No code provided'}), 400
            
        code = data['code'].strip()
        if not code:
            return jsonify({'error': 'Empty code provided'}), 400
            
        logger.info(f"Analyzing code of length {len(code)} characters")
        
        # Parse input format
        parsed_data = parse_git_diff(code)
        is_git_diff = parsed_data['format'] == 'git-diff'
        
        # Detect language if not git diff
        language = None
        if not is_git_diff:
            language = detect_programming_language(code)
            
        # Prepare context for analysis
        context = {
            'format': parsed_data['format'],
            'language': language,
            'is_git_diff': is_git_diff,
            'analysis_timestamp': datetime.now().isoformat()
        }
        
        if is_git_diff:
            context.update({
                'files_changed': parsed_data['total_files'],
                'lines_added': parsed_data['total_lines_added'],
                'lines_removed': parsed_data['total_lines_removed']
            })
        
        # Perform AI analysis
        logger.info("Starting AI analysis...")
        
        # Prepare review context for the analyzer
        review_context = {
            'code': code,
            'context': context,
            'metadata': {
                'timestamp': context['analysis_timestamp'],
                'format': parsed_data['format'],
                'language': language
            }
        }
        
        analysis_result = review_analyzer.analyze_change(review_context)
        
        if not analysis_result:
            return jsonify({
                'error': 'Analysis failed - no result returned',
                'timestamp': datetime.now().isoformat()
            }), 500
        
        # Add metadata
        processing_time = int((time.time() - start_time) * 1000)
        analysis_result.update({
            'analysis_timestamp': context['analysis_timestamp'],
            'processing_time_ms': processing_time,
            'input_format': parsed_data['format'],
            'detected_language': language,
            'input_stats': {
                'total_lines': len(code.split('\n')),
                'total_characters': len(code),
                'files_analyzed': parsed_data.get('total_files', 1)
            }
        })
        
        if is_git_diff:
            analysis_result['git_diff_info'] = {
                'files_changed': parsed_data['total_files'],
                'lines_added': parsed_data['total_lines_added'],
                'lines_removed': parsed_data['total_lines_removed'],
                'files': parsed_data['files']
            }
        
        logger.info(f"Analysis completed in {processing_time}ms")
        return jsonify(analysis_result)
        
    except Exception as e:
        logger.error(f"Error analyzing code: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'error': 'Analysis failed',
            'details': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/examples')
def get_examples():
    """Get example git diffs for testing"""
    examples = {
        'python_function': {
            'title': 'Python Function Improvement',
            'description': 'Adding null checks and error handling',
            'code': '''diff --git a/src/utils.py b/src/utils.py
index 1234567..abcdefg 100644
--- a/src/utils.py
+++ b/src/utils.py
@@ -10,7 +10,10 @@ def calculate_total(items):
     total = 0
     for item in items:
-        total += item.price
+        if item.price is not None:
+            total += item.price
+        else:
+            print(f"Warning: Item {item.name} has no price")
     return total'''
        },
        'react_component': {
            'title': 'React Component Enhancement',
            'description': 'Adding props validation and default values',
            'code': '''diff --git a/components/UserProfile.tsx b/components/UserProfile.tsx
index 1234567..abcdefg 100644
--- a/components/UserProfile.tsx
+++ b/components/UserProfile.tsx
@@ -15,8 +15,12 @@ const UserProfile: React.FC<Props> = ({ user }) => {
   return (
     <div className="user-profile">
-      <h2>{user.name}</h2>
-      <p>{user.email}</p>
+      <h2>{user.name || 'Anonymous User'}</h2>
+      <p>{user.email || 'No email provided'}</p>
+      {user.avatar && (
+        <img src={user.avatar} alt="User avatar" />
+      )}
+      <div>Last seen: {user.lastSeen || 'Never'}</div>
     </div>
   );
 };'''
        },
        'sql_optimization': {
            'title': 'SQL Query Optimization',
            'description': 'Improving query performance with proper joins and filters',
            'code': '''diff --git a/database/queries.sql b/database/queries.sql
index 1234567..abcdefg 100644
--- a/database/queries.sql
+++ b/database/queries.sql
@@ -5,10 +5,12 @@
 -- Get user orders with product details
-SELECT u.name, o.order_date, p.product_name, oi.quantity
+SELECT u.name, o.order_date, p.product_name, oi.quantity, p.category
 FROM users u
-JOIN orders o ON u.id = o.user_id
-JOIN order_items oi ON o.id = oi.order_id
-JOIN products p ON oi.product_id = p.id
-ORDER BY o.order_date DESC;
+  INNER JOIN orders o ON u.id = o.user_id
+  INNER JOIN order_items oi ON o.id = oi.order_id
+  INNER JOIN products p ON oi.product_id = p.id
+WHERE o.order_date >= DATE_SUB(NOW(), INTERVAL 30 DAY)
+  AND u.status = 'active'
+ORDER BY o.order_date DESC
+LIMIT 100;'''
        }
    }
    
    return jsonify(examples)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3001))
    host = os.environ.get('HOST', '127.0.0.1')
    
    logger.info(f"Starting AI Code Review API on http://{host}:{port}")
    print(f"\n🚀 AI Code Review API starting on http://{host}:{port}")
    print("📝 API Endpoints:")
    print(f"  - Health Check: http://{host}:{port}/api/health")
    print(f"  - Analyze Code: http://{host}:{port}/api/analyze (POST)")
    print(f"  - Examples: http://{host}:{port}/api/examples")
    print("💡 Use with React frontend in development mode")
    
    app.run(
        host=host,
        port=port,
        debug=True,
        threaded=True
    )
