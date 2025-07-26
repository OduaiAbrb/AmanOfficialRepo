"""
Real-time WebSocket Manager for Aman Cybersecurity Platform
Handles live dashboard updates, threat notifications, and real-time statistics
"""

import json
import asyncio
import logging
from typing import Dict, Set, List, Any, Optional
from datetime import datetime, timedelta
import uuid
from dataclasses import dataclass, asdict
from enum import Enum

from fastapi import WebSocket, WebSocketDisconnect
from database import get_database

logger = logging.getLogger(__name__)

class NotificationType(str, Enum):
    THREAT_DETECTED = "threat_detected"
    SCAN_COMPLETED = "scan_completed"
    STATISTICS_UPDATE = "statistics_update"
    THREAT_FEED_UPDATE = "threat_feed_update"
    SYSTEM_ALERT = "system_alert"

@dataclass
class WebSocketConnection:
    websocket: WebSocket
    user_id: str
    connection_id: str
    connected_at: datetime
    organization_id: Optional[str] = None
    subscription_types: Set[str] = None

    def __post_init__(self):
        if self.subscription_types is None:
            self.subscription_types = {"all"}

@dataclass
class RealTimeNotification:
    id: str
    user_id: str
    notification_type: NotificationType
    title: str
    message: str
    data: Dict[str, Any]
    timestamp: datetime
    priority: str = "normal"  # low, normal, high, critical
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.notification_type.value,
            "title": self.title,
            "message": self.message,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "priority": self.priority
        }

