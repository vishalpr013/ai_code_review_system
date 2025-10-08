"""
Gerrit client for interacting with Gerrit code review system.
"""
import json
import logging
from typing import Dict, List, Optional, Any
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime

from config import settings
from utils import setup_logger

logger = setup_logger(__name__)


class GerritClient:
    """Client for interacting with Gerrit REST API."""
    
    def __init__(self, host: str = None, port: int = None, username: str = None, password: str = None):
        """Initialize Gerrit client."""
        self.host = host or settings.gerrit_host
        self.port = port or settings.gerrit_port
        self.username = username or settings.gerrit_username
        self.password = password or settings.gerrit_password
        
        self.base_url = f"http://{self.host}:{self.port}"
        self.auth = HTTPBasicAuth(self.username, self.password)
        
        # Session for connection pooling
        self.session = requests.Session()
        self.session.auth = self.auth
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        logger.info(f"Initialized Gerrit client for {self.base_url}")
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict]:
        """Make HTTP request to Gerrit API."""
        url = f"{self.base_url}/a/{endpoint}"
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            
            # Gerrit responses start with )]}' to prevent XSSI
            content = response.text
            if content.startswith(")]}'"):
                content = content[4:]
            
            return json.loads(content) if content.strip() else {}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Gerrit API request failed: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gerrit response: {e}")
            return None
    
    def get_change_details(self, change_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a change."""
        logger.info(f"Fetching change details for {change_id}")
        
        endpoint = f"changes/{change_id}/detail"
        params = {
            'o': ['CURRENT_REVISION', 'CURRENT_COMMIT', 'CURRENT_FILES', 'DETAILED_LABELS']
        }
        
        return self._make_request('GET', endpoint, params=params)
    
    def get_change_files(self, change_id: str, revision_id: str = 'current') -> Optional[Dict[str, Any]]:
        """Get files changed in a revision."""
        logger.info(f"Fetching changed files for {change_id}/{revision_id}")
        
        endpoint = f"changes/{change_id}/revisions/{revision_id}/files"
        return self._make_request('GET', endpoint)
    
    def get_file_diff(self, change_id: str, revision_id: str, file_path: str) -> Optional[str]:
        """Get diff for a specific file."""
        logger.info(f"Fetching diff for {change_id}/{revision_id}/{file_path}")
        
        endpoint = f"changes/{change_id}/revisions/{revision_id}/files/{file_path}/diff"
        params = {'context': 'ALL', 'intraline': 'true'}
        
        diff_data = self._make_request('GET', endpoint, params=params)
        if not diff_data:
            return None
        
        return self._format_diff(diff_data)
    
    def get_commit_message(self, change_id: str, revision_id: str = 'current') -> Optional[str]:
        """Get commit message for a revision."""
        logger.info(f"Fetching commit message for {change_id}/{revision_id}")
        
        endpoint = f"changes/{change_id}/revisions/{revision_id}/commit"
        commit_data = self._make_request('GET', endpoint)
        
        if commit_data and 'message' in commit_data:
            return commit_data['message']
        return None
    
    def post_review(self, change_id: str, revision_id: str, review_data: Dict[str, Any]) -> bool:
        """Post a review to Gerrit."""
        logger.info(f"Posting review for {change_id}/{revision_id}")
        
        endpoint = f"changes/{change_id}/revisions/{revision_id}/review"
        
        # Format review data for Gerrit
        gerrit_review = {
            'message': review_data.get('message', ''),
            'score': review_data.get('score', 0),
            'labels': review_data.get('labels', {}),
            'comments': review_data.get('comments', {})
        }
        
        result = self._make_request('POST', endpoint, json=gerrit_review)
        return result is not None
    
    def _format_diff(self, diff_data: Dict) -> str:
        """Format diff data into readable text."""
        if not diff_data or 'content' not in diff_data:
            return ""
        
        diff_text = []
        for content in diff_data['content']:
            if 'ab' in content:
                # Context lines
                for line in content['ab']:
                    diff_text.append(f" {line}")
            elif 'a' in content:
                # Deleted lines
                for line in content['a']:
                    diff_text.append(f"-{line}")
            elif 'b' in content:
                # Added lines
                for line in content['b']:
                    diff_text.append(f"+{line}")
        
        return "\n".join(diff_text)
    
    def validate_webhook_payload(self, payload: Dict) -> bool:
        """Validate incoming webhook payload."""
        required_fields = ['change', 'patchSet', 'eventType']
        
        for field in required_fields:
            if field not in payload:
                logger.warning(f"Missing required field in webhook payload: {field}")
                return False
        
        # Only process patchset-created events
        if payload['eventType'] != 'patchset-created':
            logger.info(f"Ignoring event type: {payload['eventType']}")
            return False
        
        return True
    
    def extract_change_info(self, webhook_payload: Dict) -> Optional[Dict[str, str]]:
        """Extract change information from webhook payload."""
        if not self.validate_webhook_payload(webhook_payload):
            return None
        
        change = webhook_payload['change']
        patch_set = webhook_payload['patchSet']
        
        return {
            'change_id': change['id'],
            'change_number': str(change['number']),
            'revision_id': patch_set['revision'],
            'project': change['project'],
            'branch': change['branch'],
            'subject': change['subject'],
            'owner': change['owner']['name'],
            'owner_email': change['owner']['email']
        }


class CodeChange:
    """Represents a code change with all relevant information for review."""
    
    def __init__(self, change_info: Dict[str, str], gerrit_client: GerritClient):
        self.change_info = change_info
        self.gerrit_client = gerrit_client
        self.files_diff: Dict[str, str] = {}
        self.commit_message: str = ""
        self.loaded = False
    
    async def load_change_data(self) -> bool:
        """Load all change data from Gerrit."""
        try:
            change_id = self.change_info['change_id']
            revision_id = self.change_info['revision_id']
            
            # Get commit message
            self.commit_message = self.gerrit_client.get_commit_message(change_id, revision_id) or ""
            
            # Get changed files
            files_data = self.gerrit_client.get_change_files(change_id, revision_id)
            if not files_data:
                logger.error("Failed to get changed files")
                return False
            
            # Get diff for each changed file
            for file_path in files_data.keys():
                if file_path == '/COMMIT_MSG':
                    continue  # Skip commit message file
                
                diff = self.gerrit_client.get_file_diff(change_id, revision_id, file_path)
                if diff:
                    self.files_diff[file_path] = diff
            
            self.loaded = True
            logger.info(f"Loaded data for change {change_id}: {len(self.files_diff)} files")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load change data: {e}")
            return False
    
    def get_review_context(self) -> Dict[str, Any]:
        """Get all context needed for code review."""
        return {
            'change_info': self.change_info,
            'commit_message': self.commit_message,
            'files_diff': self.files_diff,
            'file_count': len(self.files_diff),
            'total_lines_changed': sum(
                len([line for line in diff.split('\n') if line.startswith(('+', '-'))])
                for diff in self.files_diff.values()
            )
        }
