"""
Multi-Channel Deployment Coordinator for Nexus Platform
=======================================================

Coordinates simultaneous deployment across all Nexus channels:
- REST API for web frontend integration
- CLI commands for administrative operations
- MCP server for AI agent integration
- WebSocket for real-time communication
- Unified session management across channels
- Load balancing and failover
"""

import asyncio
import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import signal
import sys

from nexus import Nexus
from nexus_enhanced_config import enhanced_config
from nexus_websocket_enhanced import enhanced_websocket_manager, MessageType, WebSocketMessage
from nexus_monitoring_system import monitoring_system, AlertLevel

logger = logging.getLogger(__name__)

class ChannelType(Enum):
    """Nexus deployment channels"""
    API = "api"
    CLI = "cli"
    MCP = "mcp"
    WEBSOCKET = "websocket"

@dataclass
class ChannelStatus:
    """Status of a deployment channel"""
    channel: ChannelType
    enabled: bool
    running: bool
    port: Optional[int] = None
    host: Optional[str] = None
    last_health_check: Optional[datetime] = None
    error_count: int = 0
    total_requests: int = 0
    active_connections: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "channel": self.channel.value,
            "enabled": self.enabled,
            "running": self.running,
            "port": self.port,
            "host": self.host,
            "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None,
            "error_count": self.error_count,
            "total_requests": self.total_requests,
            "active_connections": self.active_connections
        }

@dataclass
class SessionInfo:
    """Unified session information across channels"""
    session_id: str
    user_id: int
    channels: List[ChannelType] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    def update_activity(self, channel: ChannelType):
        """Update session activity"""
        self.last_activity = datetime.now()
        if channel not in self.channels:
            self.channels.append(channel)
    
    def is_expired(self, timeout_minutes: int = 60) -> bool:
        """Check if session is expired"""
        return (datetime.now() - self.last_activity).total_seconds() > (timeout_minutes * 60)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "channels": [c.value for c in self.channels],
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "duration_minutes": (self.last_activity - self.created_at).total_seconds() / 60
        }

