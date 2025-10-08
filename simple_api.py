"""
Simple AI Code Review API
Just takes code, sends to Gemini, returns response
"""

import os
import sys
import json
import time
import logging
import re
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    import google.generativeai as genai
    from dotenv import load_dotenv
except ImportError as e:
    print(f"❌ Missing dependencies: {e}")
    print("Run: pip install google-generativeai python-dotenv flask flask-cors")
    sys.exit(1)

# Load environment variables
load_dotenv()

# Initialize Flask
app = Flask(__name__)
CORS(app)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Gemini
gemini_model = None

# Create responses directory
RESPONSES_DIR = Path(__file__).parent / 'analysis_responses'
RESPONSES_DIR.mkdir(exist_ok=True)

def save_analysis_response(code_input: str, response_data: dict, processing_time: int):
    """Save analysis response to file for record keeping"""
    try:
        timestamp = datetime.now()
        filename = f"analysis_{timestamp.strftime('%Y%m%d_%H%M%S')}_{int(time.time())}.json"
        filepath = RESPONSES_DIR / filename
        
        # Create comprehensive record
        record = {
            'timestamp': timestamp.isoformat(),
            'input': {
                'code': code_input,
                'length': len(code_input),
                'lines': len(code_input.split('\n'))
            },
            'processing_time_ms': processing_time,
            'response': response_data,
            'metadata': {
                'model': 'gemini-2.0-flash-exp',
                'api_version': '1.0',
                'saved_by': 'AI Code Review Assistant'
            }
        }
        
        # Save to file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(record, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Analysis saved to: {filename}")
        return str(filepath)
        
    except Exception as e:
        logger.error(f"❌ Failed to save analysis: {e}")
        return None

def init_gemini():
    """Initialize Gemini AI"""
    global gemini_model
    try:
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            logger.error("❌ GEMINI_API_KEY not found in environment")
            return False
        
        genai.configure(api_key=api_key)
        gemini_model = genai.GenerativeModel('gemini-2.0-flash-exp')
        logger.info("✅ Gemini AI initialized successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to initialize Gemini: {e}")
        return False

