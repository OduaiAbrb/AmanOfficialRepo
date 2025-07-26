"""
Admin Panel Management System for Aman Cybersecurity Platform
Comprehensive organization security team dashboard and management system
"""

import logging
import uuid
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

from database import get_database
from models import UserResponse

logger = logging.getLogger(__name__)

class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin" 
    MANAGER = "manager"
    USER = "user"

class OrganizationStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIAL = "trial"
    EXPIRED = "expired"

@dataclass
class AdminDashboardStats:
    """Admin dashboard statistics"""
    total_users: int
    active_users: int
    total_organizations: int
    active_organizations: int
    today_scans: int
    today_threats: int
    total_threats_blocked: int
    avg_risk_score: float
    ai_usage_cost: float
    cache_hit_rate: float
    
class AdminManager:
    """Comprehensive admin panel management system"""
    
    def __init__(self):
        self.db = None
    
    async def get_database(self):
        """Get database connection"""
        if not self.db:
            self.db = get_database()
        return self.db
    
    async def get_admin_dashboard_stats(self) -> AdminDashboardStats:
        """Get comprehensive admin dashboard statistics"""
        try:
            db = await self.get_database()
            
            # Get today's date range
            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            tomorrow = today + timedelta(days=1)
            
            # User statistics
            total_users = await db.users.count_documents({})
            active_users = await db.users.count_documents({"is_active": True})
            
            # Organization statistics  
            total_orgs = await db.organizations.count_documents({})
            active_orgs = await db.organizations.count_documents({"status": "active"})
            
            # Scan statistics for today
            today_scans = await db.email_scans.count_documents({
                "created_at": {"$gte": today, "$lt": tomorrow}
            })
            
            today_threats = await db.email_scans.count_documents({
                "created_at": {"$gte": today, "$lt": tomorrow},
                "scan_result": {"$in": ["potential_phishing", "phishing"]}
            })
            
            # Total threats blocked (all time)
            total_threats = await db.email_scans.count_documents({
                "scan_result": {"$in": ["potential_phishing", "phishing"]}
            })
            
            # Average risk score for today
            risk_pipeline = [
                {"$match": {"created_at": {"$gte": today, "$lt": tomorrow}}},
                {"$group": {"_id": None, "avg_risk": {"$avg": "$risk_score"}}}
            ]
            risk_result = await db.email_scans.aggregate(risk_pipeline).to_list(1)
            avg_risk = risk_result[0]["avg_risk"] if risk_result else 0.0
            
            # AI usage cost for today
            ai_cost_pipeline = [
                {"$match": {"timestamp": {"$gte": today, "$lt": tomorrow}}},
                {"$group": {"_id": None, "total_cost": {"$sum": "$estimated_cost"}}}
            ]
            ai_cost_result = await db.ai_usage.aggregate(ai_cost_pipeline).to_list(1)
            ai_cost = ai_cost_result[0]["total_cost"] if ai_cost_result else 0.0
            
            # Cache hit rate for today
            cache_pipeline = [
                {"$match": {"timestamp": {"$gte": today, "$lt": tomorrow}}},
                {"$group": {
                    "_id": None,
                    "cache_hits": {"$sum": {"$cond": ["$cache_hit", 1, 0]}},
                    "total_requests": {"$sum": 1}
                }}
            ]
            cache_result = await db.ai_usage.aggregate(cache_pipeline).to_list(1)
            cache_hit_rate = 0.0
            if cache_result and cache_result[0]["total_requests"] > 0:
                cache_hit_rate = cache_result[0]["cache_hits"] / cache_result[0]["total_requests"]
            
            return AdminDashboardStats(
                total_users=total_users,
                active_users=active_users,
                total_organizations=total_orgs,
                active_organizations=active_orgs,
                today_scans=today_scans,
                today_threats=today_threats,
                total_threats_blocked=total_threats,
                avg_risk_score=round(avg_risk, 2),
                ai_usage_cost=round(ai_cost, 4),
                cache_hit_rate=round(cache_hit_rate, 3)
            )
            
        except Exception as e:
            logger.error(f"Admin dashboard stats error: {e}")
            return AdminDashboardStats(0, 0, 0, 0, 0, 0, 0, 0.0, 0.0, 0.0)
    
    async def get_user_management_data(self, page: int = 1, page_size: int = 50, search: str = "") -> Dict[str, Any]:
        """Get user management data with pagination and search"""
        try:
            db = await self.get_database()
            
            # Build search query
            query = {}
            if search:
                query = {
                    "$or": [
                        {"name": {"$regex": search, "$options": "i"}},
                        {"email": {"$regex": search, "$options": "i"}},
                        {"organization": {"$regex": search, "$options": "i"}}
                    ]
                }
            
            # Get total count
            total_users = await db.users.count_documents(query)
            
            # Get paginated users
            skip = (page - 1) * page_size
            users_cursor = db.users.find(query).skip(skip).limit(page_size).sort("created_at", -1)
            users = await users_cursor.to_list(page_size)
            
            # Process user data
            processed_users = []
            for user in users:
                # Get user's scan statistics
                scan_stats = await self._get_user_scan_stats(user.get("id", str(user["_id"])))
                
                processed_users.append({
                    "id": user.get("id", str(user["_id"])),
                    "name": user.get("name", ""),
                    "email": user.get("email", ""),
                    "organization": user.get("organization", ""),
                    "role": user.get("role", "user"),
                    "is_active": user.get("is_active", True),
                    "created_at": user.get("created_at", datetime.utcnow()).isoformat(),
                    "last_login": user.get("last_login", "").isoformat() if user.get("last_login") else "",
                    "scan_stats": scan_stats
                })
            
            return {
                "users": processed_users,
                "pagination": {
                    "current_page": page,
                    "page_size": page_size,
                    "total_users": total_users,
                    "total_pages": (total_users + page_size - 1) // page_size
                }
            }
            
        except Exception as e:
            logger.error(f"User management data error: {e}")
            return {"users": [], "pagination": {}}
    
    async def _get_user_scan_stats(self, user_id: str) -> Dict[str, Any]:
        """Get scan statistics for a specific user"""
        try:
            db = await self.get_database()
            
            # Get today's date range
            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            
            # User's scan statistics
            total_scans = await db.email_scans.count_documents({"user_id": user_id})
            
            today_scans = await db.email_scans.count_documents({
                "user_id": user_id,
                "created_at": {"$gte": today}
            })
            
            threats_blocked = await db.email_scans.count_documents({
                "user_id": user_id,
                "scan_result": {"$in": ["potential_phishing", "phishing"]}
            })
            
            # AI usage cost
            ai_cost_pipeline = [
                {"$match": {"user_id": user_id}},
                {"$group": {"_id": None, "total_cost": {"$sum": "$estimated_cost"}}}
            ]
            ai_cost_result = await db.ai_usage.aggregate(ai_cost_pipeline).to_list(1)
            ai_cost = ai_cost_result[0]["total_cost"] if ai_cost_result else 0.0
            
            return {
                "total_scans": total_scans,
                "today_scans": today_scans,
                "threats_blocked": threats_blocked,
                "ai_cost": round(ai_cost, 4)
            }
            
        except Exception as e:
            logger.error(f"User scan stats error: {e}")
            return {"total_scans": 0, "today_scans": 0, "threats_blocked": 0, "ai_cost": 0.0}
    
    async def update_user_status(self, admin_user_id: str, target_user_id: str, is_active: bool) -> Dict[str, Any]:
        """Update user active status"""
        try:
            db = await self.get_database()
            
            # Update user status
            result = await db.users.update_one(
                {"id": target_user_id},
                {
                    "$set": {
                        "is_active": is_active,
                        "updated_at": datetime.utcnow(),
                        "updated_by": admin_user_id
                    }
                }
            )
            
            if result.modified_count > 0:
                # Log admin action
                await self._log_admin_action(admin_user_id, "USER_STATUS_UPDATE", {
                    "target_user_id": target_user_id,
                    "new_status": "active" if is_active else "inactive"
                })
                
                return {"success": True, "message": "User status updated successfully"}
            else:
                return {"success": False, "error": "User not found or status unchanged"}
                
        except Exception as e:
            logger.error(f"Update user status error: {e}")
            return {"success": False, "error": str(e)}
    
    async def update_user_role(self, admin_user_id: str, target_user_id: str, new_role: str) -> Dict[str, Any]:
        """Update user role"""
        try:
            # Validate role
            if new_role not in [role.value for role in UserRole]:
                return {"success": False, "error": "Invalid role"}
            
            db = await self.get_database()
            
            # Update user role
            result = await db.users.update_one(
                {"id": target_user_id},
                {
                    "$set": {
                        "role": new_role,
                        "updated_at": datetime.utcnow(),
                        "updated_by": admin_user_id
                    }
                }
            )
            
            if result.modified_count > 0:
                # Log admin action
                await self._log_admin_action(admin_user_id, "USER_ROLE_UPDATE", {
                    "target_user_id": target_user_id,
                    "new_role": new_role
                })
                
                return {"success": True, "message": "User role updated successfully"}
            else:
                return {"success": False, "error": "User not found or role unchanged"}
                
        except Exception as e:
            logger.error(f"Update user role error: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_threat_management_data(self, days: int = 7) -> Dict[str, Any]:
        """Get threat management dashboard data"""
        try:
            db = await self.get_database()
            
            # Date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Threat statistics
            threat_stats_pipeline = [
                {
                    "$match": {
                        "created_at": {"$gte": start_date, "$lt": end_date},
                        "scan_result": {"$in": ["potential_phishing", "phishing"]}
                    }
                },
                {
                    "$group": {
                        "_id": {
                            "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
                            "status": "$scan_result"
                        },
                        "count": {"$sum": 1},
                        "avg_risk": {"$avg": "$risk_score"}
                    }
                },
                {"$sort": {"_id.date": 1}}
            ]
            
            threat_stats = await db.email_scans.aggregate(threat_stats_pipeline).to_list(100)
            
            # Top threat sources
            threat_sources_pipeline = [
                {
                    "$match": {
                        "created_at": {"$gte": start_date, "$lt": end_date},
                        "scan_result": {"$in": ["potential_phishing", "phishing"]}
                    }
                },
                {"$unwind": "$threat_sources"},
                {
                    "$group": {
                        "_id": "$threat_sources",
                        "count": {"$sum": 1}
                    }
                },
                {"$sort": {"count": -1}},
                {"$limit": 10}
            ]
            
            threat_sources = await db.email_scans.aggregate(threat_sources_pipeline).to_list(10)
            
            # Recent high-risk scans
            recent_threats = await db.email_scans.find({
                "created_at": {"$gte": start_date, "$lt": end_date},
                "risk_score": {"$gte": 70}
            }).sort("created_at", -1).limit(20).to_list(20)
            
            # Process recent threats
            processed_threats = []
            for threat in recent_threats:
                processed_threats.append({
                    "id": threat.get("id", str(threat["_id"])),
                    "user_id": threat.get("user_id", ""),
                    "email_subject": threat.get("email_subject", "")[:50],
                    "sender": threat.get("sender", ""),
                    "risk_score": threat.get("risk_score", 0),
                    "scan_result": threat.get("scan_result", ""),
                    "threat_sources": threat.get("threat_sources", []),
                    "detected_threats": threat.get("detected_threats", []),
                    "created_at": threat.get("created_at", datetime.utcnow()).isoformat()
                })
            
            return {
                "threat_timeline": threat_stats,
                "top_threat_sources": threat_sources,
                "recent_threats": processed_threats,
                "analysis_period": {
                    "days": days,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Threat management data error: {e}")
            return {}
    
    async def get_system_monitoring_data(self) -> Dict[str, Any]:
        """Get system monitoring and health data"""
        try:
            db = await self.get_database()
            
            # System health metrics
            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            
            # API performance metrics
            api_pipeline = [
                {"$match": {"timestamp": {"$gte": today}}},
                {
                    "$group": {
                        "_id": "$operation_type",
                        "total_requests": {"$sum": 1},
                        "avg_response_time": {"$avg": "$response_time_ms"},
                        "total_cost": {"$sum": "$estimated_cost"}
                    }
                }
            ]
            
            api_metrics = await db.ai_usage.aggregate(api_pipeline).to_list(10)
            
            # Error rate analysis
            error_pipeline = [
                {"$match": {"timestamp": {"$gte": today - timedelta(hours=24)}}},
                {
                    "$group": {
                        "_id": {"$hour": "$timestamp"},
                        "total_requests": {"$sum": 1},
                        "errors": {"$sum": {"$cond": [{"$ifNull": ["$metadata.error", False]}, 1, 0]}}
                    }
                },
                {"$sort": {"_id": 1}}
            ]
            
            error_rates = await db.ai_usage.aggregate(error_pipeline).to_list(24)
            
            # Database statistics
            db_stats = await db.command("dbStats")
            
            # WebSocket connections (if realtime manager is available)
            ws_stats = {"active_connections": 0, "unique_users": 0}
            try:
                from realtime_manager import realtime_manager
                ws_stats = realtime_manager.get_connection_stats()
            except:
                pass
            
            return {
                "api_performance": api_metrics,
                "error_rates": error_rates,
                "database_stats": {
                    "total_size": db_stats.get("dataSize", 0),
                    "collections": db_stats.get("collections", 0),
                    "indexes": db_stats.get("indexes", 0)
                },
                "websocket_stats": ws_stats,
                "system_health": "healthy",  # This could be enhanced with actual health checks
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"System monitoring data error: {e}")
            return {}
    
    async def _log_admin_action(self, admin_user_id: str, action_type: str, details: Dict[str, Any]):
        """Log admin actions for audit trail"""
        try:
            db = await self.get_database()
            
            log_entry = {
                "id": str(uuid.uuid4()),
                "admin_user_id": admin_user_id,
                "action_type": action_type,
                "details": details,
                "timestamp": datetime.utcnow(),
                "ip_address": details.get("ip_address", ""),
                "user_agent": details.get("user_agent", "")
            }
            
            await db.admin_actions.insert_one(log_entry)
            
        except Exception as e:
            logger.error(f"Admin action logging error: {e}")
    
    async def get_admin_audit_log(self, page: int = 1, page_size: int = 50, days: int = 30) -> Dict[str, Any]:
        """Get admin action audit log"""
        try:
            db = await self.get_database()
            
            # Date range
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Build query
            query = {"timestamp": {"$gte": start_date}}
            
            # Get total count
            total_actions = await db.admin_actions.count_documents(query)
            
            # Get paginated actions
            skip = (page - 1) * page_size
            actions_cursor = db.admin_actions.find(query).skip(skip).limit(page_size).sort("timestamp", -1)
            actions = await actions_cursor.to_list(page_size)
            
            # Process actions
            processed_actions = []
            for action in actions:
                processed_actions.append({
                    "id": action.get("id", str(action["_id"])),
                    "admin_user_id": action.get("admin_user_id", ""),
                    "action_type": action.get("action_type", ""),
                    "details": action.get("details", {}),
                    "timestamp": action.get("timestamp", datetime.utcnow()).isoformat(),
                    "ip_address": action.get("ip_address", ""),
                    "user_agent": action.get("user_agent", "")[:100]  # Truncate user agent
                })
            
            return {
                "actions": processed_actions,
                "pagination": {
                    "current_page": page,
                    "page_size": page_size,
                    "total_actions": total_actions,
                    "total_pages": (total_actions + page_size - 1) // page_size
                },
                "period_days": days
            }
            
        except Exception as e:
            logger.error(f"Admin audit log error: {e}")
            return {"actions": [], "pagination": {}}

# Global instance
admin_manager = AdminManager()

# Helper functions
async def get_admin_dashboard_stats() -> AdminDashboardStats:
    """Helper function to get admin dashboard statistics"""
    return await admin_manager.get_admin_dashboard_stats()

async def get_user_management_data(page: int = 1, page_size: int = 50, search: str = "") -> Dict[str, Any]:
    """Helper function to get user management data"""
    return await admin_manager.get_user_management_data(page, page_size, search)

async def update_user_status(admin_user_id: str, target_user_id: str, is_active: bool) -> Dict[str, Any]:
    """Helper function to update user status"""
    return await admin_manager.update_user_status(admin_user_id, target_user_id, is_active)

async def update_user_role(admin_user_id: str, target_user_id: str, new_role: str) -> Dict[str, Any]:
    """Helper function to update user role"""
    return await admin_manager.update_user_role(admin_user_id, target_user_id, new_role)

async def get_threat_management_data(days: int = 7) -> Dict[str, Any]:
    """Helper function to get threat management data"""
    return await admin_manager.get_threat_management_data(days)

async def get_system_monitoring_data() -> Dict[str, Any]:
    """Helper function to get system monitoring data"""
    return await admin_manager.get_system_monitoring_data()

async def get_admin_audit_log(page: int = 1, page_size: int = 50, days: int = 30) -> Dict[str, Any]:
    """Helper function to get admin audit log"""
    return await admin_manager.get_admin_audit_log(page, page_size, days)