class RealTimeManager:
    """Manages WebSocket connections and real-time updates"""
    
    def __init__(self):
        self.connections: Dict[str, WebSocketConnection] = {}
        self.user_connections: Dict[str, Set[str]] = {}  # user_id -> set of connection_ids
        self.organization_connections: Dict[str, Set[str]] = {}  # org_id -> set of connection_ids
        self.notification_queue: asyncio.Queue = asyncio.Queue()
        self.background_tasks: Set[asyncio.Task] = set()
        
    async def connect(self, websocket: WebSocket, user_id: str, organization_id: Optional[str] = None) -> str:
        """Accept a WebSocket connection"""
        try:
            await websocket.accept()
            connection_id = str(uuid.uuid4())
            
            connection = WebSocketConnection(
                websocket=websocket,
                user_id=user_id,
                connection_id=connection_id,
                connected_at=datetime.utcnow(),
                organization_id=organization_id
            )
            
            self.connections[connection_id] = connection
            
            # Add to user connections
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(connection_id)
            
            # Add to organization connections
            if organization_id:
                if organization_id not in self.organization_connections:
                    self.organization_connections[organization_id] = set()
                self.organization_connections[organization_id].add(connection_id)
            
            logger.info(f"WebSocket connected: user_id={user_id}, connection_id={connection_id}")
            
            # Send connection confirmation
            await self.send_to_connection(connection_id, {
                "type": "connection_established",
                "connection_id": connection_id,
                "timestamp": datetime.utcnow().isoformat(),
                "message": "Real-time connection established"
            })
            
            # Send initial statistics
            await self.send_dashboard_statistics(user_id)
            
            return connection_id
            
        except Exception as e:
            logger.error(f"WebSocket connection error: {e}")
            raise
    
    async def disconnect(self, connection_id: str):
        """Disconnect a WebSocket connection"""
        try:
            if connection_id in self.connections:
                connection = self.connections[connection_id]
                user_id = connection.user_id
                organization_id = connection.organization_id
                
                # Remove from connections
                del self.connections[connection_id]
                
                # Remove from user connections
                if user_id in self.user_connections:
                    self.user_connections[user_id].discard(connection_id)
                    if not self.user_connections[user_id]:
                        del self.user_connections[user_id]
                
                # Remove from organization connections
                if organization_id and organization_id in self.organization_connections:
                    self.organization_connections[organization_id].discard(connection_id)
                    if not self.organization_connections[organization_id]:
                        del self.organization_connections[organization_id]
                
                logger.info(f"WebSocket disconnected: connection_id={connection_id}")
                
        except Exception as e:
            logger.error(f"WebSocket disconnect error: {e}")
    
    async def send_to_connection(self, connection_id: str, data: Dict[str, Any]) -> bool:
        """Send data to a specific connection"""
        try:
            if connection_id in self.connections:
                websocket = self.connections[connection_id].websocket
                await websocket.send_text(json.dumps(data))
                return True
            return False
        except WebSocketDisconnect:
            await self.disconnect(connection_id)
            return False
        except Exception as e:
            logger.error(f"Error sending to connection {connection_id}: {e}")
            return False
    
    async def send_to_user(self, user_id: str, data: Dict[str, Any]) -> int:
        """Send data to all connections of a specific user"""
        sent_count = 0
        if user_id in self.user_connections:
            connection_ids = list(self.user_connections[user_id])  # Create copy to avoid modification during iteration
            for connection_id in connection_ids:
                if await self.send_to_connection(connection_id, data):
                    sent_count += 1
        return sent_count
    
    async def send_to_organization(self, organization_id: str, data: Dict[str, Any]) -> int:
        """Send data to all connections in an organization"""
        sent_count = 0
        if organization_id in self.organization_connections:
            connection_ids = list(self.organization_connections[organization_id])
            for connection_id in connection_ids:
                if await self.send_to_connection(connection_id, data):
                    sent_count += 1
        return sent_count
    
    async def broadcast_to_all(self, data: Dict[str, Any]) -> int:
        """Send data to all connected users"""
        sent_count = 0
        connection_ids = list(self.connections.keys())
        for connection_id in connection_ids:
            if await self.send_to_connection(connection_id, data):
                sent_count += 1
        return sent_count
    
    async def notify_threat_detected(self, user_id: str, scan_result: Dict[str, Any]):
        """Send real-time threat detection notification"""
        try:
            if scan_result.get('status') in ['potential_phishing', 'phishing']:
                risk_score = scan_result.get('risk_score', 0)
                explanation = scan_result.get('explanation', 'Threat detected')
                
                priority = "high" if risk_score >= 80 else "normal"
                
                notification = RealTimeNotification(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    notification_type=NotificationType.THREAT_DETECTED,
                    title=f"🚨 Threat Detected - Risk {risk_score:.0f}%",
                    message=explanation,
                    data={
                        "scan_result": scan_result,
                        "risk_score": risk_score,
                        "status": scan_result.get('status'),
                        "threat_sources": scan_result.get('threat_sources', []),
                        "detected_threats": scan_result.get('detected_threats', [])
                    },
                    timestamp=datetime.utcnow(),
                    priority=priority
                )
                
                await self.send_to_user(user_id, {
                    "type": "notification",
                    "notification": notification.to_dict()
                })
                
                logger.info(f"Sent threat notification to user {user_id}: risk_score={risk_score}")
                
        except Exception as e:
            logger.error(f"Error sending threat notification: {e}")
    
    async def send_scan_completed(self, user_id: str, scan_result: Dict[str, Any]):
        """Send scan completion notification"""
        try:
            await self.send_to_user(user_id, {
                "type": "scan_completed",
                "scan_result": scan_result,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Update statistics in real-time
            await self.send_dashboard_statistics(user_id)
            
        except Exception as e:
            logger.error(f"Error sending scan completion: {e}")
    
    async def send_dashboard_statistics(self, user_id: str):
        """Send real-time dashboard statistics"""
        try:
            db = get_database()
            
            # Get today's scans for the user
            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            tomorrow = today + timedelta(days=1)
            
            # Count today's scans
            today_scans = await db.email_scans.count_documents({
                "user_id": user_id,
                "created_at": {"$gte": today, "$lt": tomorrow}
            })
            
            # Count threats blocked
            threats_blocked = await db.email_scans.count_documents({
                "user_id": user_id,
                "created_at": {"$gte": today, "$lt": tomorrow},
                "scan_result": {"$in": ["potential_phishing", "phishing"]}
            })
            
            # Calculate average risk score
            pipeline = [
                {"$match": {"user_id": user_id, "created_at": {"$gte": today, "$lt": tomorrow}}},
                {"$group": {"_id": None, "avg_risk": {"$avg": "$risk_score"}}}
            ]
            
            avg_risk_result = await db.email_scans.aggregate(pipeline).to_list(1)
            avg_risk = avg_risk_result[0]["avg_risk"] if avg_risk_result else 0
            
            # Get recent scans
            recent_scans = await db.email_scans.find({
                "user_id": user_id
            }).sort("created_at", -1).limit(5).to_list(5)
            
            # Format recent scans
            formatted_scans = []
            for scan in recent_scans:
                formatted_scans.append({
                    "id": scan.get("id", str(scan.get("_id", ""))),
                    "email_subject": scan.get("email_subject", "")[:50],
                    "sender": scan.get("sender", ""),
                    "scan_result": scan.get("scan_result"),
                    "risk_score": scan.get("risk_score", 0),
                    "explanation": scan.get("explanation", ""),
                    "created_at": scan.get("created_at").isoformat() if scan.get("created_at") else ""
                })
            
            statistics = {
                "type": "statistics_update",
                "data": {
                    "today_scans": today_scans,
                    "threats_blocked": threats_blocked,
                    "avg_risk_score": round(avg_risk, 1),
                    "recent_scans": formatted_scans,
                    "last_updated": datetime.utcnow().isoformat()
                }
            }
            
            await self.send_to_user(user_id, statistics)
            
        except Exception as e:
            logger.error(f"Error sending dashboard statistics: {e}")
    
    async def send_threat_feed_update(self, threat_data: Dict[str, Any]):
        """Send global threat feed update to all users"""
        try:
            feed_update = {
                "type": "threat_feed_update",
                "data": {
                    "threat_type": threat_data.get("threat_type"),
                    "severity": threat_data.get("severity"),
                    "description": threat_data.get("description"),
                    "indicators": threat_data.get("indicators", []),
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
            sent_count = await self.broadcast_to_all(feed_update)
            logger.info(f"Sent threat feed update to {sent_count} connections")
            
        except Exception as e:
            logger.error(f"Error sending threat feed update: {e}")
    
    async def send_system_alert(self, alert_message: str, priority: str = "normal"):
        """Send system-wide alert to all users"""
        try:
            alert = {
                "type": "system_alert",
                "data": {
                    "message": alert_message,
                    "priority": priority,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
            sent_count = await self.broadcast_to_all(alert)
            logger.info(f"Sent system alert to {sent_count} connections: {alert_message}")
            
        except Exception as e:
            logger.error(f"Error sending system alert: {e}")
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get WebSocket connection statistics"""
        return {
            "total_connections": len(self.connections),
            "unique_users": len(self.user_connections),
            "organizations": len(self.organization_connections),
            "connections_by_user": {
                user_id: len(connections) 
                for user_id, connections in self.user_connections.items()
            }
        }
    
    async def start_background_tasks(self):
        """Start background tasks for real-time features"""
        # Statistics update task - every 30 seconds
        stats_task = asyncio.create_task(self._periodic_statistics_update())
        self.background_tasks.add(stats_task)
        stats_task.add_done_callback(self.background_tasks.discard)
        
        # Connection cleanup task - every 5 minutes
        cleanup_task = asyncio.create_task(self._connection_cleanup())
        self.background_tasks.add(cleanup_task)
        cleanup_task.add_done_callback(self.background_tasks.discard)
        
        logger.info("Real-time background tasks started")
    
    async def _periodic_statistics_update(self):
        """Periodically update statistics for all connected users"""
        while True:
            try:
                await asyncio.sleep(30)  # Update every 30 seconds
                
                for user_id in list(self.user_connections.keys()):
                    await self.send_dashboard_statistics(user_id)
                
            except Exception as e:
                logger.error(f"Error in periodic statistics update: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _connection_cleanup(self):
        """Clean up stale connections"""
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                
                current_time = datetime.utcnow()
                stale_connections = []
                
                for connection_id, connection in self.connections.items():
                    # Check if connection is older than 24 hours
                    if current_time - connection.connected_at > timedelta(hours=24):
                        stale_connections.append(connection_id)
                
                # Clean up stale connections
                for connection_id in stale_connections:
                    await self.disconnect(connection_id)
                
                if stale_connections:
                    logger.info(f"Cleaned up {len(stale_connections)} stale connections")
                
            except Exception as e:
                logger.error(f"Error in connection cleanup: {e}")
                await asyncio.sleep(600)  # Wait longer on error

# Global instance
realtime_manager = RealTimeManager()

# Helper functions for easy access
async def notify_threat_detected(user_id: str, scan_result: Dict[str, Any]):
    """Helper function to notify threat detection"""
    await realtime_manager.notify_threat_detected(user_id, scan_result)

async def notify_scan_completed(user_id: str, scan_result: Dict[str, Any]):
    """Helper function to notify scan completion"""
    await realtime_manager.send_scan_completed(user_id, scan_result)

async def update_dashboard_statistics(user_id: str):
    """Helper function to update dashboard statistics"""
    await realtime_manager.send_dashboard_statistics(user_id)

async def broadcast_threat_feed(threat_data: Dict[str, Any]):
    """Helper function to broadcast threat feed update"""
    await realtime_manager.send_threat_feed_update(threat_data)