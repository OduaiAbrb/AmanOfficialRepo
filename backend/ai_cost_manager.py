"""
AI Cost Management System for Aman Cybersecurity Platform
Tracks API usage, implements smart caching, and provides cost analytics
"""

import os
import json
import hashlib
import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict
import uuid

from database import get_database

logger = logging.getLogger(__name__)

class AIProvider(str, Enum):
    GEMINI = "gemini"
    OPENAI = "openai"
    CLAUDE = "claude"

@dataclass
class AIUsageRecord:
    """Record of AI API usage"""
    id: str
    user_id: str
    provider: AIProvider
    model: str
    operation_type: str  # email_scan, link_scan, content_analysis
    input_tokens: int
    output_tokens: int
    estimated_cost: float
    response_time_ms: int
    cache_hit: bool
    timestamp: datetime
    metadata: Dict[str, Any]

@dataclass
class CacheEntry:
    """Cached AI response entry"""
    content_hash: str
    provider: AIProvider
    model: str
    response_data: Dict[str, Any]
    created_at: datetime
    accessed_count: int
    last_accessed: datetime
    expires_at: datetime

class AIUsageTracker:
    """Tracks AI API usage and costs"""
    
    def __init__(self):
        # Pricing per 1K tokens (in USD) - approximate values
        self.token_pricing = {
            AIProvider.GEMINI: {
                "gemini-2.0-flash": {
                    "input": 0.000075,   # $0.075 per 1M tokens
                    "output": 0.0003     # $0.30 per 1M tokens
                }
            },
            AIProvider.OPENAI: {
                "gpt-4": {"input": 0.03, "output": 0.06},
                "gpt-3.5-turbo": {"input": 0.001, "output": 0.002}
            },
            AIProvider.CLAUDE: {
                "claude-3": {"input": 0.015, "output": 0.075}
            }
        }
        
        # Usage limits per user per day (to prevent abuse)
        self.daily_limits = {
            "free_tier": {"requests": 100, "tokens": 50000, "cost": 0.50},
            "premium": {"requests": 1000, "tokens": 500000, "cost": 5.00},
            "enterprise": {"requests": 10000, "tokens": 5000000, "cost": 50.00}
        }
    
    async def record_usage(
        self, 
        user_id: str, 
        provider: AIProvider, 
        model: str,
        operation_type: str,
        input_tokens: int,
        output_tokens: int,
        response_time_ms: int,
        cache_hit: bool = False,
        metadata: Dict[str, Any] = None
    ) -> str:
        """Record AI API usage"""
        try:
            # Calculate estimated cost
            estimated_cost = self._calculate_cost(provider, model, input_tokens, output_tokens)
            
            # Create usage record
            record = AIUsageRecord(
                id=str(uuid.uuid4()),
                user_id=user_id,
                provider=provider,
                model=model,
                operation_type=operation_type,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                estimated_cost=estimated_cost,
                response_time_ms=response_time_ms,
                cache_hit=cache_hit,
                timestamp=datetime.utcnow(),
                metadata=metadata or {}
            )
            
            # Store in database
            db = get_database()
            await db.ai_usage.insert_one({
                **asdict(record),
                "provider": provider.value,
                "timestamp": record.timestamp
            })
            
            logger.info(
                f"AI usage recorded: user={user_id}, provider={provider.value}, "
                f"tokens={input_tokens + output_tokens}, cost=${estimated_cost:.4f}, "
                f"cache_hit={cache_hit}"
            )
            
            return record.id
            
        except Exception as e:
            logger.error(f"Failed to record AI usage: {e}")
            return ""
    
    def _calculate_cost(
        self, 
        provider: AIProvider, 
        model: str, 
        input_tokens: int, 
        output_tokens: int
    ) -> float:
        """Calculate estimated cost based on token usage"""
        try:
            if provider not in self.token_pricing or model not in self.token_pricing[provider]:
                # Default cost estimate if pricing not available
                return (input_tokens + output_tokens) * 0.0001  # $0.1 per 1K tokens
            
            pricing = self.token_pricing[provider][model]
            input_cost = (input_tokens / 1000) * pricing["input"]
            output_cost = (output_tokens / 1000) * pricing["output"]
            
            return input_cost + output_cost
            
        except Exception as e:
            logger.error(f"Cost calculation error: {e}")
            return 0.0
    
    async def check_usage_limits(self, user_id: str, user_tier: str = "free_tier") -> Tuple[bool, Dict[str, Any]]:
        """Check if user has exceeded daily usage limits"""
        try:
            # Get user's usage for today
            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            tomorrow = today + timedelta(days=1)
            
            db = get_database()
            
            # Aggregate today's usage
            pipeline = [
                {
                    "$match": {
                        "user_id": user_id,
                        "timestamp": {"$gte": today, "$lt": tomorrow}
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "total_requests": {"$sum": 1},
                        "total_tokens": {"$sum": {"$add": ["$input_tokens", "$output_tokens"]}},
                        "total_cost": {"$sum": "$estimated_cost"}
                    }
                }
            ]
            
            usage_result = await db.ai_usage.aggregate(pipeline).to_list(1)
            
            if not usage_result:
                current_usage = {"total_requests": 0, "total_tokens": 0, "total_cost": 0.0}
            else:
                current_usage = usage_result[0]
            
            # Check against limits
            limits = self.daily_limits.get(user_tier, self.daily_limits["free_tier"])
            
            within_limits = (
                current_usage["total_requests"] < limits["requests"] and
                current_usage["total_tokens"] < limits["tokens"] and
                current_usage["total_cost"] < limits["cost"]
            )
            
            usage_info = {
                "within_limits": within_limits,
                "current_usage": current_usage,
                "limits": limits,
                "remaining": {
                    "requests": max(0, limits["requests"] - current_usage["total_requests"]),
                    "tokens": max(0, limits["tokens"] - current_usage["total_tokens"]),
                    "cost": max(0, limits["cost"] - current_usage["total_cost"])
                }
            }
            
            return within_limits, usage_info
            
        except Exception as e:
            logger.error(f"Usage limit check error: {e}")
            return True, {}  # Allow by default on error
    
    async def get_user_usage_analytics(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get user's usage analytics for specified days"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            db = get_database()
            
            # Usage by day
            daily_pipeline = [
                {
                    "$match": {
                        "user_id": user_id,
                        "timestamp": {"$gte": start_date}
                    }
                },
                {
                    "$group": {
                        "_id": {
                            "$dateToString": {
                                "format": "%Y-%m-%d",
                                "date": "$timestamp"
                            }
                        },
                        "requests": {"$sum": 1},
                        "tokens": {"$sum": {"$add": ["$input_tokens", "$output_tokens"]}},
                        "cost": {"$sum": "$estimated_cost"},
                        "cache_hits": {"$sum": {"$cond": ["$cache_hit", 1, 0]}}
                    }
                },
                {"$sort": {"_id": 1}}
            ]
            
            daily_usage = await db.ai_usage.aggregate(daily_pipeline).to_list(days + 1)
            
            # Usage by operation type
            operation_pipeline = [
                {
                    "$match": {
                        "user_id": user_id,
                        "timestamp": {"$gte": start_date}
                    }
                },
                {
                    "$group": {
                        "_id": "$operation_type",
                        "requests": {"$sum": 1},
                        "tokens": {"$sum": {"$add": ["$input_tokens", "$output_tokens"]}},
                        "cost": {"$sum": "$estimated_cost"},
                        "avg_response_time": {"$avg": "$response_time_ms"}
                    }
                }
            ]
            
            operation_usage = await db.ai_usage.aggregate(operation_pipeline).to_list(10)
            
            # Overall stats
            total_pipeline = [
                {
                    "$match": {
                        "user_id": user_id,
                        "timestamp": {"$gte": start_date}
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "total_requests": {"$sum": 1},
                        "total_tokens": {"$sum": {"$add": ["$input_tokens", "$output_tokens"]}},
                        "total_cost": {"$sum": "$estimated_cost"},
                        "cache_hit_rate": {"$avg": {"$cond": ["$cache_hit", 1, 0]}},
                        "avg_response_time": {"$avg": "$response_time_ms"}
                    }
                }
            ]
            
            total_stats = await db.ai_usage.aggregate(total_pipeline).to_list(1)
            total = total_stats[0] if total_stats else {}
            
            return {
                "period_days": days,
                "daily_usage": daily_usage,
                "usage_by_operation": operation_usage,
                "total_stats": total,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Usage analytics error: {e}")
            return {}

class SmartCacheManager:
    """Manages AI response caching to reduce costs"""
    
    def __init__(self, cache_ttl_hours: int = 24, max_cache_size: int = 10000):
        self.cache_ttl = timedelta(hours=cache_ttl_hours)
        self.max_cache_size = max_cache_size
    
    def _generate_content_hash(self, content: str, provider: AIProvider, model: str) -> str:
        """Generate hash for content caching"""
        content_key = f"{provider.value}:{model}:{content}"
        return hashlib.sha256(content_key.encode()).hexdigest()[:16]
    
    async def get_cached_response(
        self, 
        content: str, 
        provider: AIProvider, 
        model: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached AI response if available"""
        try:
            content_hash = self._generate_content_hash(content, provider, model)
            
            db = get_database()
            cache_entry = await db.ai_cache.find_one({
                "content_hash": content_hash,
                "provider": provider.value,
                "model": model,
                "expires_at": {"$gt": datetime.utcnow()}
            })
            
            if cache_entry:
                # Update access statistics
                await db.ai_cache.update_one(
                    {"_id": cache_entry["_id"]},
                    {
                        "$inc": {"accessed_count": 1},
                        "$set": {"last_accessed": datetime.utcnow()}
                    }
                )
                
                logger.info(f"Cache hit for content hash: {content_hash}")
                return cache_entry["response_data"]
            
            return None
            
        except Exception as e:
            logger.error(f"Cache retrieval error: {e}")
            return None
    
    async def store_response(
        self, 
        content: str, 
        provider: AIProvider, 
        model: str, 
        response_data: Dict[str, Any]
    ) -> bool:
        """Store AI response in cache"""
        try:
            content_hash = self._generate_content_hash(content, provider, model)
            
            cache_entry = {
                "content_hash": content_hash,
                "provider": provider.value,
                "model": model,
                "response_data": response_data,
                "created_at": datetime.utcnow(),
                "accessed_count": 1,
                "last_accessed": datetime.utcnow(),
                "expires_at": datetime.utcnow() + self.cache_ttl
            }
            
            db = get_database()
            
            # Upsert cache entry
            await db.ai_cache.update_one(
                {
                    "content_hash": content_hash,
                    "provider": provider.value,
                    "model": model
                },
                {"$set": cache_entry},
                upsert=True
            )
            
            # Clean up old cache entries if needed
            await self._cleanup_cache()
            
            logger.info(f"Response cached for hash: {content_hash}")
            return True
            
        except Exception as e:
            logger.error(f"Cache storage error: {e}")
            return False
    
    async def _cleanup_cache(self):
        """Clean up expired and least used cache entries"""
        try:
            db = get_database()
            
            # Remove expired entries
            await db.ai_cache.delete_many({
                "expires_at": {"$lt": datetime.utcnow()}
            })
            
            # Check cache size
            cache_count = await db.ai_cache.count_documents({})
            
            if cache_count > self.max_cache_size:
                # Remove least accessed entries
                excess_count = cache_count - self.max_cache_size
                
                old_entries = await db.ai_cache.find({}).sort([
                    ("accessed_count", 1),
                    ("last_accessed", 1)
                ]).limit(excess_count).to_list(excess_count)
                
                if old_entries:
                    old_ids = [entry["_id"] for entry in old_entries]
                    await db.ai_cache.delete_many({"_id": {"$in": old_ids}})
                    
                    logger.info(f"Cleaned up {len(old_ids)} old cache entries")
            
        except Exception as e:
            logger.error(f"Cache cleanup error: {e}")
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        try:
            db = get_database()
            
            # Cache statistics
            pipeline = [
                {
                    "$group": {
                        "_id": None,
                        "total_entries": {"$sum": 1},
                        "total_accesses": {"$sum": "$accessed_count"},
                        "avg_accesses": {"$avg": "$accessed_count"},
                        "oldest_entry": {"$min": "$created_at"},
                        "newest_entry": {"$max": "$created_at"}
                    }
                }
            ]
            
            stats = await db.ai_cache.aggregate(pipeline).to_list(1)
            
            # Provider breakdown
            provider_pipeline = [
                {
                    "$group": {
                        "_id": "$provider",
                        "count": {"$sum": 1},
                        "total_accesses": {"$sum": "$accessed_count"}
                    }
                }
            ]
            
            provider_stats = await db.ai_cache.aggregate(provider_pipeline).to_list(10)
            
            return {
                "overall": stats[0] if stats else {},
                "by_provider": provider_stats,
                "max_cache_size": self.max_cache_size,
                "cache_ttl_hours": self.cache_ttl.total_seconds() / 3600
            }
            
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {}

# Global instances
usage_tracker = AIUsageTracker()
cache_manager = SmartCacheManager()

# Helper functions
async def record_ai_usage(
    user_id: str, 
    provider: str, 
    model: str,
    operation_type: str,
    input_tokens: int,
    output_tokens: int,
    response_time_ms: int,
    cache_hit: bool = False,
    metadata: Dict[str, Any] = None
) -> str:
    """Helper function to record AI usage"""
    provider_enum = AIProvider(provider.lower())
    return await usage_tracker.record_usage(
        user_id, provider_enum, model, operation_type,
        input_tokens, output_tokens, response_time_ms, cache_hit, metadata
    )

async def check_ai_usage_limits(user_id: str, user_tier: str = "free_tier") -> Tuple[bool, Dict[str, Any]]:
    """Helper function to check usage limits"""
    return await usage_tracker.check_usage_limits(user_id, user_tier)

async def get_cached_ai_response(content: str, provider: str, model: str) -> Optional[Dict[str, Any]]:
    """Helper function to get cached response"""
    provider_enum = AIProvider(provider.lower())
    return await cache_manager.get_cached_response(content, provider_enum, model)

async def cache_ai_response(content: str, provider: str, model: str, response_data: Dict[str, Any]) -> bool:
    """Helper function to cache AI response"""
    provider_enum = AIProvider(provider.lower())
    return await cache_manager.store_response(content, provider_enum, model, response_data)