"""
AI-Powered Email Scanning using Google Gemini
Advanced phishing detection with natural language processing and machine learning
"""

import os
import json
import uuid
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import asyncio
from dataclasses import dataclass
import re

from emergentintegrations.llm.chat import LlmChat, UserMessage
from database import get_database
from ai_cost_manager import (
    record_ai_usage, check_ai_usage_limits, 
    get_cached_ai_response, cache_ai_response
)

# Configure logging
logger = logging.getLogger(__name__)

# Security and content filtering
SENSITIVE_PATTERNS = [
    # Personal identifiers
    r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
    r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',  # Credit card
    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email addresses
    r'\b\d{3}-\d{3}-\d{4}\b',  # Phone numbers
    # API keys and tokens (basic patterns)
    r'[Aa][Pp][Ii]_?[Kk][Ee][Yy]\s*[:=]\s*["\']?[\w-]+["\']?',
    r'[Tt][Oo][Kk][Ee][Nn]\s*[:=]\s*["\']?[\w.-]+["\']?',
]

@dataclass 
class AIThreatAnalysis:
    """Advanced threat analysis result from AI"""
    risk_score: float  # 0-100
    risk_level: str  # "safe", "potential_phishing", "phishing"
    threat_categories: List[str]
    confidence: float  # 0-1
    explanation: str
    ai_reasoning: str
    detected_patterns: List[str]
    recommendations: List[str]
    metadata: Dict[str, Any]

class ContentFilter:
    """Content filtering and sanitization for AI requests"""
    
    @staticmethod
    def sanitize_for_ai(content: str, max_length: int = 2000) -> str:
        """Sanitize content for AI analysis"""
        if not content:
            return ""
        
        # Remove sensitive information
        sanitized = content
        for pattern in SENSITIVE_PATTERNS:
            sanitized = re.sub(pattern, '[REDACTED]', sanitized, flags=re.IGNORECASE)
        
        # Limit length
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length] + "..."
        
        # Remove control characters
        sanitized = ''.join(char for char in sanitized if ord(char) >= 32 or char in '\n\r\t')
        
        return sanitized.strip()
    
    @staticmethod
    def extract_metadata(content: str) -> Dict[str, Any]:
        """Extract safe metadata from content"""
        return {
            "length": len(content),
            "word_count": len(content.split()),
            "line_count": content.count('\n'),
            "has_urls": bool(re.search(r'https?://\S+', content)),
            "has_numbers": bool(re.search(r'\d+', content)),
            "uppercase_ratio": sum(c.isupper() for c in content) / len(content) if content else 0,
        }

