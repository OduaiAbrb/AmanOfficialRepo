"""
Threat Intelligence System for Aman Cybersecurity Platform
Provides real-time threat intelligence for enhanced security analysis
"""

import asyncio
import aiohttp
import hashlib
import time
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta
from enum import Enum
import logging
import re
import ipaddress
from dataclasses import dataclass
from database import get_database
import uuid

logger = logging.getLogger(__name__)

class ThreatCategory(Enum):
    MALWARE = "malware"
    PHISHING = "phishing"
    SPAM = "spam"
    BOTNET = "botnet"
    RANSOMWARE = "ransomware"
    CRYPTOMINING = "cryptomining"
    SUSPICIOUS = "suspicious"
    SAFE = "safe"

class ThreatSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"

@dataclass
class ThreatIntelligenceEntry:
    domain: str
    ip_address: Optional[str]
    category: ThreatCategory
    severity: ThreatSeverity
    confidence: float  # 0.0 to 1.0
    source: str
    description: str
    first_seen: datetime
    last_seen: datetime
    indicators: List[str]
    metadata: Dict[str, Any]

class ThreatIntelligenceProvider:
    """Base class for threat intelligence providers"""
    
    def __init__(self, name: str, api_key: Optional[str] = None):
        self.name = name
        self.api_key = api_key
        self.rate_limit = 100  # requests per minute
        self.last_request_time = 0
        self.request_count = 0
        self.request_window_start = time.time()
    
    async def check_rate_limit(self) -> bool:
        """Check if we're within rate limits"""
        current_time = time.time()
        
        # Reset counter if minute has passed
        if current_time - self.request_window_start > 60:
            self.request_count = 0
            self.request_window_start = current_time
        
        if self.request_count >= self.rate_limit:
            return False
        
        self.request_count += 1
        return True
    
    async def lookup_domain(self, domain: str) -> Optional[ThreatIntelligenceEntry]:
        """Lookup threat intelligence for a domain"""
        raise NotImplementedError
    
    async def lookup_url(self, url: str) -> Optional[ThreatIntelligenceEntry]:
        """Lookup threat intelligence for a URL"""
        raise NotImplementedError
    
    async def lookup_ip(self, ip: str) -> Optional[ThreatIntelligenceEntry]:
        """Lookup threat intelligence for an IP address"""
        raise NotImplementedError

