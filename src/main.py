"""
Main application for the automated code review system.
Flask web server that receives Gerrit webhooks and orchestrates the review process.
"""
import asyncio
import json
import logging
import os
import signal
import sys
from datetime import datetime
from typing import Dict, Any

from flask import Flask, request, jsonify, Response
import threading

# Add the src directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from config import settings
from gerrit_client import GerritClient
from llm_client import GeminiClient
from review_evaluator import ReviewEvaluator
from utils import setup_logger, format_timestamp

# Initialize logger
logger = setup_logger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Global instances
gerrit_client = None
gemini_client = None
review_evaluator = None

# Background task queue
review_queue = asyncio.Queue()
is_running = True


def initialize_clients():
    """Initialize all clients and services."""
    global gerrit_client, gemini_client, review_evaluator
    
    try:
        logger.info("Initializing clients...")
        
        # Initialize Gerrit client
        gerrit_client = GerritClient()
        logger.info("Gerrit client initialized")
        
        # Initialize Gemini client
        gemini_client = GeminiClient()
        logger.info("Gemini client initialized")
        
        # Test Gemini connection
        if not gemini_client.test_connection():
            logger.error("Gemini connection test failed")
            return False
        
        # Initialize review evaluator
        review_evaluator = ReviewEvaluator(gerrit_client, gemini_client)
        logger.info("Review evaluator initialized")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize clients: {e}")
        return False


async def background_review_processor():
    """Background task processor for handling reviews."""
    logger.info("Background review processor started")
    
    while is_running:
        try:
            # Wait for a review task with timeout
            webhook_payload = await asyncio.wait_for(review_queue.get(), timeout=1.0)
            
            logger.info(f"Processing review for change {webhook_payload.get('change', {}).get('id', 'unknown')}")
            
            # Perform evaluation
            review_result = await review_evaluator.evaluate_change(webhook_payload)
            
            if review_result:
                # Post review back to Gerrit if configured
                await review_evaluator.post_review_to_gerrit(review_result)
                logger.info("Review completed and posted")
            else:
                logger.error("Review evaluation failed")
            
            # Mark task as done
            review_queue.task_done()
            
        except asyncio.TimeoutError:
            # No tasks in queue, continue
            continue
        except Exception as e:
            logger.error(f"Error in background processor: {e}")
            # Mark task as done even on error
            try:
                review_queue.task_done()
            except:
                pass


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    try:
        # Check if clients are initialized
        if not all([gerrit_client, gemini_client, review_evaluator]):
            return jsonify({
                'status': 'unhealthy',
                'message': 'Clients not properly initialized',
                'timestamp': format_timestamp()
            }), 503
        
        # Test Gemini connection
        gemini_status = gemini_client.test_connection()
        
        return jsonify({
            'status': 'healthy' if gemini_status else 'degraded',
            'services': {
                'gerrit_client': 'ok',
                'gemini_client': 'ok' if gemini_status else 'error',
                'review_evaluator': 'ok'
            },
            'queue_size': review_queue.qsize(),
            'timestamp': format_timestamp()
        }), 200 if gemini_status else 503
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': format_timestamp()
        }), 500


@app.route('/webhook', methods=['POST'])
def handle_webhook():
    """Handle incoming Gerrit webhooks."""
    try:
        # Check if we're ready to process
        if not all([gerrit_client, gemini_client, review_evaluator]):
            logger.error("Services not initialized")
            return jsonify({'error': 'Services not ready'}), 503
        
        # Validate content type
        if not request.is_json:
            logger.warning("Received non-JSON webhook")
            return jsonify({'error': 'Content-Type must be application/json'}), 400
        
        webhook_payload = request.get_json()
        
        if not webhook_payload:
            logger.warning("Received empty webhook payload")
            return jsonify({'error': 'Empty payload'}), 400
        
        # Log webhook received
        event_type = webhook_payload.get('eventType', 'unknown')
        change_id = webhook_payload.get('change', {}).get('id', 'unknown')
        
        logger.info(f"Received webhook: {event_type} for change {change_id}")
        
        # Validate webhook payload
        if not gerrit_client.validate_webhook_payload(webhook_payload):
            logger.info("Webhook payload validation failed or event type ignored")
            return jsonify({'message': 'Event ignored'}), 200
        
        # Add to review queue for background processing
        try:
            # Add timestamp to payload
            webhook_payload['received_timestamp'] = format_timestamp()
            
            # Add to queue (non-blocking)
            review_queue.put_nowait(webhook_payload)
            
            logger.info(f"Added change {change_id} to review queue")
            
            return jsonify({
                'message': 'Webhook received and queued for processing',
                'change_id': change_id,
                'event_type': event_type,
                'queue_size': review_queue.qsize(),
                'timestamp': format_timestamp()
            }), 202
            
        except asyncio.QueueFull:
            logger.error("Review queue is full")
            return jsonify({'error': 'Review queue is full, try again later'}), 429
        
    except Exception as e:
        logger.error(f"Error handling webhook: {e}")
        return jsonify({
            'error': 'Internal server error',
            'timestamp': format_timestamp()
        }), 500


