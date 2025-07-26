"""
Advanced Email Scanning Core Logic for Aman Cybersecurity Platform
Implements sophisticated content analysis, threat detection, and risk scoring
"""

import re
import json
import hashlib
import ipaddress
import urllib.parse
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from enum import Enum

# Configure logging
logger = logging.getLogger(__name__)

class ThreatSource(Enum):
    BODY = "body"
    LINK = "link"
    IMAGE = "image"
    FILE = "file"
    SENDER = "sender"
    SUBJECT = "subject"

class ThreatType(Enum):
    PHISHING = "phishing"
    MALWARE = "malware"
    SPAM = "spam"
    SCAM = "scam"
    CREDENTIAL_HARVESTING = "credential_harvesting"
    BUSINESS_EMAIL_COMPROMISE = "business_email_compromise"
    SOCIAL_ENGINEERING = "social_engineering"

@dataclass
class ThreatIndicator:
    source: ThreatSource
    threat_type: ThreatType
    confidence: float  # 0.0 to 1.0
    description: str
    evidence: str

@dataclass
class ScanResult:
    overall_risk_score: float
    risk_level: str  # "safe", "potential_phishing", "phishing"
    threat_indicators: List[ThreatIndicator]
    explanation: str
    recommendations: List[str]
    scan_duration: float
    metadata: Dict[str, Any]

