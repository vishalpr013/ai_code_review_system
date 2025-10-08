# Automated Code Review System

An intelligent automated code review system that integrates with Gerrit and uses Google Gemini AI to provide comprehensive code analysis across 16 different quality criteria.

## Features

🤖 **AI-Powered Analysis**: Uses Google Gemini to provide intelligent code reviews
📊 **Comprehensive Scoring**: Evaluates code across 16 different criteria
🔗 **Gerrit Integration**: Seamlessly integrates with Gerrit via webhooks
🛡️ **Security Analysis**: Identifies potential security vulnerabilities
📈 **Complexity Analysis**: Measures cyclomatic complexity and code smells
🔍 **Rule-Based Checks**: Combines AI analysis with traditional rule-based checks
📝 **Detailed Feedback**: Provides actionable suggestions and recommendations
⚡ **Real-time Processing**: Processes reviews asynchronously via background queue

## Review Criteria

The system evaluates code changes across these 16 criteria:

1. **Are Code Changes Optimized** - Performance and efficiency evaluation
2. **Are Code Changes Relative** - Relevance to intended functionality
3. **Is Code Formatted** - Style consistency and formatting
4. **Is Code Well Written** - Overall code quality and readability
5. **Are Comments Written** - Adequate and meaningful comments
6. **Cyclomatic Complexity Score** - Code complexity measurement
7. **Missing Elements** - Missing components like error handling
8. **Loopholes** - Logic gaps and edge cases
9. **Is Commit Message Well Written** - Commit message quality
10. **Is Naming Convention Followed** - Adherence to naming standards
11. **Are There Any Spelling Mistakes** - Spelling errors in code/comments
12. **Security Concerns Any** - Potential security vulnerabilities
13. **Is Code Duplicated** - Code duplication detection
14. **Are Constants Defined Centrally** - Proper constant management
15. **Is Code Modular** - Modularity and separation of concerns
16. **Is Logging Done Properly** - Proper logging implementation

## Installation

### Prerequisites

- Python 3.8 or higher
- Gerrit server with webhook support
- Google Gemini API key

### Setup

1. **Clone or download the project**:
   ```bash
   # The system is already set up in this directory
   cd code-review
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Set up your environment file (.env)**:
   ```env
   # Gemini API Configuration
   GEMINI_API_KEY=your_gemini_api_key_here
   GEMINI_MODEL=gemini-1.5-flash
   
   # Gerrit Configuration
   GERRIT_HOST=your-gerrit-server.com
   GERRIT_PORT=8080
   GERRIT_USERNAME=your-gerrit-username
   GERRIT_PASSWORD=your-gerrit-password
   
   # Application Configuration
   APP_HOST=0.0.0.0
   APP_PORT=5000
   AUTO_POST_REVIEW=true
   MIN_REVIEW_SCORE=7.0
   ```

## Usage

### Starting the Service

```bash
python src/main.py
```

The service will start and listen for webhooks on the configured port (default: 5000).

### Available Endpoints

- **GET /health** - Health check endpoint
- **GET /status** - System status and queue information
- **GET /config** - Current configuration
- **POST /webhook** - Gerrit webhook endpoint
- **POST /manual-review** - Manually trigger a review

### Gerrit Webhook Configuration

Configure Gerrit to send webhooks to your service:

1. **In Gerrit, go to Projects → Your Project → General**
2. **Add webhook URL**: `http://your-server:5000/webhook`
3. **Select events**: `patchset-created`
4. **Save configuration**

### Manual Review Trigger

You can manually trigger a review using the REST API:

```bash
curl -X POST http://localhost:5000/manual-review \\
  -H "Content-Type: application/json" \\
  -d '{
    "change_id": "your-change-id",
    "revision_id": "current",
    "project": "your-project",
    "branch": "main"
  }'
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Google Gemini API key | Required |
| `GEMINI_MODEL` | Gemini model to use | `gemini-1.5-flash` |
| `GERRIT_HOST` | Gerrit server hostname | Required |
| `GERRIT_PORT` | Gerrit server port | `8080` |
| `GERRIT_USERNAME` | Gerrit username | Required |
| `GERRIT_PASSWORD` | Gerrit password | Required |
| `APP_HOST` | Application host | `0.0.0.0` |
| `APP_PORT` | Application port | `5000` |
| `AUTO_POST_REVIEW` | Auto-post reviews to Gerrit | `true` |
| `MIN_REVIEW_SCORE` | Minimum score for approval | `7.0` |
| `LOG_LEVEL` | Logging level | `INFO` |

### Review Criteria Configuration

You can customize review criteria in `config/review_criteria.json`:

```json
{
  "review_criteria": {
    "areCodeChangesOptimized": {
      "label": "Are Code Changes Optimized",
      "weight": 1.0,
      "enabled": true,
      "thresholds": {
        "excellent": 9,
        "good": 7,
        "acceptable": 5,
        "poor": 3
      }
    }
  }
}
```

## Architecture

The system consists of several key components:

### Core Components

- **`main.py`** - Flask web server and webhook handler
- **`gerrit_client.py`** - Gerrit REST API integration
- **`llm_client.py`** - Google Gemini AI integration
- **`review_evaluator.py`** - Main orchestration logic
- **`utils.py`** - Utility functions and helpers
- **`config.py`** - Configuration management

### Process Flow

1. **Webhook Reception** - Gerrit sends webhook on code push
2. **Change Extraction** - System extracts change information
3. **Code Analysis** - Combined AI and rule-based analysis
4. **Review Generation** - Comprehensive review with scores
5. **Result Posting** - Review posted back to Gerrit (optional)

## API Reference

### Health Check
```http
GET /health
```

Response:
```json
{
  "status": "healthy",
  "services": {
    "gerrit_client": "ok",
    "gemini_client": "ok",
    "review_evaluator": "ok"
  },
  "queue_size": 0,
  "timestamp": "2025-01-07 12:00:00 UTC"
}
```

### Manual Review
```http
POST /manual-review
Content-Type: application/json

{
  "change_id": "your-change-id",
  "revision_id": "current",
  "project": "your-project",
  "branch": "main"
}
```

## Development

### Project Structure

```
code-review/
├── src/
│   ├── __init__.py
│   ├── main.py              # Main application
│   ├── config.py           # Configuration management
│   ├── gerrit_client.py    # Gerrit integration
│   ├── llm_client.py       # Gemini AI integration
│   ├── review_evaluator.py # Review orchestration
│   └── utils.py            # Utility functions
├── config/
│   ├── review_criteria.json # Review criteria config
│   └── README.md
├── logs/                   # Log files
├── requirements.txt        # Python dependencies
├── .env.example           # Environment template
└── README.md              # This file
```

### Adding New Criteria

1. **Update `config.py`** - Add new criterion to `ReviewCriteria.CRITERIA`
2. **Update prompt** - Modify prompt in `llm_client.py`
3. **Add rule-based checks** - Implement in `review_evaluator.py`
4. **Update configuration** - Modify `config/review_criteria.json`

### Testing

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests
pytest

# Run with coverage
pytest --cov=src
```

## Logging

The system provides comprehensive logging:

- **Console output** - Real-time status and errors
- **File logging** - Detailed logs in `logs/code_review.log`
- **Review storage** - Individual reviews saved as JSON files

## Security Considerations

- Store API keys securely in environment variables
- Use HTTPS for production deployments
- Implement webhook authentication if needed
- Regularly rotate API keys and passwords
- Monitor logs for suspicious activity

## Troubleshooting

### Common Issues

1. **Gemini API errors**
   - Verify API key is correct
   - Check API quotas and limits
   - Ensure model name is valid

2. **Gerrit connection issues**
   - Verify hostname and port
   - Check credentials
   - Ensure Gerrit REST API is enabled

3. **Webhook not received**
   - Check Gerrit webhook configuration
   - Verify network connectivity
   - Check firewall settings

### Debug Mode

Enable debug mode for verbose logging:

```bash
export APP_DEBUG=true
export LOG_LEVEL=DEBUG
python src/main.py
```

## Performance

- Reviews are processed asynchronously in background queue
- Configurable timeouts prevent hanging requests
- File size limits prevent oversized analyses
- Connection pooling for efficient API usage

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is available under the MIT License.

## Support

For issues and questions:

1. Check the troubleshooting section
2. Review the logs for error details
3. Open an issue with detailed information

---

**Happy Code Reviewing! 🚀**
