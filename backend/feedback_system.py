"""
Feedback System for Aman Cybersecurity Platform
Collects user feedback to improve threat detection accuracy
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
import logging
from dataclasses import dataclass
import asyncio
from database import get_database
import uuid

logger = logging.getLogger(__name__)

class FeedbackType(Enum):
    FALSE_POSITIVE = "false_positive"  # Marked as threat but was safe
    FALSE_NEGATIVE = "false_negative"  # Missed a real threat
    CORRECT_DETECTION = "correct_detection"  # Correctly identified threat/safe
    SEVERITY_ADJUSTMENT = "severity_adjustment"  # Risk score too high/low

class FeedbackSource(Enum):
    USER_MANUAL = "user_manual"  # User manually provided feedback
    USER_REPORT = "user_report"  # User reported email as phishing
    AUTOMATIC = "automatic"  # System detected inconsistency
    ADMIN_REVIEW = "admin_review"  # Admin reviewed and corrected

@dataclass
class FeedbackEntry:
    id: str
    scan_id: str
    user_id: str
    feedback_type: FeedbackType
    source: FeedbackSource
    original_risk_score: float
    suggested_risk_score: Optional[float]
    original_risk_level: str
    suggested_risk_level: Optional[str]
    user_comment: Optional[str]
    email_metadata: Dict[str, Any]
    threat_indicators: List[Dict[str, Any]]
    created_at: datetime
    processed: bool = False
    admin_review: Optional[str] = None

class FeedbackCollector:
    """Collects and processes user feedback for improving threat detection"""
    
    def __init__(self):
        self.feedback_patterns = {}
        self.improvement_suggestions = []
    
    async def submit_feedback(
        self,
        scan_id: str,
        user_id: str,
        feedback_type: str,
        is_correct: bool,
        suggested_risk_level: Optional[str] = None,
        user_comment: Optional[str] = None,
        email_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Submit user feedback for a scan result
        
        Args:
            scan_id: ID of the original scan
            user_id: ID of the user providing feedback
            feedback_type: Type of feedback
            is_correct: Whether the original assessment was correct
            suggested_risk_level: User's suggested risk level
            user_comment: Optional user comment
            email_metadata: Metadata about the email
            
        Returns:
            Feedback submission result
        """
        try:
            db = get_database()
            
            # Get original scan result
            original_scan = await db.email_scans.find_one({"id": scan_id})
            if not original_scan:
                return {
                    "success": False,
                    "error": "Original scan not found"
                }
            
            # Determine feedback type based on user input
            determined_feedback_type = self._determine_feedback_type(
                is_correct, 
                original_scan.get("scan_result", "safe"),
                suggested_risk_level
            )
            
            # Create feedback entry
            feedback_entry = FeedbackEntry(
                id=str(uuid.uuid4()),
                scan_id=scan_id,
                user_id=user_id,
                feedback_type=determined_feedback_type,
                source=FeedbackSource.USER_MANUAL,
                original_risk_score=original_scan.get("risk_score", 0.0),
                suggested_risk_score=self._convert_risk_level_to_score(suggested_risk_level),
                original_risk_level=original_scan.get("scan_result", "safe"),
                suggested_risk_level=suggested_risk_level,
                user_comment=user_comment,
                email_metadata=email_metadata or {},
                threat_indicators=original_scan.get("threat_indicators", []),
                created_at=datetime.utcnow()
            )
            
            # Store feedback
            await db.feedback.insert_one(feedback_entry.__dict__)
            
            # Process feedback for immediate learning
            await self._process_feedback_immediately(feedback_entry)
            
            # Update scan accuracy metrics
            await self._update_accuracy_metrics(user_id, determined_feedback_type)
            
            logger.info(f"Feedback submitted for scan {scan_id} by user {user_id}")
            
            return {
                "success": True,
                "feedback_id": feedback_entry.id,
                "message": "Feedback submitted successfully"
            }
            
        except Exception as e:
            logger.error(f"Error submitting feedback: {e}")
            return {
                "success": False,
                "error": "Failed to submit feedback"
            }
    
    def _determine_feedback_type(
        self, 
        is_correct: bool, 
        original_level: str, 
        suggested_level: Optional[str]
    ) -> FeedbackType:
        """Determine the type of feedback based on user input"""
        
        if is_correct:
            return FeedbackType.CORRECT_DETECTION
        
        # If not correct, determine if false positive or false negative
        if original_level in ["phishing", "potential_phishing"] and suggested_level == "safe":
            return FeedbackType.FALSE_POSITIVE
        elif original_level == "safe" and suggested_level in ["phishing", "potential_phishing"]:
            return FeedbackType.FALSE_NEGATIVE
        else:
            return FeedbackType.SEVERITY_ADJUSTMENT
    
    def _convert_risk_level_to_score(self, risk_level: Optional[str]) -> Optional[float]:
        """Convert risk level to approximate score"""
        if not risk_level:
            return None
            
        level_mapping = {
            "safe": 10.0,
            "potential_phishing": 50.0,
            "phishing": 85.0
        }
        
        return level_mapping.get(risk_level, 50.0)
    
    async def _process_feedback_immediately(self, feedback: FeedbackEntry):
        """Process feedback immediately for quick learning"""
        try:
            # Analyze patterns in the feedback
            pattern_analysis = await self._analyze_feedback_patterns(feedback)
            
            # Update internal learning metrics
            await self._update_learning_metrics(feedback, pattern_analysis)
            
            # Generate improvement suggestions
            suggestions = await self._generate_improvement_suggestions(feedback)
            
            if suggestions:
                self.improvement_suggestions.extend(suggestions)
                
                # Keep only recent suggestions (last 100)
                self.improvement_suggestions = self.improvement_suggestions[-100:]
            
        except Exception as e:
            logger.error(f"Error processing immediate feedback: {e}")
    
    async def _analyze_feedback_patterns(self, feedback: FeedbackEntry) -> Dict[str, Any]:
        """Analyze patterns in feedback to identify learning opportunities"""
        try:
            db = get_database()
            
            # Get recent feedback for pattern analysis
            recent_feedback = await db.feedback.find({
                "created_at": {"$gte": datetime.utcnow() - timedelta(days=30)}
            }).to_list(length=1000)
            
            patterns = {
                "common_false_positives": [],
                "common_false_negatives": [],
                "accuracy_trends": {},
                "threat_pattern_misses": []
            }
            
            # Analyze false positives
            false_positives = [f for f in recent_feedback if f.get("feedback_type") == FeedbackType.FALSE_POSITIVE.value]
            if false_positives:
                # Find common patterns in false positives
                fp_patterns = self._extract_common_patterns(false_positives)
                patterns["common_false_positives"] = fp_patterns
            
            # Analyze false negatives
            false_negatives = [f for f in recent_feedback if f.get("feedback_type") == FeedbackType.FALSE_NEGATIVE.value]
            if false_negatives:
                # Find common patterns in false negatives
                fn_patterns = self._extract_common_patterns(false_negatives)
                patterns["common_false_negatives"] = fn_patterns
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error analyzing feedback patterns: {e}")
            return {}
    
    def _extract_common_patterns(self, feedback_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract common patterns from feedback entries"""
        patterns = []
        
        # Analyze common threat indicators that were incorrectly assessed
        threat_indicator_counts = {}
        
        for feedback in feedback_list:
            threat_indicators = feedback.get("threat_indicators", [])
            for indicator in threat_indicators:
                indicator_key = f"{indicator.get('source', 'unknown')}:{indicator.get('threat_type', 'unknown')}"
                threat_indicator_counts[indicator_key] = threat_indicator_counts.get(indicator_key, 0) + 1
        
        # Identify most common problematic patterns
        sorted_patterns = sorted(threat_indicator_counts.items(), key=lambda x: x[1], reverse=True)
        
        for pattern, count in sorted_patterns[:5]:  # Top 5 patterns
            if count >= 3:  # Only if seen multiple times
                source, threat_type = pattern.split(":", 1)
                patterns.append({
                    "pattern": pattern,
                    "source": source,
                    "threat_type": threat_type,
                    "frequency": count,
                    "suggestion": f"Review detection logic for {threat_type} in {source}"
                })
        
        return patterns
    
    async def _update_learning_metrics(self, feedback: FeedbackEntry, patterns: Dict[str, Any]):
        """Update learning metrics based on feedback"""
        try:
            db = get_database()
            
            # Update or create learning metrics document
            learning_metrics = await db.learning_metrics.find_one({"type": "scanner_performance"})
            
            if not learning_metrics:
                learning_metrics = {
                    "type": "scanner_performance",
                    "total_feedback": 0,
                    "accuracy_rate": 0.0,
                    "false_positive_rate": 0.0,
                    "false_negative_rate": 0.0,
                    "last_updated": datetime.utcnow(),
                    "feedback_breakdown": {
                        "correct_detections": 0,
                        "false_positives": 0,
                        "false_negatives": 0,
                        "severity_adjustments": 0
                    }
                }
            
            # Update feedback counts
            learning_metrics["total_feedback"] += 1
            feedback_type_key = feedback.feedback_type.value
            
            if feedback_type_key in learning_metrics["feedback_breakdown"]:
                learning_metrics["feedback_breakdown"][feedback_type_key] += 1
            
            # Recalculate rates
            total = learning_metrics["total_feedback"]
            correct = learning_metrics["feedback_breakdown"]["correct_detections"]
            fp = learning_metrics["feedback_breakdown"]["false_positives"]
            fn = learning_metrics["feedback_breakdown"]["false_negatives"]
            
            learning_metrics["accuracy_rate"] = (correct / total * 100) if total > 0 else 0
            learning_metrics["false_positive_rate"] = (fp / total * 100) if total > 0 else 0
            learning_metrics["false_negative_rate"] = (fn / total * 100) if total > 0 else 0
            learning_metrics["last_updated"] = datetime.utcnow()
            
            # Store updated metrics
            await db.learning_metrics.replace_one(
                {"type": "scanner_performance"},
                learning_metrics,
                upsert=True
            )
            
        except Exception as e:
            logger.error(f"Error updating learning metrics: {e}")
    
    async def _generate_improvement_suggestions(self, feedback: FeedbackEntry) -> List[Dict[str, Any]]:
        """Generate improvement suggestions based on feedback"""
        suggestions = []
        
        try:
            if feedback.feedback_type == FeedbackType.FALSE_POSITIVE:
                # Suggest reducing sensitivity for similar patterns
                suggestions.append({
                    "type": "sensitivity_adjustment",
                    "description": f"Consider reducing sensitivity for {feedback.original_risk_level} classification",
                    "priority": "medium",
                    "threat_indicators": feedback.threat_indicators,
                    "feedback_id": feedback.id
                })
            
            elif feedback.feedback_type == FeedbackType.FALSE_NEGATIVE:
                # Suggest new detection patterns
                email_metadata = feedback.email_metadata
                
                suggestions.append({
                    "type": "detection_enhancement",
                    "description": f"Enhance detection for missed {feedback.suggested_risk_level} threats",
                    "priority": "high",
                    "email_patterns": {
                        "subject_length": len(email_metadata.get("subject", "")),
                        "body_length": len(email_metadata.get("body", "")),
                        "sender_domain": email_metadata.get("sender_domain", ""),
                        "link_count": email_metadata.get("link_count", 0)
                    },
                    "feedback_id": feedback.id
                })
            
            elif feedback.feedback_type == FeedbackType.SEVERITY_ADJUSTMENT:
                # Suggest risk score calibration
                score_diff = (feedback.suggested_risk_score or 50) - feedback.original_risk_score
                
                suggestions.append({
                    "type": "score_calibration",
                    "description": f"Risk score adjustment needed: {score_diff:+.1f} points",
                    "priority": "low" if abs(score_diff) < 20 else "medium",
                    "score_adjustment": score_diff,
                    "feedback_id": feedback.id
                })
            
        except Exception as e:
            logger.error(f"Error generating improvement suggestions: {e}")
        
        return suggestions
    
    async def _update_accuracy_metrics(self, user_id: str, feedback_type: FeedbackType):
        """Update user-specific accuracy metrics"""
        try:
            db = get_database()
            
            # Update user accuracy tracking
            user_accuracy = await db.user_accuracy.find_one({"user_id": user_id})
            
            if not user_accuracy:
                user_accuracy = {
                    "user_id": user_id,
                    "total_feedback": 0,
                    "correct_assessments": 0,
                    "accuracy_rate": 0.0,
                    "last_feedback": datetime.utcnow()
                }
            
            user_accuracy["total_feedback"] += 1
            
            if feedback_type == FeedbackType.CORRECT_DETECTION:
                user_accuracy["correct_assessments"] += 1
            
            # Calculate accuracy rate
            total = user_accuracy["total_feedback"]
            correct = user_accuracy["correct_assessments"]
            user_accuracy["accuracy_rate"] = (correct / total * 100) if total > 0 else 0
            user_accuracy["last_feedback"] = datetime.utcnow()
            
            # Store updated metrics
            await db.user_accuracy.replace_one(
                {"user_id": user_id},
                user_accuracy,
                upsert=True
            )
            
        except Exception as e:
            logger.error(f"Error updating user accuracy metrics: {e}")
    
    async def get_feedback_analytics(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get feedback analytics for dashboard display"""
        try:
            db = get_database()
            
            # Build query
            query = {}
            if user_id:
                query["user_id"] = user_id
            
            # Get recent feedback (last 30 days)
            recent_date = datetime.utcnow() - timedelta(days=30)
            query["created_at"] = {"$gte": recent_date}
            
            feedback_data = await db.feedback.find(query).to_list(length=1000)
            
            # Calculate analytics
            total_feedback = len(feedback_data)
            
            if total_feedback == 0:
                return {
                    "total_feedback": 0,
                    "accuracy_rate": 0,
                    "feedback_breakdown": {},
                    "improvement_areas": [],
                    "user_engagement": "low"
                }
            
            # Count feedback types
            feedback_counts = {}
            for feedback in feedback_data:
                feedback_type = feedback.get("feedback_type", "unknown")
                feedback_counts[feedback_type] = feedback_counts.get(feedback_type, 0) + 1
            
            # Calculate accuracy rate
            correct_detections = feedback_counts.get(FeedbackType.CORRECT_DETECTION.value, 0)
            accuracy_rate = (correct_detections / total_feedback * 100) if total_feedback > 0 else 0
            
            # Identify improvement areas
            improvement_areas = []
            false_positives = feedback_counts.get(FeedbackType.FALSE_POSITIVE.value, 0)
            false_negatives = feedback_counts.get(FeedbackType.FALSE_NEGATIVE.value, 0)
            
            if false_positives > total_feedback * 0.1:  # >10% false positives
                improvement_areas.append("Reduce false positive rate")
            
            if false_negatives > total_feedback * 0.05:  # >5% false negatives
                improvement_areas.append("Improve threat detection sensitivity")
            
            # Determine user engagement level
            engagement_level = "high" if total_feedback > 20 else "medium" if total_feedback > 5 else "low"
            
            return {
                "total_feedback": total_feedback,
                "accuracy_rate": round(accuracy_rate, 2),
                "feedback_breakdown": feedback_counts,
                "improvement_areas": improvement_areas,
                "user_engagement": engagement_level,
                "recent_improvements": self.improvement_suggestions[-5:] if self.improvement_suggestions else []
            }
            
        except Exception as e:
            logger.error(f"Error getting feedback analytics: {e}")
            return {
                "total_feedback": 0,
                "accuracy_rate": 0,
                "feedback_breakdown": {},
                "improvement_areas": ["Error loading analytics"],
                "user_engagement": "unknown"
            }
    
    async def get_improvement_suggestions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent improvement suggestions"""
        return self.improvement_suggestions[-limit:] if self.improvement_suggestions else []

# Global feedback collector instance
feedback_collector = FeedbackCollector()

async def submit_scan_feedback(
    scan_id: str,
    user_id: str,
    is_correct: bool,
    suggested_risk_level: Optional[str] = None,
    user_comment: Optional[str] = None
) -> Dict[str, Any]:
    """
    API function to submit feedback for a scan result
    
    Args:
        scan_id: ID of the scan to provide feedback for
        user_id: ID of the user providing feedback
        is_correct: Whether the scan result was correct
        suggested_risk_level: User's suggested risk level
        user_comment: Optional user comment
        
    Returns:
        Feedback submission result
    """
    return await feedback_collector.submit_feedback(
        scan_id=scan_id,
        user_id=user_id,
        feedback_type="user_assessment",
        is_correct=is_correct,
        suggested_risk_level=suggested_risk_level,
        user_comment=user_comment
    )

async def get_user_feedback_analytics(user_id: str) -> Dict[str, Any]:
    """Get feedback analytics for a specific user"""
    return await feedback_collector.get_feedback_analytics(user_id=user_id)

async def get_system_feedback_analytics() -> Dict[str, Any]:
    """Get system-wide feedback analytics"""
    return await feedback_collector.get_feedback_analytics()