@app.route('/status', methods=['GET'])
def get_status():
    """Get system status and statistics."""
    try:
        return jsonify({
            'system_status': 'running',
            'queue_size': review_queue.qsize(),
            'configuration': {
                'gerrit_host': settings.gerrit_host,
                'gemini_model': settings.gemini_model,
                'auto_post_review': settings.auto_post_review,
                'min_review_score': settings.min_review_score
            },
            'review_criteria_count': len(get_review_criteria()),
            'timestamp': format_timestamp()
        })
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/manual-review', methods=['POST'])
def manual_review():
    """Manually trigger a review for a specific change."""
    try:
        data = request.get_json()
        
        if not data or 'change_id' not in data:
            return jsonify({'error': 'change_id is required'}), 400
        
        change_id = data['change_id']
        revision_id = data.get('revision_id', 'current')
        
        logger.info(f"Manual review requested for {change_id}/{revision_id}")
        
        # Create a mock webhook payload
        webhook_payload = {
            'eventType': 'patchset-created',
            'change': {
                'id': change_id,
                'number': data.get('change_number', 0),
                'project': data.get('project', ''),
                'branch': data.get('branch', 'main'),
                'subject': data.get('subject', 'Manual review'),
                'owner': {
                    'name': data.get('owner_name', 'Manual'),
                    'email': data.get('owner_email', 'manual@example.com')
                }
            },
            'patchSet': {
                'revision': revision_id
            },
            'received_timestamp': format_timestamp()
        }
        
        # Add to queue
        review_queue.put_nowait(webhook_payload)
        
        return jsonify({
            'message': 'Manual review queued',
            'change_id': change_id,
            'revision_id': revision_id,
            'queue_size': review_queue.qsize(),
            'timestamp': format_timestamp()
        }), 202
        
    except Exception as e:
        logger.error(f"Error processing manual review: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/config', methods=['GET'])
def get_config():
    """Get current configuration (without sensitive data)."""
    try:
        from config import get_review_criteria
        
        return jsonify({
            'review_criteria': get_review_criteria(),
            'settings': {
                'gemini_model': settings.gemini_model,
                'gemini_temperature': settings.gemini_temperature,
                'auto_post_review': settings.auto_post_review,
                'min_review_score': settings.min_review_score,
                'app_host': settings.app_host,
                'app_port': settings.app_port,
                'log_level': settings.log_level
            },
            'timestamp': format_timestamp()
        })
    except Exception as e:
        logger.error(f"Error getting config: {e}")
        return jsonify({'error': str(e)}), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        'error': 'Endpoint not found',
        'timestamp': format_timestamp()
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {error}")
    return jsonify({
        'error': 'Internal server error',
        'timestamp': format_timestamp()
    }), 500


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    global is_running
    logger.info(f"Received signal {signum}, shutting down...")
    is_running = False
    sys.exit(0)


def run_background_processor():
    """Run the background processor in a separate thread."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(background_review_processor())


def main():
    """Main application entry point."""
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("Starting automated code review system...")
    
    # Initialize clients
    if not initialize_clients():
        logger.error("Failed to initialize clients, exiting")
        sys.exit(1)
    
    # Start background processor thread
    processor_thread = threading.Thread(target=run_background_processor, daemon=True)
    processor_thread.start()
    
    logger.info(f"Background processor started in thread {processor_thread.name}")
    
    # Print startup information
    logger.info(f"Server starting on {settings.app_host}:{settings.app_port}")
    logger.info(f"Debug mode: {settings.app_debug}")
    logger.info(f"Gerrit host: {settings.gerrit_host}:{settings.gerrit_port}")
    logger.info(f"Gemini model: {settings.gemini_model}")
    logger.info(f"Auto-post reviews: {settings.auto_post_review}")
    
    # Available endpoints
    logger.info("Available endpoints:")
    logger.info("  GET  /health       - Health check")
    logger.info("  GET  /status       - System status")
    logger.info("  GET  /config       - Configuration")
    logger.info("  POST /webhook      - Gerrit webhook")
    logger.info("  POST /manual-review - Manual review trigger")
    
    try:
        # Start Flask app
        app.run(
            host=settings.app_host,
            port=settings.app_port,
            debug=settings.app_debug,
            threaded=True
        )
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