class LocalThreatIntelligence(ThreatIntelligenceProvider):
    """Local threat intelligence using curated lists and patterns"""
    
    def __init__(self):
        super().__init__("local_intelligence")
        self.known_malicious_domains = self._load_malicious_domains()
        self.known_safe_domains = self._load_safe_domains()
        self.suspicious_patterns = self._load_suspicious_patterns()
        self.threat_ip_ranges = self._load_threat_ip_ranges()
    
    def _load_malicious_domains(self) -> Set[str]:
        """Load known malicious domains"""
        return {
            # Known phishing domains
            "phishing-bank.com", "fake-paypal.net", "amazon-verify.org",
            "microsoft-security.info", "google-alert.co", "apple-support.net",
            "secure-banking.org", "account-update.info", "verify-account.net",
            
            # Malware distribution
            "malware-host.com", "trojan-download.net", "virus-site.org",
            "infected-files.com", "malicious-payload.net",
            
            # Spam domains
            "cheap-meds.org", "quick-money.net", "work-from-home.biz",
            "lottery-winner.com", "inheritance-claim.net",
            
            # Cryptocurrency scams
            "crypto-doubler.com", "bitcoin-giveaway.net", "invest-crypto.org",
            "mining-profit.com", "coin-multiplier.net",
            
            # Tech support scams
            "pc-repair-now.com", "virus-removal.net", "system-alert.org",
            "computer-help.info", "tech-support-urgent.com"
        }
    
    def _load_safe_domains(self) -> Set[str]:
        """Load known safe domains"""
        return {
            # Major tech companies
            "google.com", "microsoft.com", "apple.com", "amazon.com",
            "facebook.com", "meta.com", "twitter.com", "linkedin.com",
            
            # Financial institutions
            "paypal.com", "stripe.com", "square.com", "bankofamerica.com",
            "chase.com", "wellsfargo.com", "citibank.com",
            
            # Email providers
            "gmail.com", "outlook.com", "yahoo.com", "protonmail.com",
            "icloud.com", "zoho.com",
            
            # Cloud services
            "aws.amazon.com", "azure.microsoft.com", "cloud.google.com",
            "dropbox.com", "box.com", "onedrive.com",
            
            # Development and tech
            "github.com", "stackoverflow.com", "reddit.com", "wikipedia.org",
            "mozilla.org", "cloudflare.com", "netlify.com"
        }
    
    def _load_suspicious_patterns(self) -> List[Dict[str, Any]]:
        """Load suspicious domain patterns"""
        return [
            {
                "pattern": r".*-security\..*",
                "description": "Domains with 'security' keyword",
                "severity": ThreatSeverity.MEDIUM,
                "confidence": 0.6
            },
            {
                "pattern": r".*-verification\..*",
                "description": "Domains with 'verification' keyword",
                "severity": ThreatSeverity.MEDIUM,
                "confidence": 0.7
            },
            {
                "pattern": r".*-update\..*",
                "description": "Domains with 'update' keyword",
                "severity": ThreatSeverity.LOW,
                "confidence": 0.5
            },
            {
                "pattern": r"secure-.*\..*",
                "description": "Domains starting with 'secure'",
                "severity": ThreatSeverity.MEDIUM,
                "confidence": 0.6
            },
            {
                "pattern": r".*\.(tk|ml|cf|ga|pw)$",
                "description": "Suspicious top-level domains",
                "severity": ThreatSeverity.HIGH,
                "confidence": 0.8
            },
            {
                "pattern": r".*\d{4,}.*",
                "description": "Domains with many numbers",
                "severity": ThreatSeverity.LOW,
                "confidence": 0.3
            },
            {
                "pattern": r".*-{3,}.*",
                "description": "Domains with multiple hyphens",
                "severity": ThreatSeverity.MEDIUM,
                "confidence": 0.5
            }
        ]
    
    def _load_threat_ip_ranges(self) -> List[Dict[str, Any]]:
        """Load known threat IP ranges"""
        return [
            {
                "range": "185.220.0.0/16",
                "description": "Known Tor exit nodes range",
                "category": ThreatCategory.SUSPICIOUS,
                "severity": ThreatSeverity.MEDIUM
            },
            {
                "range": "194.180.48.0/24",
                "description": "Known botnet C&C range",
                "category": ThreatCategory.BOTNET,
                "severity": ThreatSeverity.HIGH
            }
        ]
    
    async def lookup_domain(self, domain: str) -> Optional[ThreatIntelligenceEntry]:
        """Lookup domain in local threat intelligence"""
        if not domain:
            return None
        
        domain_lower = domain.lower()
        
        # Check known malicious domains
        if domain_lower in self.known_malicious_domains:
            return ThreatIntelligenceEntry(
                domain=domain,
                ip_address=None,
                category=ThreatCategory.PHISHING,
                severity=ThreatSeverity.HIGH,
                confidence=0.95,
                source="local_database",
                description=f"Known malicious domain: {domain}",
                first_seen=datetime.utcnow() - timedelta(days=30),
                last_seen=datetime.utcnow(),
                indicators=["known_malicious"],
                metadata={"list_type": "curated_malicious"}
            )
        
        # Check known safe domains
        if domain_lower in self.known_safe_domains:
            return ThreatIntelligenceEntry(
                domain=domain,
                ip_address=None,
                category=ThreatCategory.SAFE,
                severity=ThreatSeverity.NONE,
                confidence=0.99,
                source="local_database",
                description=f"Known safe domain: {domain}",
                first_seen=datetime.utcnow() - timedelta(days=365),
                last_seen=datetime.utcnow(),
                indicators=["known_safe"],
                metadata={"list_type": "curated_safe"}
            )
        
        # Check suspicious patterns
        for pattern_info in self.suspicious_patterns:
            pattern = pattern_info["pattern"]
            if re.match(pattern, domain_lower):
                return ThreatIntelligenceEntry(
                    domain=domain,
                    ip_address=None,
                    category=ThreatCategory.SUSPICIOUS,
                    severity=pattern_info["severity"],
                    confidence=pattern_info["confidence"],
                    source="pattern_analysis",
                    description=pattern_info["description"],
                    first_seen=datetime.utcnow(),
                    last_seen=datetime.utcnow(),
                    indicators=[f"pattern_match:{pattern}"],
                    metadata={"pattern": pattern}
                )
        
        return None
    
    async def lookup_url(self, url: str) -> Optional[ThreatIntelligenceEntry]:
        """Analyze URL for threats"""
        if not url:
            return None
        
        # Extract domain from URL
        try:
            import urllib.parse
            parsed = urllib.parse.urlparse(url)
            domain = parsed.netloc.lower()
            
            # First check domain
            domain_result = await self.lookup_domain(domain)
            if domain_result:
                return domain_result
            
            # Check for suspicious URL patterns
            suspicious_url_patterns = [
                {
                    "pattern": r".*bit\.ly.*",
                    "description": "Shortened URL service",
                    "severity": ThreatSeverity.MEDIUM,
                    "confidence": 0.6
                },
                {
                    "pattern": r".*\?.*=.*http.*",
                    "description": "URL with suspicious redirect parameter",
                    "severity": ThreatSeverity.HIGH,
                    "confidence": 0.8
                },
                {
                    "pattern": r".*\.(exe|bat|scr|com|pif)$",
                    "description": "URL pointing to executable file",
                    "severity": ThreatSeverity.CRITICAL,
                    "confidence": 0.9
                }
            ]
            
            for pattern_info in suspicious_url_patterns:
                if re.search(pattern_info["pattern"], url.lower()):
                    return ThreatIntelligenceEntry(
                        domain=domain,
                        ip_address=None,
                        category=ThreatCategory.SUSPICIOUS,
                        severity=pattern_info["severity"],
                        confidence=pattern_info["confidence"],
                        source="url_analysis",
                        description=f"Suspicious URL: {pattern_info['description']}",
                        first_seen=datetime.utcnow(),
                        last_seen=datetime.utcnow(),
                        indicators=[f"url_pattern:{pattern_info['pattern']}"],
                        metadata={"url": url, "pattern": pattern_info["pattern"]}
                    )
            
        except Exception as e:
            logger.error(f"Error analyzing URL {url}: {e}")
        
        return None
    
    async def lookup_ip(self, ip: str) -> Optional[ThreatIntelligenceEntry]:
        """Check IP against threat ranges"""
        if not ip:
            return None
        
        try:
            ip_obj = ipaddress.ip_address(ip)
            
            for threat_range in self.threat_ip_ranges:
                network = ipaddress.ip_network(threat_range["range"])
                if ip_obj in network:
                    return ThreatIntelligenceEntry(
                        domain="",
                        ip_address=ip,
                        category=threat_range["category"],
                        severity=threat_range["severity"],
                        confidence=0.8,
                        source="ip_range_analysis",
                        description=threat_range["description"],
                        first_seen=datetime.utcnow() - timedelta(days=7),
                        last_seen=datetime.utcnow(),
                        indicators=[f"ip_range:{threat_range['range']}"],
                        metadata={"ip_range": threat_range["range"]}
                    )
            
        except Exception as e:
            logger.error(f"Error analyzing IP {ip}: {e}")
        
        return None

