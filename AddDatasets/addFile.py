#!/usr/bin/env python3
"""
Document Training Script for AI Mentor System
Safely uploads and trains documents to specified mentor pathways.

Usage:
    python addFile.py

Author: Syracuse University
Version: 1.0
"""

import requests
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import logging
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('document_upload.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class DocumentUploadError(Exception):
    """Custom exception for document upload failures"""
    pass


class ConfigurationError(Exception):
    """Custom exception for configuration issues"""
    pass


def validate_file_path(file_path: str) -> Path:
    """
    Validate that the file exists and is accessible.
    
    Args:
        file_path: Path to the file to validate
        
    Returns:
        Path object of the validated file
        
    Raises:
        ConfigurationError: If file doesn't exist or isn't readable
    """
    path = Path(file_path)
    
    if not path.exists():
        raise ConfigurationError(f"File not found: {file_path}")
    
    if not path.is_file():
        raise ConfigurationError(f"Path is not a file: {file_path}")
    
    if not os.access(path, os.R_OK):
        raise ConfigurationError(f"File is not readable: {file_path}")
    
    # Check file size (e.g., max 100MB)
    max_size = 100 * 1024 * 1024  # 100MB in bytes
    file_size = path.stat().st_size
    if file_size > max_size:
        raise ConfigurationError(
            f"File too large: {file_size / (1024*1024):.2f}MB (max: 100MB)"
        )
    
    if file_size == 0:
        raise ConfigurationError(f"File is empty: {file_path}")
    
    logger.info(f"File validated: {file_path} ({file_size / 1024:.2f}KB)")
    return path


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    Returns:
        Namespace object containing parsed arguments
    """
    parser = argparse.ArgumentParser(
        description='Upload and train documents to AI Mentor System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  %(prog)s -u jasidel -m 25223e76-fc94-4cc2-aec1-f9fb51f0c2bf -f document.pdf
  
  # With custom organization
  %(prog)s -o myorg -u jsmith -m abc-123-def -f report.pdf
  
  # With custom credentials file
  %(prog)s -u jasidel -m abc-123 -f doc.pdf -c my_api_key.txt
        """
    )
    
    parser.add_argument(
        '-o', '--org-id',
        type=str,
        default='syracuse',
        help='Organization ID (default: syracuse)'
    )
    
    parser.add_argument(
        '-u', '--user-id',
        type=str,
        required=True,
        help='User NetID (required)'
    )
    
    parser.add_argument(
        '-m', '--mentor-id',
        type=str,
        required=True,
        help='Mentor pathway ID (required)'
    )
    
    parser.add_argument(
        '-f', '--file',
        type=str,
        required=True,
        help='Path to document file to upload (required)'
    )
    
    parser.add_argument(
        '-c', '--credentials',
        type=str,
        default='api_credentials.txt',
        help='Path to API credentials file (default: api_credentials.txt)'
    )
    
    parser.add_argument(
        '-b', '--base-url',
        type=str,
        default='https://base.manager.ai.syr.edu',
        help='Base URL for API (default: https://base.manager.ai.syr.edu)'
    )
    
    parser.add_argument(
        '-t', '--timeout',
        type=int,
        default=300,
        help='Request timeout in seconds (default: 300)'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Validate timeout
    if args.timeout < 1:
        parser.error("Timeout must be at least 1 second")
    
    return args


def load_api_key(credential_file: str = 'api_credentials.txt') -> str:
    """
    Securely load API key from credentials file.
    
    Args:
        credential_file: Path to the credentials file
        
    Returns:
        API key string
        
    Raises:
        ConfigurationError: If credentials file is missing or invalid
    """
    cred_path = Path(credential_file)
    
    if not cred_path.exists():
        raise ConfigurationError(
            f"Credentials file not found: {credential_file}\n"
            f"Please create this file with your API key on the first line."
        )
    
    try:
        with open(cred_path, 'r') as f:
            api_key = f.readline().strip()
        
        if not api_key:
            raise ConfigurationError("API key is empty in credentials file")
        
        # Basic validation - check it's not obviously wrong
        if len(api_key) < 10:
            raise ConfigurationError("API key appears to be invalid (too short)")
        
        logger.info("API key loaded successfully")
        return api_key
        
    except IOError as e:
        raise ConfigurationError(f"Error reading credentials file: {e}")


def validate_configuration(
    org_id: str,
    user_id: str,
    mentor_id: str
) -> None:
    """
    Validate configuration parameters.
    
    Args:
        org_id: Organization ID
        user_id: User NetID
        mentor_id: Mentor pathway ID
        
    Raises:
        ConfigurationError: If any parameter is invalid
    """
    if not org_id or not isinstance(org_id, str):
        raise ConfigurationError("Organization ID must be a non-empty string")
    
    if not user_id or not isinstance(user_id, str):
        raise ConfigurationError("User ID must be a non-empty string")
    
    if not mentor_id or not isinstance(mentor_id, str):
        raise ConfigurationError("Mentor ID must be a non-empty string")
    
    # Validate mentor_id format (UUID-like)
    if len(mentor_id) != 36 or mentor_id.count('-') != 4:
        logger.warning(
            f"Mentor ID format looks unusual: {mentor_id}\n"
            f"Expected UUID format (e.g., 25223e76-fc94-4cc2-aec1-f9fb51f0c2bf)"
        )
    
    logger.info(f"Configuration validated - Org: {org_id}, User: {user_id}")


def upload_document(
    org_id: str,
    user_id: str,
    mentor_id: str,
    file_path: Path,
    api_key: str,
    base_url: str = "https://base.manager.ai.syr.edu",
    timeout: int = 300  # 5 minutes
) -> Dict[str, Any]:
    """
    Upload and train a document to the mentor system.
    
    Args:
        org_id: Organization ID
        user_id: User NetID
        mentor_id: Mentor pathway ID
        file_path: Path to the document file
        api_key: API authentication key
        base_url: Base URL for the API
        timeout: Request timeout in seconds
        
    Returns:
        Dictionary containing the response data
        
    Raises:
        DocumentUploadError: If upload fails
    """
    # Construct URL
    url = f"{base_url}/api/ai-index/orgs/{org_id}/users/{user_id}/documents/train/"
    
    # Prepare headers
    headers = {
        'Authorization': f'Api-Token {api_key}'
    }
    
    # Determine MIME type based on extension
    mime_types = {
        '.pdf': 'application/pdf',
        '.txt': 'text/plain',
        '.doc': 'application/msword',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    }
    
    file_extension = file_path.suffix.lower()
    mime_type = mime_types.get(file_extension, 'application/octet-stream')
    
    if mime_type == 'application/octet-stream':
        logger.warning(f"Unknown file type: {file_extension}, using generic MIME type")
    
    # Document type for API - always use 'file' to match browser behavior
    doc_type = 'file'
    
    logger.info(f"Uploading document: {file_path.name}")
    logger.info(f"Target URL: {url}")
    logger.info(f"Document type: {doc_type}, MIME type: {mime_type}")
    
    try:
        with open(file_path, 'rb') as f:
            files = {
                'file': (file_path.name, f, mime_type)
            }
            data = {
                'pathway': mentor_id,
                'type': doc_type,
                'name': file_path.name
            }
            
            response = requests.post(
                url,
                headers=headers,
                files=files,
                data=data,
                timeout=timeout
            )
        
        # Check response status
        if response.status_code in [200, 201]:
            result = response.json()
            logger.info("Upload successful!")
            logger.info(f"Document ID: {result.get('document_id', 'N/A')}")
            return result
        else:
            error_msg = f"Upload failed with status {response.status_code}"
            try:
                error_detail = response.json()
                error_msg += f"\nDetails: {error_detail}"
            except:
                error_msg += f"\nResponse: {response.text}"
            
            logger.error(error_msg)
            raise DocumentUploadError(error_msg)
    
    except requests.exceptions.Timeout:
        raise DocumentUploadError(
            f"Upload timed out after {timeout} seconds. "
            f"The file may be too large or the server is slow to respond."
        )
    except requests.exceptions.ConnectionError as e:
        raise DocumentUploadError(f"Connection error: {e}")
    except requests.exceptions.RequestException as e:
        raise DocumentUploadError(f"Request failed: {e}")


def main() -> int:
    """
    Main execution function.
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    # Parse command-line arguments
    args = parse_arguments()
    
    # Configure logging level based on verbose flag
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")
    
    logger.info("=" * 60)
    logger.info("Document Upload Script Started")
    logger.info("=" * 60)
    
    # Log configuration (but not sensitive data)
    logger.info(f"Organization: {args.org_id}")
    logger.info(f"User: {args.user_id}")
    logger.info(f"Mentor ID: {args.mentor_id}")
    logger.info(f"File: {args.file}")
    logger.info(f"Base URL: {args.base_url}")
    logger.info(f"Timeout: {args.timeout}s")
    
    try:
        # Validate configuration
        validate_configuration(args.org_id, args.user_id, args.mentor_id)
        
        # Load API credentials
        api_key = load_api_key(args.credentials)
        
        # Validate file
        validated_path = validate_file_path(args.file)
        
        # Upload document
        result = upload_document(
            org_id=args.org_id,
            user_id=args.user_id,
            mentor_id=args.mentor_id,
            file_path=validated_path,
            api_key=api_key,
            base_url=args.base_url,
            timeout=args.timeout
        )
        
        logger.info("=" * 60)
        logger.info("Script completed successfully!")
        logger.info("=" * 60)
        return 0
        
    except ConfigurationError as e:
        logger.error(f"Configuration Error: {e}")
        logger.error("Please check your settings and try again.")
        return 1
        
    except DocumentUploadError as e:
        logger.error(f"Upload Error: {e}")
        return 1
        
    except KeyboardInterrupt:
        logger.warning("\nScript interrupted by user")
        return 130
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
