"""
Simple security utilities for Aman Cybersecurity Platform MVP
"""

import logging
from typing import Dict, Any
from datetime import datetime
from fastapi import Request

logger = logging.getLogger(__name__)

def log_security_event(event_type: str, details: Dict[str, Any], ip_address: str = None):
    """Simple security event logging"""
    logger.info(f"Security Event - {event_type}: {details} from {ip_address}")

class InputValidator:
    """Simple input validator"""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        return "@" in email and "." in email
    
    @staticmethod
    def validate_domain(domain: str) -> bool:
        return "." in domain
    
    @staticmethod
    def sanitize_input(text: str) -> str:
        return text.strip() if text else ""

def validate_input(data: Dict[str, Any]) -> Dict[str, Any]:
    """Simple input validation"""
    return data  # For MVP, just return as-is