class CommunityThreatIntelligence(ThreatIntelligenceProvider):
    """Community-based threat intelligence using shared indicators"""
    
    def __init__(self):
        super().__init__("community_intelligence")
        self.community_reports = {}
        self.trust_scores = {}
    
    async def lookup_domain(self, domain: str) -> Optional[ThreatIntelligenceEntry]:
        """Check community reports for domain"""
        try:
            db = get_database()
            
            # Check community threat reports
            reports = await db.community_threats.find({
                "domain": domain,
                "created_at": {"$gte": datetime.utcnow() - timedelta(days=30)}
            }).to_list(length=100)
            
            if not reports:
                return None
            
            # Aggregate community reports
            total_reports = len(reports)
            threat_votes = sum(1 for r in reports if r.get("is_threat", False))
            safe_votes = total_reports - threat_votes
            
            if total_reports < 3:  # Need minimum reports for confidence
                return None
            
            # Calculate confidence based on consensus
            threat_ratio = threat_votes / total_reports
            confidence = min(0.9, threat_ratio) if threat_ratio > 0.6 else 0.3
            
            if threat_ratio > 0.6:  # Majority says it's a threat
                category = ThreatCategory.SUSPICIOUS
                severity = ThreatSeverity.MEDIUM if threat_ratio > 0.8 else ThreatSeverity.LOW
                description = f"Community reported as threat ({threat_votes}/{total_reports} reports)"
            else:
                category = ThreatCategory.SAFE
                severity = ThreatSeverity.NONE
                description = f"Community reported as safe ({safe_votes}/{total_reports} reports)"
            
            return ThreatIntelligenceEntry(
                domain=domain,
                ip_address=None,
                category=category,
                severity=severity,
                confidence=confidence,
                source="community_reports",
                description=description,
                first_seen=min(r.get("created_at", datetime.utcnow()) for r in reports),
                last_seen=max(r.get("created_at", datetime.utcnow()) for r in reports),
                indicators=[f"community_consensus:{threat_ratio:.2f}"],
                metadata={
                    "total_reports": total_reports,
                    "threat_votes": threat_votes,
                    "safe_votes": safe_votes
                }
            )
        
        except Exception as e:
            logger.error(f"Error checking community intelligence for {domain}: {e}")
            return None

