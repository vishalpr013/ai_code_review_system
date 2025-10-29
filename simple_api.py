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

def transform_ai_response_to_frontend_format(ai_response: dict, config: dict) -> dict:
    """Transform AI response to match frontend expected format"""
    
    # Criterion name mapping for better display
    criteria_names = {
        'areCodeChangesOptimized': 'Code Optimization',
        'areCodeChangesRelative': 'Code Relevance',
        'isCodeFormatted': 'Code Formatting',
        'isCodeWellWritten': 'Code Quality',
        'areCommentsWritten': 'Documentation',
        'cyclomaticComplexityScore': 'Complexity Management',
        'missingElements': 'Completeness',
        'loopholes': 'Bug Prevention',
        'isCommitMessageWellWritten': 'Commit Message Quality',
        'isNamingConventionFollowed': 'Naming Conventions',
        'areThereAnySpellingMistakes': 'Spelling Accuracy',
        'securityConcernsAny': 'Security Analysis',
        'isCodeDuplicated': 'Code Duplication',
        'areConstantsDefinedCentrally': 'Constants Management',
        'isCodeModular': 'Modularity',
        'isLoggingDoneProperly': 'Logging Practices'
    }
    
    # Get enabled criteria from config
    enabled_criteria = set(key for key, value in config.items() if value) if config else set()
    
    # Look for criteria in different possible locations in the AI response
    criteria_data = {}
    nested_key = None
    
    # Check if criteria are nested under a special key (like we saw in the response)
    for key, value in ai_response.items():
        if isinstance(value, dict) and any(criterion in value for criterion in criteria_names.keys()):
            criteria_data = value
            nested_key = key
            logger.info(f"🔍 Found criteria nested under key: '{key}'")
            break
    
    # If no nested structure found, look at root level
    if not criteria_data:
        criteria_data = ai_response
        logger.info(f"🔍 Using root level for criteria extraction")
    
    # Build criteria results array for frontend
    criteria_results = []
    areas_for_improvement = []
    positive_aspects = []
    recommendations = []
    potential_issues = []
    
    # Calculate weighted overall score and collect criteria
    weights = {
    'securityConcernsAny': 3.0,
    'loopholes': 3.0,
    'isCodeWellWritten': 2.5,
    'isCodeFormatted': 1.0,
    'areCommentsWritten': 1.0,
    'cyclomaticComplexityScore': 2.0,
    'isNamingConventionFollowed': 1.5,
    'areCodeChangesOptimized': 2.0,
    'isCodeModular': 2.0,
    'isLoggingDoneProperly': 1.5,
    'areConstantsDefinedCentrally': 1.0,
    'isCodeDuplicated': 1.5,
    'missingElements': 2.0,
    'areCodeChangesRelative': 1.5,
    'isCommitMessageWellWritten': 1.0,
    'areThereAnySpellingMistakes': 0.5
}

    
    weighted_sum = 0
    total_weight = 0
    
    for key, criterion_result in criteria_data.items():
        if key in criteria_names and isinstance(criterion_result, dict) and 'score' in criterion_result:
            # Only include if it's in enabled criteria (if config provided) or if no config filtering
            if not enabled_criteria or key in enabled_criteria:
                score = float(criterion_result.get('score', 0))
                comment = criterion_result.get('comment', '')
                
                # Determine severity based on score
                if score >= 8:
                    severity = 'low'
                elif score >= 6:
                    severity = 'medium'
                elif score >= 4:
                    severity = 'high'
                else:
                    severity = 'critical'
                
                criteria_result = {
                    'criterion': criteria_names[key],
                    'score': score,
                    'feedback': comment,
                    'suggestions': [],  # AI doesn't provide separate suggestions, could extract from comment
                    'severity': severity
                }
                
                criteria_results.append(criteria_result)
                
                # Collect feedback for different categories
                if score < 6:
                    areas_for_improvement.append(f"{criteria_names[key]}: {comment}")
                    if score < 4:
                        potential_issues.append(f"Critical issue in {criteria_names[key]}: {comment}")
                else:
                    positive_aspects.append(f"{criteria_names[key]}: {comment}")
                
                # Add to weighted calculation
                if key in weights:
                    weight = weights[key]
                    weighted_sum += score * weight
                    total_weight += weight
    
    # Get AI's overall score directly from the response
    # Try multiple locations: root level, nested in criteria_data, or in the nested structure
    ai_overall_score = ai_response.get('overall_score')
    
    # If not found at root and we have a nested structure, check there too
    if not ai_overall_score and nested_key:
        ai_overall_score = ai_response.get(nested_key, {}).get('overall_score')
        if ai_overall_score:
            logger.info(f"✅ Found overall_score in nested structure under '{nested_key}'")
    
    # Also check in criteria_data itself
    if not ai_overall_score and isinstance(criteria_data, dict):
        ai_overall_score = criteria_data.get('overall_score')
        if ai_overall_score:
            logger.info(f"✅ Found overall_score in criteria_data")
    
    # Calculate weighted average score from individual criteria
    weighted_overall_score = 0
    if total_weight > 0:
        weighted_overall_score = round(weighted_sum / total_weight, 1)
    
    # If AI didn't provide a score, log warning and try to use weighted as fallback
    if not ai_overall_score:
        logger.warning(f"⚠️ AI did not provide overall_score in response! Using weighted calculation as fallback.")
        logger.warning(f"📋 AI response keys: {list(ai_response.keys())}")
        logger.warning(f"📋 Criteria data keys: {list(criteria_data.keys()) if isinstance(criteria_data, dict) else 'Not a dict'}")
        ai_overall_score = weighted_overall_score if weighted_overall_score > 0 else 0
    else:
        logger.info(f"✅ Using AI's overall_score: {ai_overall_score}")

    # Build response in BOTH formats for compatibility
    # New format for advanced frontend
    new_format_response = {
        'overall_score': float(ai_overall_score),  # AI's judgment score
        'weighted_overall_score': float(weighted_overall_score),  # Calculated weighted average
        'summary': ai_response.get('summary', ai_response.get('detailed_feedback', 'Code analysis completed')),
        'criteria_results': criteria_results,
        'recommendations': recommendations or ['Continue following current best practices'],
        'positive_aspects': positive_aspects,
        'areas_for_improvement': areas_for_improvement,
        'code_quality_metrics': {
            'complexity': min(10, len([c for c in criteria_results if 'complexity' in c['criterion'].lower()])) or 7,
            'maintainability': ai_overall_score,
            'readability': next((c['score'] for c in criteria_results if 'format' in c['criterion'].lower()), ai_overall_score),
            'testability': ai_overall_score
        },
        'detected_patterns': [],
        'potential_issues': potential_issues,
        'analysis_timestamp': ai_response.get('analysis_timestamp', datetime.now().isoformat()),
        'processing_time_ms': ai_response.get('processing_time_ms', 0)
    }
    
    # Old format for simple frontend compatibility - add individual criteria as direct properties
    reverse_mapping = {v: k for k, v in criteria_names.items()}
    for criteria_result in criteria_results:
        criterion_name = criteria_result['criterion']
        original_key = reverse_mapping.get(criterion_name)
        if original_key:
            new_format_response[original_key] = {
                'score': criteria_result['score'],
                'comment': criteria_result['feedback']
            }
    
    logger.info(f"🔄 Transformed AI response: {len(criteria_results)} criteria")
    logger.info(f"📊 AI Score: {ai_overall_score} | Weighted Score: {weighted_overall_score}")
    logger.info(f"📋 Added individual criteria keys for compatibility: {list(reverse_mapping.values())}")
    return new_format_response

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
        
        # Only replace template syntax if it exists in the custom prompt
        if custom_prompt and '${JSON.stringify(' in custom_prompt:
            if config:
                # Generate dynamic JSON structure based on enabled criteria only
                enabled_criteria = [key for key, value in config.items() if value]
                
                # Check if at least one criterion is enabled
                if enabled_criteria:
                    criteria_json = {key: {"score": "<0-10>", "comment": "<explanation>"} for key in enabled_criteria}
                    criteria_json_str = json.dumps(criteria_json, indent=2)
                    
                    # Replace the template with the actual config JSON
                    custom_prompt = re.sub(r'\$\{JSON\.stringify\(\s*config\s*\)\}', criteria_json_str, custom_prompt, flags=re.DOTALL)
                    logger.info(f"🔄 Template replacement: Success - replaced with enabled criteria JSON")
                    logger.info(f"📋 Enabled criteria: {len(enabled_criteria)} items: {enabled_criteria}")
                    
                    # IMPORTANT: Ensure overall_score is always in the prompt
                    if 'overall_score' not in custom_prompt.lower():
                        logger.warning("⚠️ Custom prompt missing 'overall_score' - adding instruction")
                        custom_prompt += "\n\nIMPORTANT: Your response MUST include an 'overall_score' field at the root level with a numeric value from 0-10 representing the overall code quality."
                else:
                    # No criteria enabled - return error
                    logger.warning("❌ No criteria selected for analysis")
                    return jsonify({
                        'error': 'No criteria selected', 
                        'details': 'Please select at least one analysis criterion before running the analysis.',
                        'timestamp': datetime.now().isoformat()
                    }), 400
            else:
                # If no config, replace with empty object (fallback case)
                custom_prompt = re.sub(r'\$\{JSON\.stringify\(\s*config\s*\)\}', '{}', custom_prompt, flags=re.DOTALL)
                logger.info(f"🔄 Template replacement: Success - replaced with empty object")
        else:
            logger.info(f"� Using custom prompt as-is (no template replacement needed)")
        
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

IMPORTANT SCORING INSTRUCTIONS:
1. Calculate the "overall_score" as a weighted average of all individual criterion scores
2. Give higher weight to critical aspects like security, bugs, and code quality
3. Give lower weight to minor aspects like spelling or formatting
4. The overall_score should reflect the true quality of the code changes
5. Focus on code quality, security, performance, and best practices
6. Score each criterion from 0-10 where 10 is excellent"""
        
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
        
        # Transform the response to match frontend expectations
        transformed_result = transform_ai_response_to_frontend_format(result, config)
        
        # Use the transformed result
        result = transformed_result
        
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