@app.route('/api/health')
def health():
    """Simple health check"""
    return jsonify({
        'status': 'healthy',
        'gemini_ready': gemini_model is not None,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/analyze', methods=['POST'])
def analyze():
    """Analyze code with Gemini AI"""
    try:
        # Get the code and prompt from request
        data = request.get_json()
        if not data or 'code' not in data:
            return jsonify({'error': 'No code provided'}), 400
        
        code = data['code'].strip()
        if not code:
            return jsonify({'error': 'Empty code provided'}), 400
        
        # Get custom prompt and config from request
        custom_prompt = data.get('prompt', '').strip()
        config = data.get('config', {})
        
        # If prompt contains JavaScript template syntax, replace it with proper instructions
        if custom_prompt and '${JSON.stringify(' in custom_prompt:
            if config:
                # Generate proper scoring instructions based on config
                enabled_criteria = [key for key, value in config.items() if value]
                criteria_instructions = f"""
Please evaluate the following criteria and include them in your JSON response:
{', '.join(enabled_criteria)}

For each criterion, provide an object with "score" (0-10) and "comment" fields.
Example: "areCodeChangesOptimized": {{"score": 8, "comment": "Code shows good optimization practices"}}
"""
            else:
                criteria_instructions = "Please provide detailed analysis with scores for all relevant criteria."
            
            # Replace the template with proper instructions
            custom_prompt = re.sub(r'\$\{JSON\.stringify\(\s*config\s*\)\}', criteria_instructions, custom_prompt, flags=re.DOTALL)
            logger.info(f"🔄 Template replacement: Success")
            logger.info(f"📋 Enabled criteria: {len(config) if config else 0} items")
        
        if not custom_prompt:
            custom_prompt = """Analyze this code and provide a comprehensive review:

Please evaluate each criterion and provide your analysis in this JSON format:
{
    "overall_score": <number 0-10>,
    "summary": "<brief summary>",
    "detailed_feedback": "<detailed analysis>",
    "areCodeChangesOptimized": {"score": <0-10>, "comment": "<explanation>"},
    "areCodeChangesRelative": {"score": <0-10>, "comment": "<explanation>"},
    "isCodeFormatted": {"score": <0-10>, "comment": "<explanation>"},
    "isCodeWellWritten": {"score": <0-10>, "comment": "<explanation>"},
    "areCommentsWritten": {"score": <0-10>, "comment": "<explanation>"},
    "cyclomaticComplexityScore": {"score": <0-10>, "comment": "<explanation>"},
    "missingElements": {"score": <0-10>, "comment": "<explanation>"},
    "loopholes": {"score": <0-10>, "comment": "<explanation>"},
    "isCommitMessageWellWritten": {"score": <0-10>, "comment": "<explanation>"},
    "isNamingConventionFollowed": {"score": <0-10>, "comment": "<explanation>"},
    "areThereAnySpellingMistakes": {"score": <0-10>, "comment": "<explanation>"},
    "securityConcernsAny": {"score": <0-10>, "comment": "<explanation>"},
    "isCodeDuplicated": {"score": <0-10>, "comment": "<explanation>"},
    "areConstantsDefinedCentrally": {"score": <0-10>, "comment": "<explanation>"},
    "isCodeModular": {"score": <0-10>, "comment": "<explanation>"},
    "isLoggingDoneProperly": {"score": <0-10>, "comment": "<explanation>"}
}

Focus on code quality, security, performance, and best practices. Score each criterion from 0-10 where 10 is excellent."""
        
        if not gemini_model:
            return jsonify({'error': 'AI service not available'}), 503
        
        logger.info(f"Analyzing code ({len(code)} characters)")
        
        # Build prompt with custom template
        prompt = f"""
{custom_prompt}

```
{code}
```
"""
        
        # Send to Gemini
        start_time = time.time()
        response = gemini_model.generate_content(prompt)
        processing_time = int((time.time() - start_time) * 1000)
        
        if not response or not response.text:
            return jsonify({'error': 'No response from AI'}), 500
        
        # Try to parse as JSON, handle markdown code blocks
        response_text = response.text.strip()
        logger.info(f"📝 Raw response from Gemini: {response_text[:200]}...")
        
        try:
            # First try direct JSON parsing
            result = json.loads(response_text)
            logger.info("✅ Got direct JSON response")
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            try:
                # Look for ```json ... ``` blocks
                json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response_text)
                if not json_match:
                    # Try generic code blocks
                    json_match = re.search(r'```\s*(\{[\s\S]*?\})\s*```', response_text)
                if not json_match:
                    # Try to find any JSON-like structure
                    json_match = re.search(r'(\{[\s\S]*\})', response_text)
                
                if json_match:
                    json_text = json_match.group(1).strip()
                    logger.info(f"📋 Found JSON in text: {json_text[:100]}...")
                    result = json.loads(json_text)
                    logger.info("✅ Successfully parsed JSON from markdown")
                else:
                    raise json.JSONDecodeError("No JSON found", response_text, 0)
            except json.JSONDecodeError:
                # If inner parsing also fails, fall through to outer except
                raise
                    
        except json.JSONDecodeError:
            # Fallback: return as plain text with basic criteria scores
            result = {
                "overall_score": 7,
                "summary": "Analysis completed (raw format)",
                "detailed_feedback": response.text,
                "areCodeChangesOptimized": {"score": 7, "comment": "Unable to parse detailed analysis"},
                "isCodeFormatted": {"score": 7, "comment": "Unable to parse detailed analysis"},
                "isCodeWellWritten": {"score": 7, "comment": "Unable to parse detailed analysis"}
            }
            logger.info("⚠️ Got plain text response, wrapped in JSON")
        
        # Add metadata
        result['processing_time_ms'] = processing_time
        result['analysis_timestamp'] = datetime.now().isoformat()
        result['input_length'] = len(code)
        
        # Save the analysis response
        saved_file = save_analysis_response(code, result, processing_time)
        if saved_file:
            result['saved_to'] = saved_file
        
        logger.info(f"✅ Analysis completed in {processing_time}ms")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"❌ Error during analysis: {e}")
        return jsonify({
            'error': 'Analysis failed', 
            'details': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/saved-analyses')
def get_saved_analyses():
    """Get list of saved analysis files"""
    try:
        analyses = []
        for file_path in RESPONSES_DIR.glob('analysis_*.json'):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    analyses.append({
                        'filename': file_path.name,
                        'timestamp': data.get('timestamp'),
                        'input_length': data.get('input', {}).get('length', 0),
                        'input_lines': data.get('input', {}).get('lines', 0),
                        'processing_time_ms': data.get('processing_time_ms', 0),
                        'overall_score': data.get('response', {}).get('overall_score'),
                        'summary': data.get('response', {}).get('summary', '')[:100] + '...' if data.get('response', {}).get('summary', '') else ''
                    })
            except Exception as e:
                logger.warning(f"Failed to read {file_path}: {e}")
                continue
        
        # Sort by timestamp (newest first)
        analyses.sort(key=lambda x: x['timestamp'] or '', reverse=True)
        
        return jsonify({
            'total_analyses': len(analyses),
            'analyses': analyses[:50]  # Return last 50 analyses
        })
        
    except Exception as e:
        logger.error(f"Error getting saved analyses: {e}")
        return jsonify({'error': 'Failed to get saved analyses'}), 500

@app.route('/api/saved-analyses/<filename>')
def get_saved_analysis(filename):
    """Get specific saved analysis"""
    try:
        file_path = RESPONSES_DIR / filename
        if not file_path.exists():
            return jsonify({'error': 'Analysis not found'}), 404
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return jsonify(data)
        
    except Exception as e:
        logger.error(f"Error getting saved analysis: {e}")
        return jsonify({'error': 'Failed to get saved analysis'}), 500

if __name__ == '__main__':
    print("""
🤖 Simple AI Code Review API
═══════════════════════════════════════
🚀 Gemini AI + Flask + React
📡 API Server for Frontend
═══════════════════════════════════════
""")
    
    # Initialize Gemini
    if not init_gemini():
        print("⚠️ Gemini not initialized - check your GEMINI_API_KEY")
        print("💡 Set it in your .env file: GEMINI_API_KEY=your_key_here")
    
    # Start server
    port = 5001
    print(f"🌐 Starting API server on http://localhost:{port}")
    print(f"📋 Endpoints:")
    print(f"   GET  /api/health  - Health check")
    print(f"   POST /api/analyze - Analyze code")
    print(f"🔗 React app should connect to this API")
    print("=" * 40)
    
    app.run(
        host='127.0.0.1',
        port=port,
        debug=True
    )