class ThreatIntelligenceAggregator:
    """Aggregates threat intelligence from multiple sources"""
    
    def __init__(self):
        self.providers = [
            LocalThreatIntelligence(),
            CommunityThreatIntelligence()
        ]
        self.cache = {}
        self.cache_ttl = 3600  # 1 hour cache
    
    async def lookup_domain(self, domain: str) -> Dict[str, Any]:
        """Lookup domain across all threat intelligence sources"""
        if not domain:
            return self._create_safe_result(domain)
        
        # Check cache first
        cache_key = f"domain:{domain}"
        cached_result = self._get_cached_result(cache_key)
        if cached_result:
            return cached_result
        
        # Query all providers
        results = []
        for provider in self.providers:
            try:
                result = await provider.lookup_domain(domain)
                if result:
                    results.append(result)
            except Exception as e:
                logger.error(f"Error querying provider {provider.name} for domain {domain}: {e}")
        
        # Aggregate results
        aggregated_result = self._aggregate_results(results, domain)
        
        # Cache result
        self._cache_result(cache_key, aggregated_result)
        
        # Store in database for historical tracking
        await self._store_lookup_result(domain, "domain", aggregated_result)
        
        return aggregated_result
    
    async def lookup_url(self, url: str) -> Dict[str, Any]:
        """Lookup URL across all threat intelligence sources"""
        if not url:
            return self._create_safe_result(url)
        
        # Check cache first
        cache_key = f"url:{hashlib.md5(url.encode()).hexdigest()}"
        cached_result = self._get_cached_result(cache_key)
        if cached_result:
            return cached_result
        
        # Query all providers
        results = []
        for provider in self.providers:
            try:
                result = await provider.lookup_url(url)
                if result:
                    results.append(result)
            except Exception as e:
                logger.error(f"Error querying provider {provider.name} for URL {url}: {e}")
        
        # Aggregate results
        aggregated_result = self._aggregate_results(results, url)
        
        # Cache result
        self._cache_result(cache_key, aggregated_result)
        
        # Store in database
        await self._store_lookup_result(url, "url", aggregated_result)
        
        return aggregated_result
    
    def _aggregate_results(self, results: List[ThreatIntelligenceEntry], target: str) -> Dict[str, Any]:
        """Aggregate results from multiple providers"""
        if not results:
            return self._create_safe_result(target)
        
        # Find highest confidence result
        highest_confidence_result = max(results, key=lambda r: r.confidence)
        
        # Aggregate all sources and indicators
        all_sources = list(set(r.source for r in results))
        all_indicators = []
        for r in results:
            all_indicators.extend(r.indicators)
        
        # Calculate aggregated confidence (weighted by source reliability)
        source_weights = {
            "local_database": 0.9,
            "community_reports": 0.7,
            "pattern_analysis": 0.6,
            "url_analysis": 0.8,
            "ip_range_analysis": 0.8
        }
        
        weighted_confidence = 0
        total_weight = 0
        
        for result in results:
            weight = source_weights.get(result.source, 0.5)
            weighted_confidence += result.confidence * weight
            total_weight += weight
        
        final_confidence = weighted_confidence / total_weight if total_weight > 0 else 0.5
        
        # Determine final risk level
        if highest_confidence_result.category in [ThreatCategory.MALWARE, ThreatCategory.PHISHING]:
            risk_level = "phishing"
            risk_score = min(90, 50 + (final_confidence * 40))
        elif highest_confidence_result.category == ThreatCategory.SUSPICIOUS:
            risk_level = "potential_phishing"
            risk_score = min(70, 30 + (final_confidence * 30))
        else:
            risk_level = "safe"
            risk_score = max(10, 20 - (final_confidence * 15))
        
        return {
            "target": target,
            "risk_level": risk_level,
            "risk_score": risk_score,
            "category": highest_confidence_result.category.value,
            "severity": highest_confidence_result.severity.value,
            "confidence": final_confidence,
            "description": highest_confidence_result.description,
            "sources": all_sources,
            "indicators": list(set(all_indicators)),
            "first_seen": min(r.first_seen for r in results).isoformat(),
            "last_seen": max(r.last_seen for r in results).isoformat(),
            "metadata": {
                "provider_count": len(results),
                "aggregated_confidence": final_confidence,
                "primary_source": highest_confidence_result.source
            }
        }
    
    def _create_safe_result(self, target: str) -> Dict[str, Any]:
        """Create a safe result for unknown targets"""
        return {
            "target": target,
            "risk_level": "safe",
            "risk_score": 10,
            "category": ThreatCategory.SAFE.value,
            "severity": ThreatSeverity.NONE.value,
            "confidence": 0.8,
            "description": "No threat intelligence found - appears safe",
            "sources": ["local_intelligence"],
            "indicators": ["no_threats_found"],
            "first_seen": datetime.utcnow().isoformat(),
            "last_seen": datetime.utcnow().isoformat(),
            "metadata": {
                "provider_count": 0,
                "aggregated_confidence": 0.8,
                "primary_source": "default_safe"
            }
        }
    
    def _get_cached_result(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get result from cache if not expired"""
        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            if time.time() - cached_data["timestamp"] < self.cache_ttl:
                return cached_data["result"]
            else:
                del self.cache[cache_key]
        return None
    
    def _cache_result(self, cache_key: str, result: Dict[str, Any]):
        """Cache result with timestamp"""
        self.cache[cache_key] = {
            "result": result,
            "timestamp": time.time()
        }
        
        # Limit cache size
        if len(self.cache) > 1000:
            # Remove oldest entries
            sorted_cache = sorted(self.cache.items(), key=lambda x: x[1]["timestamp"])
            for key, _ in sorted_cache[:100]:  # Remove oldest 100
                del self.cache[key]
    
    async def _store_lookup_result(self, target: str, lookup_type: str, result: Dict[str, Any]):
        """Store lookup result in database for historical tracking"""
        try:
            db = get_database()
            
            lookup_record = {
                "id": str(uuid.uuid4()),
                "target": target,
                "lookup_type": lookup_type,
                "result": result,
                "timestamp": datetime.utcnow()
            }
            
            await db.threat_intelligence_lookups.insert_one(lookup_record)
            
        except Exception as e:
            logger.error(f"Error storing lookup result: {e}")

# Global threat intelligence aggregator
threat_intelligence = ThreatIntelligenceAggregator()

async def check_domain_reputation(domain: str) -> Dict[str, Any]:
    """
    Check domain reputation using threat intelligence
    
    Args:
        domain: Domain to check
        
    Returns:
        Threat intelligence result
    """
    return await threat_intelligence.lookup_domain(domain)

async def check_url_reputation(url: str) -> Dict[str, Any]:
    """
    Check URL reputation using threat intelligence
    
    Args:
        url: URL to check
        
    Returns:
        Threat intelligence result
    """
    return await threat_intelligence.lookup_url(url)

async def submit_community_threat_report(
    domain: str,
    user_id: str,
    is_threat: bool,
    description: str,
    evidence: Optional[str] = None
) -> Dict[str, Any]:
    """
    Submit a community threat report
    
    Args:
        domain: Domain to report
        user_id: User submitting the report
        is_threat: Whether the domain is a threat
        description: Description of the threat
        evidence: Optional evidence
        
    Returns:
        Submission result
    """
    try:
        db = get_database()
        
        report = {
            "id": str(uuid.uuid4()),
            "domain": domain,
            "user_id": user_id,
            "is_threat": is_threat,
            "description": description,
            "evidence": evidence,
            "created_at": datetime.utcnow(),
            "verified": False
        }
        
        await db.community_threats.insert_one(report)
        
        return {
            "success": True,
            "report_id": report["id"],
            "message": "Community threat report submitted successfully"
        }
        
    except Exception as e:
        logger.error(f"Error submitting community threat report: {e}")
        return {
            "success": False,
            "error": "Failed to submit threat report"
        }