class AdvancedEmailScanner:
    """Advanced email scanning with sophisticated threat detection algorithms"""
    
    def __init__(self):
        self.suspicious_keywords = self._load_suspicious_keywords()
        self.malicious_domains = self._load_malicious_domains()
        self.legitimate_domains = self._load_legitimate_domains()
        self.phishing_patterns = self._compile_phishing_patterns()
        self.social_engineering_patterns = self._compile_social_engineering_patterns()
        
    def _load_suspicious_keywords(self) -> Dict[str, Dict[str, float]]:
        """Load categorized suspicious keywords with weight scores"""
        return {
            "urgency": {
                "urgent": 0.7, "immediately": 0.8, "expires today": 0.9,
                "expires soon": 0.6, "time sensitive": 0.6, "act now": 0.8,
                "deadline": 0.5, "limited time": 0.7, "expires in": 0.6,
                "final notice": 0.9, "last chance": 0.8, "immediate action": 0.9
            },
            "credential_requests": {
                "verify account": 0.9, "confirm identity": 0.8, "update password": 0.7,
                "login credentials": 0.9, "account suspended": 0.9, "verify identity": 0.8,
                "confirm details": 0.7, "update information": 0.6, "verify email": 0.5,
                "account verification": 0.8, "identity verification": 0.8
            },
            "financial": {
                "claim prize": 0.9, "lottery winner": 0.9, "inheritance": 0.8,
                "tax refund": 0.7, "bonus payment": 0.6, "wire transfer": 0.8,
                "bank account": 0.6, "payment required": 0.7, "billing issue": 0.5,
                "refund available": 0.6, "credit card": 0.4, "payment method": 0.4
            },
            "social_engineering": {
                "help me": 0.6, "confidential": 0.5, "personal favor": 0.7,
                "don't tell anyone": 0.8, "between us": 0.7, "secret": 0.6,
                "trust me": 0.7, "just between you and me": 0.8, "keep this quiet": 0.8
            },
            "threats": {
                "account will be closed": 0.8, "legal action": 0.7, "suspended": 0.8,
                "terminated": 0.7, "blocked": 0.6, "consequences": 0.6,
                "penalty": 0.6, "legal consequences": 0.8, "court action": 0.9
            }
        }
    
    def _load_malicious_domains(self) -> List[str]:
        """Load known malicious domains"""
        return [
            # Known phishing domains
            "secure-bank-update.com", "paypal-verification.net", "amazon-security.org",
            "microsoft-support.info", "google-security.co", "apple-id-verification.com",
            "banking-secure.net", "account-verification.info", "security-update.org",
            
            # Suspicious TLDs and patterns
            "bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "short.link",
            
            # Generic suspicious patterns (will be checked with regex)
            r".*-security\..*", r".*-verification\..*", r".*-update\..*",
            r".*-support\..*", r"secure-.*\..*", r"verify-.*\..*"
        ]
    
    def _load_legitimate_domains(self) -> List[str]:
        """Load known legitimate domains"""
        return [
            "google.com", "microsoft.com", "apple.com", "amazon.com", "paypal.com",
            "facebook.com", "twitter.com", "linkedin.com", "github.com", "stackoverflow.com",
            "gmail.com", "outlook.com", "yahoo.com", "hotmail.com", "icloud.com",
            "salesforce.com", "slack.com", "zoom.us", "dropbox.com", "adobe.com"
        ]
    
    def _compile_phishing_patterns(self) -> List[re.Pattern]:
        """Compile regex patterns for phishing detection"""
        patterns = [
            # Credential harvesting patterns
            r"click\s+here\s+to\s+(verify|update|confirm)",
            r"(login|sign\s+in)\s+to\s+(verify|update|confirm)",
            r"your\s+(account|password)\s+(has\s+been\s+)?(suspended|locked|compromised)",
            r"verify\s+your\s+(identity|account|email|information)",
            r"update\s+your\s+(payment|billing|account)\s+information",
            
            # Urgency patterns
            r"(expires?|expire)\s+(today|soon|in\s+\d+\s+(hours?|days?))",
            r"immediate(ly)?\s+(action|response|verification)\s+required",
            r"your\s+account\s+will\s+be\s+(closed|suspended|terminated)",
            
            # Suspicious links
            r"click\s+(here|this\s+link)\s+to\s+",
            r"http[s]?://[^\s]+\.(tk|ml|cf|ga|bit\.ly|tinyurl\.com)",
            
            # Social engineering
            r"(don't|do\s+not)\s+(tell|share|forward)",
            r"(confidential|secret|private)\s+(information|message|request)",
            r"help\s+me\s+(transfer|move|access)\s+",
            
            # Financial scams
            r"you\s+(have\s+)?(won|inherited)\s+",
            r"(claim|collect)\s+your\s+(prize|reward|inheritance)",
            r"transfer\s+\$?\d+([,.]?\d+)*\s+(million|thousand|dollars?)"
        ]
        
        return [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
    
    def _compile_social_engineering_patterns(self) -> List[re.Pattern]:
        """Compile patterns for social engineering detection"""
        patterns = [
            r"(ceo|president|manager|director)\s+(is\s+)?(traveling|away|unavailable)",
            r"urgent\s+(wire\s+)?transfer\s+needed",
            r"change\s+(of|in)\s+(banking|payment|vendor)\s+details",
            r"invoice\s+(payment|amount)\s+(has\s+)?changed",
            r"new\s+(banking|account)\s+(details|information)",
            r"please\s+(wire|transfer|send)\s+funds?\s+to",
            r"tax\s+(id|number|information)\s+(required|needed|update)",
            r"w-?9\s+(form|tax\s+form|information)\s+(required|needed)"
        ]
        
        return [re.compile(pattern, re.IGNORECASE) for pattern in patterns]

    def scan_email(self, email_data: Dict[str, Any]) -> ScanResult:
        """
        Comprehensive email scanning with advanced threat detection
        
        Args:
            email_data: Dictionary containing email fields
            
        Returns:
            ScanResult with detailed analysis
        """
        start_time = datetime.now()
        threat_indicators = []
        
        # Extract email components
        subject = email_data.get('email_subject', '')
        body = email_data.get('email_body', '')
        sender = email_data.get('sender', '')
        recipient = email_data.get('recipient', '')
        
        # Analyze each component
        threat_indicators.extend(self._analyze_subject(subject))
        threat_indicators.extend(self._analyze_body(body))
        threat_indicators.extend(self._analyze_sender(sender))
        threat_indicators.extend(self._analyze_links(body))
        
        # Calculate overall risk score
        overall_risk_score = self._calculate_risk_score(threat_indicators)
        risk_level = self._determine_risk_level(overall_risk_score)
        
        # Generate explanation and recommendations
        explanation = self._generate_explanation(threat_indicators, risk_level)
        recommendations = self._generate_recommendations(threat_indicators, risk_level)
        
        # Calculate scan duration
        scan_duration = (datetime.now() - start_time).total_seconds()
        
        # Prepare metadata
        metadata = {
            'scan_timestamp': start_time.isoformat(),
            'email_length': len(body),
            'link_count': len(re.findall(r'http[s]?://[^\s]+', body)),
            'subject_length': len(subject),
            'sender_domain': self._extract_domain(sender),
            'threat_count': len(threat_indicators)
        }
        
        return ScanResult(
            overall_risk_score=overall_risk_score,
            risk_level=risk_level,
            threat_indicators=threat_indicators,
            explanation=explanation,
            recommendations=recommendations,
            scan_duration=scan_duration,
            metadata=metadata
        )
    
    def _analyze_subject(self, subject: str) -> List[ThreatIndicator]:
        """Analyze email subject for threats"""
        indicators = []
        
        if not subject:
            return indicators
        
        # Check for suspicious keywords
        for category, keywords in self.suspicious_keywords.items():
            for keyword, weight in keywords.items():
                if keyword.lower() in subject.lower():
                    indicators.append(ThreatIndicator(
                        source=ThreatSource.SUBJECT,
                        threat_type=self._map_category_to_threat_type(category),
                        confidence=weight,
                        description=f"Suspicious keyword in subject: '{keyword}'",
                        evidence=f"Subject contains: '{keyword}'"
                    ))
        
        # Check for excessive urgency markers
        urgency_markers = ['!', 'urgent', 'asap', 'immediately']
        urgency_count = sum(subject.lower().count(marker) for marker in urgency_markers)
        if urgency_count >= 3:
            indicators.append(ThreatIndicator(
                source=ThreatSource.SUBJECT,
                threat_type=ThreatType.SOCIAL_ENGINEERING,
                confidence=0.7,
                description="Excessive urgency markers in subject",
                evidence=f"Found {urgency_count} urgency markers"
            ))
        
        # Check for all caps (potential shouting/urgency)
        if len(subject) > 10 and subject.isupper():
            indicators.append(ThreatIndicator(
                source=ThreatSource.SUBJECT,
                threat_type=ThreatType.SOCIAL_ENGINEERING,
                confidence=0.4,
                description="Subject in all caps (urgency manipulation)",
                evidence="Subject line entirely in uppercase"
            ))
        
        return indicators
    
    def _analyze_body(self, body: str) -> List[ThreatIndicator]:
        """Analyze email body content for threats"""
        indicators = []
        
        if not body:
            return indicators
        
        # Check suspicious keywords by category
        for category, keywords in self.suspicious_keywords.items():
            for keyword, weight in keywords.items():
                if keyword.lower() in body.lower():
                    indicators.append(ThreatIndicator(
                        source=ThreatSource.BODY,
                        threat_type=self._map_category_to_threat_type(category),
                        confidence=weight,
                        description=f"Suspicious content: {category}",
                        evidence=f"Contains: '{keyword}'"
                    ))
        
        # Check phishing patterns
        for pattern in self.phishing_patterns:
            matches = pattern.findall(body)
            if matches:
                indicators.append(ThreatIndicator(
                    source=ThreatSource.BODY,
                    threat_type=ThreatType.PHISHING,
                    confidence=0.8,
                    description="Phishing pattern detected",
                    evidence=f"Pattern match: {matches[0] if matches else 'detected'}"
                ))
        
        # Check social engineering patterns
        for pattern in self.social_engineering_patterns:
            matches = pattern.findall(body)
            if matches:
                indicators.append(ThreatIndicator(
                    source=ThreatSource.BODY,
                    threat_type=ThreatType.BUSINESS_EMAIL_COMPROMISE,
                    confidence=0.9,
                    description="Business Email Compromise (BEC) pattern",
                    evidence=f"BEC pattern: {matches[0] if matches else 'detected'}"
                ))
        
        # Check for suspicious financial requests
        financial_patterns = [
            r'\$[\d,]+(?:\.\d{2})?', r'bitcoin', r'cryptocurrency', r'wire transfer',
            r'western union', r'moneygram', r'gift card', r'prepaid card'
        ]
        
        for pattern in financial_patterns:
            if re.search(pattern, body, re.IGNORECASE):
                indicators.append(ThreatIndicator(
                    source=ThreatSource.BODY,
                    threat_type=ThreatType.SCAM,
                    confidence=0.6,
                    description="Financial request detected",
                    evidence=f"Financial pattern: {pattern}"
                ))
        
        # Check for grammar and spelling issues (common in phishing)
        grammar_score = self._assess_grammar_quality(body)
        if grammar_score < 0.3:  # Poor grammar
            indicators.append(ThreatIndicator(
                source=ThreatSource.BODY,
                threat_type=ThreatType.PHISHING,
                confidence=0.3,
                description="Poor grammar and spelling",
                evidence=f"Grammar quality score: {grammar_score:.2f}"
            ))
        
        return indicators
    
    def _analyze_sender(self, sender: str) -> List[ThreatIndicator]:
        """Analyze sender information for threats"""
        indicators = []
        
        if not sender:
            return indicators
        
        domain = self._extract_domain(sender)
        
        # Check against known malicious domains
        for malicious_domain in self.malicious_domains:
            if malicious_domain.startswith('r"') and malicious_domain.endswith('"'):
                # Regex pattern
                pattern = malicious_domain[2:-1]  # Remove r" and "
                if re.search(pattern, domain):
                    indicators.append(ThreatIndicator(
                        source=ThreatSource.SENDER,
                        threat_type=ThreatType.PHISHING,
                        confidence=0.9,
                        description="Sender from suspicious domain",
                        evidence=f"Domain: {domain}"
                    ))
            elif domain and malicious_domain in domain:
                indicators.append(ThreatIndicator(
                    source=ThreatSource.SENDER,
                    threat_type=ThreatType.PHISHING,
                    confidence=0.8,
                    description="Sender from known malicious domain",
                    evidence=f"Domain: {domain}"
                ))
        
        # Check for domain spoofing
        spoofing_score = self._check_domain_spoofing(domain)
        if spoofing_score > 0.5:
            indicators.append(ThreatIndicator(
                source=ThreatSource.SENDER,
                threat_type=ThreatType.PHISHING,
                confidence=spoofing_score,
                description="Potential domain spoofing",
                evidence=f"Suspicious domain: {domain}"
            ))
        
        # Check for suspicious TLDs
        suspicious_tlds = ['.tk', '.ml', '.cf', '.ga', '.pw', '.top', '.click']
        if any(domain.endswith(tld) for tld in suspicious_tlds):
            indicators.append(ThreatIndicator(
                source=ThreatSource.SENDER,
                threat_type=ThreatType.PHISHING,
                confidence=0.6,
                description="Sender from suspicious TLD",
                evidence=f"Domain: {domain}"
            ))
        
        return indicators
    
    def _analyze_links(self, body: str) -> List[ThreatIndicator]:
        """Analyze links in email body for threats"""
        indicators = []
        
        # Extract all URLs
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        urls = re.findall(url_pattern, body)
        
        for url in urls:
            link_indicators = self._analyze_single_link(url)
            indicators.extend(link_indicators)
        
        return indicators
    
    def _analyze_single_link(self, url: str) -> List[ThreatIndicator]:
        """Analyze a single link for threats"""
        indicators = []
        
        try:
            parsed_url = urllib.parse.urlparse(url)
            domain = parsed_url.netloc.lower()
            
            # Check shortened URLs
            shortener_domains = ['bit.ly', 'tinyurl.com', 't.co', 'goo.gl', 'ow.ly', 'short.link']
            if any(shortener in domain for shortener in shortener_domains):
                indicators.append(ThreatIndicator(
                    source=ThreatSource.LINK,
                    threat_type=ThreatType.PHISHING,
                    confidence=0.7,
                    description="Shortened URL detected",
                    evidence=f"Shortened URL: {url}"
                ))
            
            # Check suspicious domains
            for malicious_domain in self.malicious_domains:
                if malicious_domain in domain:
                    indicators.append(ThreatIndicator(
                        source=ThreatSource.LINK,
                        threat_type=ThreatType.PHISHING,
                        confidence=0.9,
                        description="Link to malicious domain",
                        evidence=f"Malicious URL: {url}"
                    ))
            
            # Check for URL cloaking/redirection
            if self._is_url_cloaked(url):
                indicators.append(ThreatIndicator(
                    source=ThreatSource.LINK,
                    threat_type=ThreatType.PHISHING,
                    confidence=0.6,
                    description="Potentially cloaked URL",
                    evidence=f"Suspicious URL structure: {url}"
                ))
            
            # Check for suspicious URL patterns
            suspicious_patterns = [
                r'secure.*login', r'verify.*account', r'update.*payment',
                r'confirm.*identity', r'account.*suspended'
            ]
            
            for pattern in suspicious_patterns:
                if re.search(pattern, url, re.IGNORECASE):
                    indicators.append(ThreatIndicator(
                        source=ThreatSource.LINK,
                        threat_type=ThreatType.PHISHING,
                        confidence=0.7,
                        description="Suspicious URL pattern",
                        evidence=f"Pattern in URL: {pattern}"
                    ))
        
        except Exception as e:
            logger.warning(f"Error analyzing URL {url}: {e}")
        
        return indicators
    
    def _calculate_risk_score(self, threat_indicators: List[ThreatIndicator]) -> float:
        """Calculate overall risk score from threat indicators"""
        if not threat_indicators:
            return 0.0
        
        # Weight factors for different threat types
        threat_weights = {
            ThreatType.PHISHING: 1.0,
            ThreatType.BUSINESS_EMAIL_COMPROMISE: 1.2,
            ThreatType.CREDENTIAL_HARVESTING: 1.1,
            ThreatType.MALWARE: 1.1,
            ThreatType.SCAM: 0.9,
            ThreatType.SOCIAL_ENGINEERING: 0.8,
            ThreatType.SPAM: 0.3
        }
        
        # Calculate weighted score
        total_score = 0.0
        max_possible_score = 0.0
        
        for indicator in threat_indicators:
            weight = threat_weights.get(indicator.threat_type, 0.5)
            weighted_confidence = indicator.confidence * weight
            total_score += weighted_confidence
            max_possible_score += weight
        
        # Normalize to 0-100 scale
        if max_possible_score > 0:
            normalized_score = (total_score / max_possible_score) * 100
        else:
            normalized_score = 0.0
        
        # Apply diminishing returns to prevent over-scoring
        if normalized_score > 50:
            normalized_score = 50 + (normalized_score - 50) * 0.7
        
        return min(normalized_score, 100.0)
    
    def _determine_risk_level(self, risk_score: float) -> str:
        """Determine risk level based on score"""
        if risk_score >= 70:
            return "phishing"
        elif risk_score >= 30:
            return "potential_phishing"
        else:
            return "safe"
    
    def _generate_explanation(self, threat_indicators: List[ThreatIndicator], risk_level: str) -> str:
        """Generate human-readable explanation of the analysis"""
        if not threat_indicators:
            return "No significant threats detected. Email appears to be legitimate."
        
        # Count threats by type
        threat_counts = {}
        for indicator in threat_indicators:
            threat_type = indicator.threat_type.value
            threat_counts[threat_type] = threat_counts.get(threat_type, 0) + 1
        
        # Generate explanation based on primary threats
        primary_threats = sorted(threat_counts.items(), key=lambda x: x[1], reverse=True)
        
        if risk_level == "phishing":
            explanation = "High-risk phishing attempt detected. "
        elif risk_level == "potential_phishing":
            explanation = "Potentially suspicious email with concerning elements. "
        else:
            explanation = "Low-risk email with minor suspicious indicators. "
        
        # Add details about specific threats
        threat_details = []
        for threat_type, count in primary_threats[:3]:  # Top 3 threats
            if count > 1:
                threat_details.append(f"{count} {threat_type.replace('_', ' ')} indicators")
            else:
                threat_details.append(f"{threat_type.replace('_', ' ')} pattern")
        
        if threat_details:
            explanation += f"Found: {', '.join(threat_details)}."
        
        return explanation
    
    def _generate_recommendations(self, threat_indicators: List[ThreatIndicator], risk_level: str) -> List[str]:
        """Generate security recommendations based on analysis"""
        recommendations = []
        
        if risk_level == "phishing":
            recommendations.extend([
                "Do not click any links in this email",
                "Do not download or open any attachments",
                "Do not provide any personal or financial information",
                "Report this email as phishing to your IT security team",
                "Delete this email immediately"
            ])
        elif risk_level == "potential_phishing":
            recommendations.extend([
                "Exercise caution with this email",
                "Verify sender identity through alternative communication method",
                "Do not click suspicious links or download unexpected attachments",
                "Check sender's email address carefully for spoofing",
                "When in doubt, contact your IT security team"
            ])
        else:
            recommendations.extend([
                "Email appears safe but remain vigilant",
                "Verify any unexpected requests through alternative channels",
                "Be cautious with links and attachments from unknown senders"
            ])
        
        # Add specific recommendations based on threat types
        threat_types = {indicator.threat_type for indicator in threat_indicators}
        
        if ThreatType.CREDENTIAL_HARVESTING in threat_types:
            recommendations.append("Never enter login credentials through email links")
        
        if ThreatType.BUSINESS_EMAIL_COMPROMISE in threat_types:
            recommendations.append("Verify financial requests through known contact information")
        
        if ThreatSource.LINK in {indicator.source for indicator in threat_indicators}:
            recommendations.append("Hover over links to preview destinations before clicking")
        
        return recommendations[:6]  # Limit to 6 recommendations
    
    # Helper methods
    def _extract_domain(self, email: str) -> str:
        """Extract domain from email address"""
        if '@' in email:
            return email.split('@')[-1].lower()
        return email.lower()
    
    def _map_category_to_threat_type(self, category: str) -> ThreatType:
        """Map keyword category to threat type"""
        mapping = {
            "urgency": ThreatType.SOCIAL_ENGINEERING,
            "credential_requests": ThreatType.CREDENTIAL_HARVESTING,
            "financial": ThreatType.SCAM,
            "social_engineering": ThreatType.SOCIAL_ENGINEERING,
            "threats": ThreatType.PHISHING
        }
        return mapping.get(category, ThreatType.PHISHING)
    
    def _check_domain_spoofing(self, domain: str) -> float:
        """Check for domain spoofing against legitimate domains"""
        if not domain:
            return 0.0
        
        spoofing_score = 0.0
        
        for legit_domain in self.legitimate_domains:
            similarity = self._calculate_string_similarity(domain, legit_domain)
            if 0.6 <= similarity < 1.0:  # Similar but not exact
                spoofing_score = max(spoofing_score, similarity)
        
        return spoofing_score
    
    def _calculate_string_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity between two strings using Levenshtein distance"""
        if not str1 or not str2:
            return 0.0
        
        len1, len2 = len(str1), len(str2)
        if len1 == 0: return len2
        if len2 == 0: return len1
        
        # Create matrix
        matrix = [[0] * (len2 + 1) for _ in range(len1 + 1)]
        
        # Initialize first row and column
        for i in range(len1 + 1):
            matrix[i][0] = i
        for j in range(len2 + 1):
            matrix[0][j] = j
        
        # Fill matrix
        for i in range(1, len1 + 1):
            for j in range(1, len2 + 1):
                if str1[i-1] == str2[j-1]:
                    cost = 0
                else:
                    cost = 1
                
                matrix[i][j] = min(
                    matrix[i-1][j] + 1,      # deletion
                    matrix[i][j-1] + 1,      # insertion
                    matrix[i-1][j-1] + cost  # substitution
                )
        
        # Calculate similarity
        max_len = max(len1, len2)
        distance = matrix[len1][len2]
        similarity = (max_len - distance) / max_len
        
        return similarity
    
    def _assess_grammar_quality(self, text: str) -> float:
        """Assess grammar quality of text (simplified implementation)"""
        if not text:
            return 1.0
        
        # Simple heuristics for grammar assessment
        sentences = re.split(r'[.!?]+', text)
        if not sentences:
            return 0.5
        
        issues = 0
        total_checks = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 3:
                continue
            
            total_checks += 1
            
            # Check for basic issues
            if not sentence[0].isupper():  # Should start with capital
                issues += 1
            
            # Check for excessive repetition
            words = sentence.split()
            if len(words) != len(set(word.lower() for word in words)):
                issues += 1
            
            # Check for suspicious patterns
            if re.search(r'[a-z][A-Z]', sentence):  # Mixed case within words
                issues += 1
        
        if total_checks == 0:
            return 0.5
        
        quality_score = 1.0 - (issues / total_checks)
        return max(0.0, quality_score)
    
    def _is_url_cloaked(self, url: str) -> bool:
        """Check if URL appears to be cloaked or suspicious"""
        try:
            parsed = urllib.parse.urlparse(url)
            
            # Check for suspicious URL patterns
            suspicious_patterns = [
                len(parsed.netloc) > 50,  # Very long domain
                parsed.netloc.count('-') > 3,  # Many hyphens
                parsed.netloc.count('.') > 5,  # Many subdomains
                bool(re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', parsed.netloc)),  # IP address
                len(parsed.query) > 100,  # Very long query string
                parsed.fragment and len(parsed.fragment) > 50  # Long fragment
            ]
            
            return sum(suspicious_patterns) >= 2
        
        except Exception:
            return True  # If we can't parse it, consider it suspicious

class LinkScanner:
    """Advanced link scanning and analysis"""
    
    def __init__(self):
        self.scanner = AdvancedEmailScanner()
    
    def scan_link(self, url: str, context: str = "") -> ScanResult:
        """
        Scan a single link for threats
        
        Args:
            url: The URL to scan
            context: Optional context where the link was found
            
        Returns:
            ScanResult with link analysis
        """
        start_time = datetime.now()
        threat_indicators = []
        
        # Analyze the link
        threat_indicators.extend(self.scanner._analyze_single_link(url))
        
        # Add context-based analysis if provided
        if context:
            if any(keyword in context.lower() for keyword in ['click here', 'urgent', 'verify']):
                threat_indicators.append(ThreatIndicator(
                    source=ThreatSource.LINK,
                    threat_type=ThreatType.PHISHING,
                    confidence=0.6,
                    description="Suspicious link context",
                    evidence=f"Context: {context[:100]}"
                ))
        
        # Calculate risk score
        overall_risk_score = self.scanner._calculate_risk_score(threat_indicators)
        risk_level = self.scanner._determine_risk_level(overall_risk_score)
        
        # Generate explanation and recommendations
        explanation = self._generate_link_explanation(url, threat_indicators, risk_level)
        recommendations = self._generate_link_recommendations(threat_indicators, risk_level)
        
        # Calculate scan duration
        scan_duration = (datetime.now() - start_time).total_seconds()
        
        # Prepare metadata
        try:
            parsed_url = urllib.parse.urlparse(url)
            metadata = {
                'scan_timestamp': start_time.isoformat(),
                'url_length': len(url),
                'domain': parsed_url.netloc,
                'scheme': parsed_url.scheme,
                'has_query': bool(parsed_url.query),
                'has_fragment': bool(parsed_url.fragment),
                'threat_count': len(threat_indicators)
            }
        except Exception:
            metadata = {
                'scan_timestamp': start_time.isoformat(),
                'url_length': len(url),
                'threat_count': len(threat_indicators)
            }
        
        return ScanResult(
            overall_risk_score=overall_risk_score,
            risk_level=risk_level,
            threat_indicators=threat_indicators,
            explanation=explanation,
            recommendations=recommendations,
            scan_duration=scan_duration,
            metadata=metadata
        )
    
    def _generate_link_explanation(self, url: str, threat_indicators: List[ThreatIndicator], risk_level: str) -> str:
        """Generate explanation for link analysis"""
        if not threat_indicators:
            return f"Link appears safe. No significant threats detected in: {url[:50]}..."
        
        if risk_level == "phishing":
            explanation = "High-risk malicious link detected. "
        elif risk_level == "potential_phishing":
            explanation = "Potentially suspicious link with concerning elements. "
        else:
            explanation = "Link has minor suspicious indicators. "
        
        # Add specific threat details
        threat_sources = {indicator.source for indicator in threat_indicators}
        
        details = []
        if ThreatSource.LINK in threat_sources:
            details.append("suspicious URL structure")
        
        threat_types = {indicator.threat_type for indicator in threat_indicators}
        if ThreatType.PHISHING in threat_types:
            details.append("phishing patterns")
        
        if details:
            explanation += f"Issues found: {', '.join(details)}."
        
        return explanation
    
    def _generate_link_recommendations(self, threat_indicators: List[ThreatIndicator], risk_level: str) -> List[str]:
        """Generate recommendations for link analysis"""
        if risk_level == "phishing":
            return [
                "Do not click this link",
                "This link may lead to a malicious website",
                "Report this link to your security team",
                "Block this domain if possible"
            ]
        elif risk_level == "potential_phishing":
            return [
                "Exercise caution before clicking",
                "Verify the link destination manually",
                "Consider using a link scanner service",
                "Check the domain reputation"
            ]
        else:
            return [
                "Link appears safe but remain cautious",
                "Verify unexpected links from unknown sources",
                "Check the URL destination before clicking"
            ]

# Global scanner instances
email_scanner = AdvancedEmailScanner()
link_scanner = LinkScanner()

def scan_email_advanced(email_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Advanced email scanning function for API integration
    
    Args:
        email_data: Email data dictionary
        
    Returns:
        Scan results dictionary
    """
    try:
        result = email_scanner.scan_email(email_data)
        
        return {
            'risk_score': result.overall_risk_score,
            'risk_level': result.risk_level,
            'explanation': result.explanation,
            'recommendations': result.recommendations,
            'threat_indicators': [
                {
                    'source': indicator.source.value,
                    'threat_type': indicator.threat_type.value,
                    'confidence': indicator.confidence,
                    'description': indicator.description,
                    'evidence': indicator.evidence
                }
                for indicator in result.threat_indicators
            ],
            'metadata': result.metadata,
            'scan_duration': result.scan_duration
        }
    
    except Exception as e:
        logger.error(f"Error in advanced email scanning: {e}")
        return {
            'risk_score': 50.0,
            'risk_level': 'potential_phishing',
            'explanation': 'Error occurred during scanning. Please try again.',
            'recommendations': ['Unable to complete scan', 'Exercise caution'],
            'threat_indicators': [],
            'metadata': {'error': str(e)},
            'scan_duration': 0.0
        }

def scan_link_advanced(url: str, context: str = "") -> Dict[str, Any]:
    """
    Advanced link scanning function for API integration
    
    Args:
        url: URL to scan
        context: Optional context
        
    Returns:
        Scan results dictionary
    """
    try:
        result = link_scanner.scan_link(url, context)
        
        return {
            'url': url,
            'risk_score': result.overall_risk_score,
            'risk_level': result.risk_level,
            'explanation': result.explanation,
            'recommendations': result.recommendations,
            'threat_indicators': [
                {
                    'source': indicator.source.value,
                    'threat_type': indicator.threat_type.value,
                    'confidence': indicator.confidence,
                    'description': indicator.description,
                    'evidence': indicator.evidence
                }
                for indicator in result.threat_indicators
            ],
            'metadata': result.metadata,
            'scan_duration': result.scan_duration
        }
    
    except Exception as e:
        logger.error(f"Error in advanced link scanning: {e}")
        return {
            'url': url,
            'risk_score': 50.0,
            'risk_level': 'potential_phishing',
            'explanation': 'Error occurred during link scanning. Please try again.',
            'recommendations': ['Unable to complete scan', 'Exercise caution'],
            'threat_indicators': [],
            'metadata': {'error': str(e)},
            'scan_duration': 0.0
        }