class UnifiedSessionManager:
    """Manage sessions across all Nexus channels"""
    
    def __init__(self):
        self.sessions: Dict[str, SessionInfo] = {}
        self.user_sessions: Dict[int, List[str]] = {}
        self.cleanup_interval = 300  # 5 minutes
        self.session_timeout = 3600  # 1 hour
        self.cleanup_task: Optional[asyncio.Task] = None
    
    def create_session(self, session_id: str, user_id: int, channel: ChannelType,
                      ip_address: str = None, user_agent: str = None) -> SessionInfo:
        """Create or update a session"""
        if session_id in self.sessions:
            # Update existing session
            session = self.sessions[session_id]
            session.update_activity(channel)
        else:
            # Create new session
            session = SessionInfo(
                session_id=session_id,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent
            )
            session.update_activity(channel)
            self.sessions[session_id] = session
            
            # Map user to session
            if user_id not in self.user_sessions:
                self.user_sessions[user_id] = []
            self.user_sessions[user_id].append(session_id)
        
        return session
    
    def get_session(self, session_id: str) -> Optional[SessionInfo]:
        """Get session by ID"""
        return self.sessions.get(session_id)
    
    def get_user_sessions(self, user_id: int) -> List[SessionInfo]:
        """Get all sessions for a user"""
        session_ids = self.user_sessions.get(user_id, [])
        return [self.sessions[sid] for sid in session_ids if sid in self.sessions]
    
    def remove_session(self, session_id: str):
        """Remove session"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            user_id = session.user_id
            
            del self.sessions[session_id]
            
            # Remove from user sessions
            if user_id in self.user_sessions:
                self.user_sessions[user_id] = [
                    sid for sid in self.user_sessions[user_id] if sid != session_id
                ]
                if not self.user_sessions[user_id]:
                    del self.user_sessions[user_id]
    
    async def start_cleanup(self):
        """Start session cleanup task"""
        if self.cleanup_task is None or self.cleanup_task.done():
            self.cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def stop_cleanup(self):
        """Stop session cleanup task"""
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
    
    async def _cleanup_loop(self):
        """Cleanup expired sessions"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self._cleanup_expired_sessions()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Session cleanup error: {e}")
    
    async def _cleanup_expired_sessions(self):
        """Remove expired sessions"""
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            if session.is_expired(self.session_timeout // 60):
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            logger.info(f"Removing expired session: {session_id}")
            self.remove_session(session_id)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get session statistics"""
        now = datetime.now()
        
        # Channel usage statistics
        channel_stats = {}
        for channel in ChannelType:
            count = sum(1 for s in self.sessions.values() if channel in s.channels)
            channel_stats[channel.value] = count
        
        # Calculate average session duration
        durations = [
            (now - s.created_at).total_seconds() / 60 
            for s in self.sessions.values()
        ]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        return {
            "total_sessions": len(self.sessions),
            "unique_users": len(self.user_sessions),
            "average_duration_minutes": avg_duration,
            "channel_usage": channel_stats,
            "cleanup_interval_seconds": self.cleanup_interval,
            "session_timeout_seconds": self.session_timeout
        }

class MultiChannelLoadBalancer:
    """Load balancer for multi-channel requests"""
    
    def __init__(self):
        self.channel_weights: Dict[ChannelType, float] = {
            ChannelType.API: 1.0,
            ChannelType.CLI: 1.0,
            ChannelType.MCP: 1.0,
            ChannelType.WEBSOCKET: 1.0
        }
        self.request_counts: Dict[ChannelType, int] = {
            channel: 0 for channel in ChannelType
        }
        self.error_counts: Dict[ChannelType, int] = {
            channel: 0 for channel in ChannelType
        }
        self.response_times: Dict[ChannelType, List[float]] = {
            channel: [] for channel in ChannelType
        }
    
    def record_request(self, channel: ChannelType, response_time: float, success: bool):
        """Record request metrics for load balancing"""
        self.request_counts[channel] += 1
        
        if not success:
            self.error_counts[channel] += 1
        
        # Keep last 100 response times for average calculation
        self.response_times[channel].append(response_time)
        if len(self.response_times[channel]) > 100:
            self.response_times[channel] = self.response_times[channel][-100:]
        
        # Adjust weights based on performance
        self._adjust_weights()
    
    def _adjust_weights(self):
        """Automatically adjust channel weights based on performance"""
        for channel in ChannelType:
            total_requests = self.request_counts[channel]
            if total_requests > 10:  # Only adjust after sufficient data
                error_rate = self.error_counts[channel] / total_requests
                avg_response_time = sum(self.response_times[channel]) / len(self.response_times[channel]) if self.response_times[channel] else 1.0
                
                # Reduce weight for high error rates or slow response times
                weight = 1.0
                if error_rate > 0.05:  # > 5% error rate
                    weight *= (1.0 - error_rate)
                
                if avg_response_time > 5.0:  # > 5 second response time
                    weight *= (5.0 / avg_response_time)
                
                self.channel_weights[channel] = max(0.1, min(1.0, weight))
    
    def get_optimal_channel(self, preferred_channel: ChannelType = None) -> ChannelType:
        """Get optimal channel based on current load and performance"""
        if preferred_channel and self.channel_weights[preferred_channel] > 0.5:
            return preferred_channel
        
        # Return channel with highest weight
        return max(self.channel_weights.keys(), key=lambda c: self.channel_weights[c])
    
    def get_stats(self) -> Dict[str, Any]:
        """Get load balancer statistics"""
        avg_response_times = {}
        for channel, times in self.response_times.items():
            avg_response_times[channel.value] = sum(times) / len(times) if times else 0
        
        error_rates = {}
        for channel in ChannelType:
            total = self.request_counts[channel]
            error_rates[channel.value] = (self.error_counts[channel] / total) if total > 0 else 0
        
        return {
            "request_counts": {c.value: count for c, count in self.request_counts.items()},
            "error_counts": {c.value: count for c, count in self.error_counts.items()},
            "error_rates": error_rates,
            "average_response_times": avg_response_times,
            "channel_weights": {c.value: weight for c, weight in self.channel_weights.items()}
        }

class NexusMultiChannelCoordinator:
    """Main coordinator for multi-channel Nexus deployment"""
    
    def __init__(self):
        self.nexus_app: Optional[Nexus] = None
        self.session_manager = UnifiedSessionManager()
        self.load_balancer = MultiChannelLoadBalancer()
        
        # Channel status tracking
        self.channel_status: Dict[ChannelType, ChannelStatus] = {
            ChannelType.API: ChannelStatus(
                channel=ChannelType.API,
                enabled=True,
                running=False,
                port=enhanced_config.server.api_port,
                host=enhanced_config.server.api_host
            ),
            ChannelType.CLI: ChannelStatus(
                channel=ChannelType.CLI,
                enabled=True,
                running=False
            ),
            ChannelType.MCP: ChannelStatus(
                channel=ChannelType.MCP,
                enabled=True,
                running=False,
                port=enhanced_config.server.mcp_port,
                host=enhanced_config.server.mcp_host
            ),
            ChannelType.WEBSOCKET: ChannelStatus(
                channel=ChannelType.WEBSOCKET,
                enabled=enhanced_config.websocket.enabled,
                running=False
            )
        }
        
        self.running = False
        self.health_check_task: Optional[asyncio.Task] = None
        self.stats_task: Optional[asyncio.Task] = None
        
        # Setup signal handlers for graceful shutdown
        self._setup_signal_handlers()
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            asyncio.create_task(self.stop())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def initialize_nexus(self) -> Nexus:
        """Initialize enhanced Nexus application"""
        try:
            # Import and setup the enhanced Nexus app
            from nexus_enhanced_app import app as nexus_app
            
            self.nexus_app = nexus_app
            
            # Mark channels as running
            self.channel_status[ChannelType.API].running = True
            self.channel_status[ChannelType.CLI].running = True
            self.channel_status[ChannelType.MCP].running = True
            
            if enhanced_config.websocket.enabled:
                self.channel_status[ChannelType.WEBSOCKET].running = True
            
            logger.info("Enhanced Nexus application initialized")
            return self.nexus_app
            
        except Exception as e:
            logger.error(f"Failed to initialize Nexus: {e}")
            raise
    
    async def start(self):
        """Start multi-channel coordinator"""
        if self.running:
            return
        
        logger.info("🚀 Starting Nexus Multi-Channel Coordinator")
        
        try:
            # Initialize Nexus application
            await self.initialize_nexus()
            
            # Start monitoring system
            await monitoring_system.start()
            logger.info("✅ Monitoring system started")
            
            # Start session management
            await self.session_manager.start_cleanup()
            logger.info("✅ Session management started")
            
            # Start health checking
            self.health_check_task = asyncio.create_task(self._health_check_loop())
            
            # Start statistics collection
            self.stats_task = asyncio.create_task(self._stats_loop())
            
            self.running = True
            
            # Display channel status
            self._display_channel_status()
            
            logger.info("🎯 Multi-channel coordinator ready")
            
        except Exception as e:
            logger.error(f"Failed to start coordinator: {e}")
            await self.stop()
            raise
    
    async def stop(self):
        """Stop multi-channel coordinator"""
        if not self.running:
            return
        
        logger.info("🛑 Stopping Nexus Multi-Channel Coordinator")
        
        self.running = False
        
        # Stop background tasks
        if self.health_check_task:
            self.health_check_task.cancel()
        
        if self.stats_task:
            self.stats_task.cancel()
        
        # Stop session management
        await self.session_manager.stop_cleanup()
        
        # Stop monitoring system
        await monitoring_system.stop()
        
        # Mark channels as stopped
        for status in self.channel_status.values():
            status.running = False
        
        logger.info("✅ Multi-channel coordinator stopped")
    
    async def _health_check_loop(self):
        """Continuous health checking for all channels"""
        while self.running:
            try:
                await self._check_channel_health()
                await asyncio.sleep(60)  # Check every minute
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check loop error: {e}")
                await asyncio.sleep(10)
    
    async def _check_channel_health(self):
        """Check health of all channels"""
        for channel_type, status in self.channel_status.items():
            if not status.enabled:
                continue
            
            try:
                health_ok = await self._check_single_channel_health(channel_type)
                
                if not health_ok and status.running:
                    # Channel is unhealthy
                    status.error_count += 1
                    
                    if status.error_count > 5:  # Alert after 5 consecutive failures
                        await monitoring_system.alert_manager.create_alert(
                            alert_id=f"channel_{channel_type.value}_unhealthy",
                            level=AlertLevel.CRITICAL,
                            title=f"{channel_type.value.upper()} Channel Unhealthy",
                            message=f"Channel {channel_type.value} has failed health checks {status.error_count} times",
                            component=f"nexus_{channel_type.value}"
                        )
                else:
                    # Channel is healthy, reset error count
                    if status.error_count > 0:
                        await monitoring_system.alert_manager.resolve_alert(f"channel_{channel_type.value}_unhealthy")
                    status.error_count = 0
                
                status.last_health_check = datetime.now()
                
            except Exception as e:
                logger.error(f"Health check failed for {channel_type.value}: {e}")
                status.error_count += 1
    
    async def _check_single_channel_health(self, channel: ChannelType) -> bool:
        """Check health of a single channel"""
        try:
            if channel == ChannelType.API:
                # Check if API is responding
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    url = f"http://{enhanced_config.server.api_host}:{enhanced_config.server.api_port}/api/health"
                    async with session.get(url, timeout=5) as response:
                        return response.status == 200
            
            elif channel == ChannelType.MCP:
                # Check if MCP server is responding
                return True  # Simplified check
            
            elif channel == ChannelType.CLI:
                # CLI is always available if process is running
                return True
            
            elif channel == ChannelType.WEBSOCKET:
                # Check WebSocket manager health
                stats = enhanced_websocket_manager.get_stats()
                return stats["active_connections"] >= 0  # Basic check
            
            return False
            
        except Exception as e:
            logger.error(f"Single channel health check error for {channel.value}: {e}")
            return False
    
    async def _stats_loop(self):
        """Collect and log statistics"""
        while self.running:
            try:
                await self._collect_stats()
                await asyncio.sleep(300)  # Every 5 minutes
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Stats collection error: {e}")
                await asyncio.sleep(30)
    
    async def _collect_stats(self):
        """Collect comprehensive statistics"""
        try:
            # Update channel statistics
            for channel_type, status in self.channel_status.items():
                if channel_type == ChannelType.WEBSOCKET:
                    ws_stats = enhanced_websocket_manager.get_stats()
                    status.active_connections = ws_stats["active_connections"]
                    status.total_requests = ws_stats["total_messages_sent"]
            
            # Log summary statistics
            total_sessions = len(self.session_manager.sessions)
            total_connections = sum(s.active_connections for s in self.channel_status.values())
            
            logger.info(f"📊 Stats: {total_sessions} sessions, {total_connections} connections")
            
        except Exception as e:
            logger.error(f"Stats collection error: {e}")
    
    def _display_channel_status(self):
        """Display current channel status"""
        logger.info("🌐 Multi-Channel Status:")
        
        for channel_type, status in self.channel_status.items():
            if status.enabled:
                port_info = f":{status.port}" if status.port else ""
                host_info = f"{status.host}{port_info}" if status.host else ""
                
                status_icon = "✅" if status.running else "❌"
                logger.info(f"   {status_icon} {channel_type.value.upper()}: {host_info}")
        
        # Display configuration summary
        logger.info("⚙️  Configuration:")
        logger.info(f"   • Environment: {enhanced_config.environment}")
        logger.info(f"   • CORS Origins: {len(enhanced_config.get_cors_origins())}")
        logger.info(f"   • WebSocket Max Connections: {enhanced_config.enhanced_websocket.max_connections}")
        logger.info(f"   • Cache TTL: {enhanced_config.performance.cache_ttl_seconds}s")
        logger.info(f"   • Request Timeout: {enhanced_config.performance.request_timeout}s")
    
    def get_comprehensive_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        return {
            "timestamp": datetime.now().isoformat(),
            "coordinator": {
                "running": self.running,
                "uptime_seconds": time.time() - (time.time() if self.running else 0)
            },
            "channels": {c.value: s.to_dict() for c, s in self.channel_status.items()},
            "sessions": self.session_manager.get_stats(),
            "load_balancer": self.load_balancer.get_stats(),
            "websocket": enhanced_websocket_manager.get_stats(),
            "configuration": {
                "environment": enhanced_config.environment,
                "cors_origins": len(enhanced_config.get_cors_origins()),
                "cache_ttl": enhanced_config.performance.cache_ttl_seconds,
                "request_timeout": enhanced_config.performance.request_timeout,
                "max_concurrent_requests": enhanced_config.performance.max_concurrent_requests
            }
        }
    
    async def run_forever(self):
        """Run coordinator until stopped"""
        await self.start()
        
        try:
            # Start the actual Nexus application
            if self.nexus_app:
                logger.info("🎯 Starting Nexus platform...")
                self.nexus_app.start()  # This blocks until stopped
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        except Exception as e:
            logger.error(f"Nexus application error: {e}")
        finally:
            await self.stop()

# Global coordinator instance
coordinator = NexusMultiChannelCoordinator()

# CLI function for standalone execution
async def main():
    """Main entry point for multi-channel coordinator"""
    try:
        await coordinator.run_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Coordinator error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

# Export for use in other modules
__all__ = [
    'ChannelType',
    'ChannelStatus',
    'SessionInfo',
    'UnifiedSessionManager',
    'MultiChannelLoadBalancer',
    'NexusMultiChannelCoordinator',
    'coordinator'
]