class GeminiAIScanner:
    """AI-powered email scanner using Google Gemini"""
    
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        self.content_filter = ContentFilter()
        
        # AI configuration
        self.model_name = "gemini-2.0-flash"
        self.max_tokens = 1024
        
        # System message for phishing detection
        self.system_message = """You are a cybersecurity expert specializing in phishing email detection for enterprise environments.

MISSION: Analyze email content and provide precise threat assessment focused on protecting SMEs in regulated sectors (finance, healthcare, insurance).

ANALYSIS CRITERIA:
1. PHISHING INDICATORS: Credential harvesting, urgency manipulation, social engineering
2. BUSINESS EMAIL COMPROMISE (BEC): Executive impersonation, financial requests
3. SOCIAL ENGINEERING: Trust building, authority claims, fear tactics
4. TECHNICAL INDICATORS: Suspicious links, domain spoofing, grammar issues

RESPONSE FORMAT - Always respond in valid JSON:
{
  "risk_score": <0-100 float>,
  "risk_level": "<safe|potential_phishing|phishing>",
  "threat_categories": ["<category1>", "<category2>"],
  "confidence": <0-1 float>,
  "explanation": "<brief explanation>",
  "ai_reasoning": "<detailed analysis>",
  "detected_patterns": ["<pattern1>", "<pattern2>"],
  "recommendations": ["<rec1>", "<rec2>"]
}

THREAT CATEGORIES:
- credential_harvesting
- social_engineering
- business_email_compromise
- financial_scam
- malware_delivery
- domain_spoofing
- urgency_manipulation

RISK LEVELS:
- safe (0-29): Legitimate business communication
- potential_phishing (30-69): Suspicious elements requiring caution  
- phishing (70-100): High confidence threat requiring immediate action

Be precise, professional, and focus on actionable intelligence."""

    async def analyze_email_content(self, email_data: Dict[str, Any]) -> AIThreatAnalysis:
        """Analyze email content using Gemini AI"""
        try:
            # Extract and sanitize email components
            subject = email_data.get('email_subject', '')
            body = email_data.get('email_body', '')
            sender = email_data.get('sender', '')
            recipient = email_data.get('recipient', '')
            
            # Sanitize content for AI
            safe_subject = self.content_filter.sanitize_for_ai(subject, 200)
            safe_body = self.content_filter.sanitize_for_ai(body, 1500)
            safe_sender = self.content_filter.sanitize_for_ai(sender, 100)
            
            # Create analysis prompt
            analysis_prompt = f"""Analyze this email for phishing threats:

SUBJECT: {safe_subject}
FROM: {safe_sender}
BODY: {safe_body}

Provide detailed threat analysis in JSON format."""

            # Generate unique session ID
            session_id = f"email_scan_{uuid.uuid4().hex[:12]}"
            
            # Initialize Gemini AI chat
            chat = LlmChat(
                api_key=self.api_key,
                session_id=session_id,
                system_message=self.system_message
            ).with_model("gemini", self.model_name).with_max_tokens(self.max_tokens)
            
            # Send message to AI
            user_message = UserMessage(text=analysis_prompt)
            ai_response = await chat.send_message(user_message)
            
            # Parse AI response
            analysis_result = self._parse_ai_response(ai_response, email_data)
            
            # Store analysis in database for learning
            await self._store_ai_analysis(analysis_result, email_data)
            
            logger.info(f"AI email analysis completed: risk_score={analysis_result.risk_score}")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"AI email analysis failed: {e}")
            # Return fallback analysis
            return self._create_fallback_analysis(email_data, str(e))
    
    async def analyze_link(self, url: str, context: str = "") -> AIThreatAnalysis:
        """Analyze link using AI threat intelligence"""
        try:
            # Sanitize inputs
            safe_url = self.content_filter.sanitize_for_ai(url, 500)
            safe_context = self.content_filter.sanitize_for_ai(context, 300)
            
            # Create analysis prompt
            analysis_prompt = f"""Analyze this URL for threats:

URL: {safe_url}
CONTEXT: {safe_context}

Focus on:
- Domain reputation and suspicious patterns
- URL structure and potential cloaking
- Shortened URL risks
- Context-based threat assessment

Provide threat analysis in JSON format."""

            # Generate session ID
            session_id = f"link_scan_{uuid.uuid4().hex[:12]}"
            
            # Initialize AI chat with modified system message for URL analysis
            url_system_message = self.system_message.replace("email content", "URLs and links")
            
            chat = LlmChat(
                api_key=self.api_key,
                session_id=session_id,
                system_message=url_system_message
            ).with_model("gemini", self.model_name).with_max_tokens(self.max_tokens)
            
            # Send message to AI
            user_message = UserMessage(text=analysis_prompt)
            ai_response = await chat.send_message(user_message)
            
            # Parse AI response
            link_data = {"url": url, "context": context}
            analysis_result = self._parse_ai_response(ai_response, link_data)
            
            # Store analysis
            await self._store_ai_analysis(analysis_result, link_data)
            
            logger.info(f"AI link analysis completed: risk_score={analysis_result.risk_score}")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"AI link analysis failed: {e}")
            return self._create_fallback_analysis({"url": url}, str(e))
    
    def _parse_ai_response(self, ai_response: str, original_data: Dict[str, Any]) -> AIThreatAnalysis:
        """Parse AI response and create threat analysis"""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                ai_json = json.loads(json_match.group())
            else:
                # Fallback parsing
                ai_json = self._extract_fallback_json(ai_response)
            
            # Extract content metadata
            content = original_data.get('email_body', original_data.get('url', ''))
            metadata = self.content_filter.extract_metadata(content)
            metadata.update({
                "ai_model": self.model_name,
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "response_length": len(ai_response)
            })
            
            return AIThreatAnalysis(
                risk_score=float(ai_json.get('risk_score', 50)),
                risk_level=ai_json.get('risk_level', 'potential_phishing'),
                threat_categories=ai_json.get('threat_categories', []),
                confidence=float(ai_json.get('confidence', 0.5)),
                explanation=ai_json.get('explanation', 'AI analysis completed'),
                ai_reasoning=ai_json.get('ai_reasoning', 'Detailed analysis not available'),
                detected_patterns=ai_json.get('detected_patterns', []),
                recommendations=ai_json.get('recommendations', ['Exercise caution']),
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Failed to parse AI response: {e}")
            return self._create_fallback_analysis(original_data, f"Parse error: {e}")
    
    def _extract_fallback_json(self, response: str) -> Dict[str, Any]:
        """Extract information from non-JSON AI response"""
        fallback = {
            "risk_score": 50,
            "risk_level": "potential_phishing",
            "threat_categories": [],
            "confidence": 0.5,
            "explanation": "AI analysis completed with partial parsing",
            "ai_reasoning": response[:500],
            "detected_patterns": [],
            "recommendations": ["Review email carefully", "Verify sender identity"]
        }
        
        # Extract risk indicators from text
        if any(word in response.lower() for word in ['phishing', 'malicious', 'dangerous']):
            fallback['risk_score'] = 75
            fallback['risk_level'] = 'phishing'
        elif any(word in response.lower() for word in ['suspicious', 'caution', 'potential']):
            fallback['risk_score'] = 45
            fallback['risk_level'] = 'potential_phishing'
        elif any(word in response.lower() for word in ['safe', 'legitimate', 'clean']):
            fallback['risk_score'] = 15
            fallback['risk_level'] = 'safe'
        
        return fallback
    
    def _create_fallback_analysis(self, data: Dict[str, Any], error: str) -> AIThreatAnalysis:
        """Create fallback analysis when AI fails"""
        return AIThreatAnalysis(
            risk_score=50.0,
            risk_level="potential_phishing",
            threat_categories=["unknown"],
            confidence=0.3,
            explanation="AI analysis unavailable - using fallback assessment",
            ai_reasoning=f"Error occurred: {error}",
            detected_patterns=["ai_error"],
            recommendations=[
                "AI analysis temporarily unavailable",
                "Use manual review for this content",
                "Exercise caution until analysis is restored"
            ],
            metadata={
                "fallback": True,
                "error": error,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    async def _store_ai_analysis(self, analysis: AIThreatAnalysis, original_data: Dict[str, Any]):
        """Store AI analysis results for learning and improvement"""
        try:
            db = get_database()
            
            analysis_record = {
                "id": str(uuid.uuid4()),
                "analysis_type": "ai_email_scan" if "email_subject" in original_data else "ai_link_scan",
                "risk_score": analysis.risk_score,
                "risk_level": analysis.risk_level,
                "threat_categories": analysis.threat_categories,
                "confidence": analysis.confidence,
                "ai_reasoning": analysis.ai_reasoning,
                "detected_patterns": analysis.detected_patterns,
                "metadata": analysis.metadata,
                "created_at": datetime.utcnow(),
                "model_used": self.model_name
            }
            
            await db.ai_analyses.insert_one(analysis_record)
            
        except Exception as e:
            logger.error(f"Failed to store AI analysis: {e}")

class AIEnhancedScanner:
    """Main scanner that combines AI with traditional methods"""
    
    def __init__(self):
        try:
            self.ai_scanner = GeminiAIScanner()
            self.ai_available = True
            logger.info("AI scanner initialized successfully")
        except Exception as e:
            logger.error(f"AI scanner initialization failed: {e}")
            self.ai_available = False
    
    async def scan_email_with_ai(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced email scanning with AI"""
        if not self.ai_available:
            return self._fallback_scan(email_data)
        
        try:
            # Use AI analysis
            ai_analysis = await self.ai_scanner.analyze_email_content(email_data)
            
            # Convert to response format
            return {
                'risk_score': ai_analysis.risk_score,
                'risk_level': ai_analysis.risk_level,
                'explanation': ai_analysis.explanation,
                'recommendations': ai_analysis.recommendations,
                'threat_indicators': [
                    {
                        'source': 'ai_analysis',
                        'threat_type': category,
                        'confidence': ai_analysis.confidence,
                        'description': f'AI detected {category}',
                        'evidence': pattern
                    }
                    for category, pattern in zip(
                        ai_analysis.threat_categories,
                        ai_analysis.detected_patterns
                    )
                ],
                'metadata': {
                    'ai_powered': True,
                    'ai_reasoning': ai_analysis.ai_reasoning,
                    'ai_confidence': ai_analysis.confidence,
                    **ai_analysis.metadata
                },
                'scan_duration': 0.5  # Placeholder
            }
            
        except Exception as e:
            logger.error(f"AI email scanning failed: {e}")
            return self._fallback_scan(email_data)
    
    async def scan_link_with_ai(self, url: str, context: str = "") -> Dict[str, Any]:
        """Enhanced link scanning with AI"""
        if not self.ai_available:
            return self._fallback_link_scan(url)
        
        try:
            # Use AI analysis
            ai_analysis = await self.ai_scanner.analyze_link(url, context)
            
            # Convert to response format
            return {
                'risk_score': ai_analysis.risk_score,
                'risk_level': ai_analysis.risk_level,
                'explanation': ai_analysis.explanation,
                'recommendations': ai_analysis.recommendations,
                'threat_indicators': [
                    {
                        'source': 'ai_analysis',
                        'threat_type': category,
                        'confidence': ai_analysis.confidence,
                        'description': f'AI detected {category} in URL',
                        'evidence': pattern
                    }
                    for category, pattern in zip(
                        ai_analysis.threat_categories,
                        ai_analysis.detected_patterns
                    )
                ],
                'metadata': {
                    'ai_powered': True,
                    'ai_reasoning': ai_analysis.ai_reasoning,
                    'ai_confidence': ai_analysis.confidence,
                    **ai_analysis.metadata
                },
                'scan_duration': 0.5
            }
            
        except Exception as e:
            logger.error(f"AI link scanning failed: {e}")
            return self._fallback_link_scan(url)
    
    def _fallback_scan(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback to traditional scanning when AI unavailable"""
        # Import existing scanner
        from email_scanner import scan_email_advanced
        return scan_email_advanced(email_data)
    
    def _fallback_link_scan(self, url: str) -> Dict[str, Any]:
        """Fallback link scanning"""
        from email_scanner import scan_link_advanced
        return scan_link_advanced(url)

# Global AI scanner instance
ai_enhanced_scanner = AIEnhancedScanner()

async def scan_email_with_ai(email_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    AI-enhanced email scanning function for API integration
    
    Args:
        email_data: Email data dictionary
        
    Returns:
        Enhanced scan results with AI analysis
    """
    return await ai_enhanced_scanner.scan_email_with_ai(email_data)

async def scan_link_with_ai(url: str, context: str = "") -> Dict[str, Any]:
    """
    AI-enhanced link scanning function for API integration
    
    Args:
        url: URL to analyze
        context: Optional context
        
    Returns:
        Enhanced link analysis with AI
    """
    return await ai_enhanced_scanner.scan_link_with_ai(url, context)