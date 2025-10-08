"""
Simple Flask API server for AI Code Review
Serves only API endpoints for the React frontend
"""

import os
import sys
import json
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from flask import Flask, request, jsonify
from flask_cors import CORS

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from config import Settings
    from llm_client import GeminiClient
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please make sure all dependencies are installed: pip install -r requirements.txt")
    sys.exit(1)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances
settings = Settings()
gemini_client = None

def initialize_gemini():
    """Initialize Gemini client"""
    global gemini_client
    try:
        gemini_client = GeminiClient()
        logger.info("✅ Gemini client initialized successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to initialize Gemini client: {e}")
        return False

def analyze_code_simple(code: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simple code analysis using Gemini AI
    """
    try:
        # Build a simple prompt for analysis
        prompt = f"""
As an expert code reviewer, analyze the following code and provide comprehensive feedback.

Code to analyze:
```
{code}
```

Context: {json.dumps(context, indent=2)}

Please provide your analysis in the following JSON format:
{{
    "overall_score": <number between 0-10>,
    "summary": "<brief summary of the code quality>",
    "criteria_results": [
        {{
            "criterion": "Code Quality",
            "score": <0-10>,
            "feedback": "<detailed feedback>",
            "suggestions": ["<suggestion1>", "<suggestion2>"],
            "severity": "<low|medium|high|critical>"
        }},
        {{
            "criterion": "Security",
            "score": <0-10>,
            "feedback": "<detailed feedback>",
            "suggestions": ["<suggestion1>", "<suggestion2>"],
            "severity": "<low|medium|high|critical>"
        }},
        {{
            "criterion": "Performance",
            "score": <0-10>,
            "feedback": "<detailed feedback>",
            "suggestions": ["<suggestion1>", "<suggestion2>"],
            "severity": "<low|medium|high|critical>"
        }},
        {{
            "criterion": "Maintainability",
            "score": <0-10>,
            "feedback": "<detailed feedback>",
            "suggestions": ["<suggestion1>", "<suggestion2>"],
            "severity": "<low|medium|high|critical>"
        }},
        {{
            "criterion": "Readability",
            "score": <0-10>,
            "feedback": "<detailed feedback>",
            "suggestions": ["<suggestion1>", "<suggestion2>"],
            "severity": "<low|medium|high|critical>"
        }}
    ],
    "recommendations": ["<recommendation1>", "<recommendation2>"],
    "positive_aspects": ["<positive1>", "<positive2>"],
    "areas_for_improvement": ["<improvement1>", "<improvement2>"],
    "code_quality_metrics": {{
        "complexity": <0-10>,
        "maintainability": <0-10>,
        "readability": <0-10>,
        "testability": <0-10>
    }},
    "detected_patterns": ["<pattern1>", "<pattern2>"],
    "potential_issues": ["<issue1>", "<issue2>"]
}}

Please ensure the JSON is valid and complete.
"""
        
        response = gemini_client.model.generate_content(prompt)
        
        if not response or not response.text:
            logger.error("Empty response from Gemini")
            return create_error_response("Empty response from AI")
        
        # Try to parse the JSON response
        try:
            result = json.loads(response.text)
            logger.info("Successfully parsed Gemini response")
            return result
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response as JSON: {e}")
            # Return a fallback response
            return create_fallback_response(code, response.text)
            
    except Exception as e:
        logger.error(f"Error during analysis: {e}")
        return create_error_response(str(e))

def create_error_response(error_msg: str) -> Dict[str, Any]:
    """Create a structured error response"""
    return {
        "overall_score": 0,
        "summary": f"Analysis failed: {error_msg}",
        "criteria_results": [],
        "recommendations": ["Please try again or check your input"],
        "positive_aspects": [],
        "areas_for_improvement": ["Fix the analysis error"],
        "code_quality_metrics": {
            "complexity": 0,
            "maintainability": 0,
            "readability": 0,
            "testability": 0
        },
        "detected_patterns": [],
        "potential_issues": [f"Analysis error: {error_msg}"]
    }

def create_fallback_response(code: str, raw_response: str) -> Dict[str, Any]:
    """Create a fallback response when JSON parsing fails"""
    return {
        "overall_score": 5,
        "summary": "Analysis completed but response format was invalid. Raw analysis provided.",
        "criteria_results": [
            {
                "criterion": "AI Analysis",
                "score": 5,
                "feedback": raw_response[:500] + "..." if len(raw_response) > 500 else raw_response,
                "suggestions": ["Review the raw analysis feedback"],
                "severity": "medium"
            }
        ],
        "recommendations": ["Please try the analysis again"],
        "positive_aspects": ["Code was successfully processed"],
        "areas_for_improvement": ["AI response formatting needs improvement"],
        "code_quality_metrics": {
            "complexity": 5,
            "maintainability": 5,
            "readability": 5,
            "testability": 5
        },
        "detected_patterns": ["Code analysis performed"],
        "potential_issues": ["Response parsing failed"]
    }

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0',
        'services': {
            'gemini_api': 'connected' if gemini_client else 'disconnected',
            'flask_server': 'running'
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
        
        if not gemini_client:
            return jsonify({'error': 'AI service not available'}), 503
        
        # Prepare context
        context = {
            'format': 'git-diff' if 'diff --git' in code else 'raw-code',
            'analysis_timestamp': datetime.now().isoformat(),
            'request_id': str(time.time())
        }
        
        # Perform analysis
        logger.info("Starting AI analysis...")
        analysis_result = analyze_code_simple(code, context)
        
        # Add metadata
        processing_time = int((time.time() - start_time) * 1000)
        analysis_result.update({
            'analysis_timestamp': context['analysis_timestamp'],
            'processing_time_ms': processing_time,
            'input_format': context['format'],
            'input_stats': {
                'total_lines': len(code.split('\n')),
                'total_characters': len(code)
            }
        })
        
        logger.info(f"Analysis completed in {processing_time}ms")
        return jsonify(analysis_result)
        
    except Exception as e:
        logger.error(f"Error analyzing code: {e}")
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
        }
    }
    
    return jsonify(examples)

if __name__ == '__main__':
    print("""
🤖 AI Code Review Assistant - API Server
═══════════════════════════════════════════════
🚀 Starting Flask API server for React frontend
📡 API endpoints available at http://localhost:5001
═══════════════════════════════════════════════
""")
    
    # Initialize Gemini client
    if not initialize_gemini():
        print("⚠️  Warning: Gemini client not initialized. Some features may not work.")
        print("💡 Make sure your GEMINI_API_KEY is set in the .env file")
    
    # Start the Flask server
    port = int(os.environ.get('PORT', 5001))
    host = os.environ.get('HOST', '127.0.0.1')
    
    print(f"🌐 API server starting on http://{host}:{port}")
    print(f"📋 Available endpoints:")
    print(f"   GET  http://{host}:{port}/api/health")
    print(f"   POST http://{host}:{port}/api/analyze")
    print(f"   GET  http://{host}:{port}/api/examples")
    print("🔗 React frontend should connect to this API")
    print("=" * 50)
    
    app.run(
        host=host,
        port=port,
        debug=True,
        threaded=True
    )
