"""
Thread-safe Session Manager for YouTube Analytics Chat API.
FIXED: Replaces global SESSION_MEMORY with proper thread-safe implementation.
"""

import threading
import time
import uuid
import logging
from collections import OrderedDict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class SessionMessage:
    """Model for storing session messages."""
    timestamp: datetime
    user_message: str
    ai_response: str
    csv_path: str
    session_id: str

class ThreadSafeSessionManager:
    """
    Thread-safe session manager with memory limits and automatic cleanup.
    FIXED: Prevents memory leaks and race conditions.
    """
    
    def __init__(self, 
                 max_sessions: int = 1000,
                 max_messages_per_session: int = 50,
                 session_timeout_hours: int = 24,
                 cleanup_interval_minutes: int = 30):
        """
        Initialize the session manager.
        
        Args:
            max_sessions (int): Maximum number of concurrent sessions
            max_messages_per_session (int): Maximum messages per session
            session_timeout_hours (int): Hours after which sessions expire
            cleanup_interval_minutes (int): Minutes between cleanup runs
        """
        self._sessions: Dict[str, List[SessionMessage]] = OrderedDict()
        self._lock = threading.RLock()  # Reentrant lock for nested calls
        self._max_sessions = max_sessions
        self._max_messages_per_session = max_messages_per_session
        self._session_timeout = timedelta(hours=session_timeout_hours)
        self._cleanup_interval = timedelta(minutes=cleanup_interval_minutes)
        self._last_cleanup = datetime.now()
        
        # Statistics
        self._total_sessions_created = 0
        self._total_messages_stored = 0
        self._sessions_cleaned_up = 0
        
        logger.info(f"Session manager initialized with limits: {max_sessions} sessions, "
                   f"{max_messages_per_session} messages/session, {session_timeout_hours}h timeout")
    
    def add_message(self, session_id: str, user_message: str, ai_response: str, csv_path: str) -> None:
        """
        Add a message to a session with automatic cleanup and limits.
        FIXED: Thread-safe with proper memory management.
        
        Args:
            session_id (str): Session identifier
            user_message (str): User's message
            ai_response (str): AI's response
            csv_path (str): CSV file path used
        """
        with self._lock:
            # FIXED: Automatic cleanup when needed
            self._cleanup_if_needed()
            
            # FIXED: Limit total sessions
            if session_id not in self._sessions and len(self._sessions) >= self._max_sessions:
                # Remove oldest session
                oldest_session_id = next(iter(self._sessions))
                self._remove_session(oldest_session_id)
                logger.warning(f"Removed oldest session {oldest_session_id} due to session limit")
            
            # Create session if it doesn't exist
            if session_id not in self._sessions:
                self._sessions[session_id] = []
                self._total_sessions_created += 1
                logger.debug(f"Created new session: {session_id}")
            
            # Create message
            message = SessionMessage(
                timestamp=datetime.now(),
                user_message=user_message,
                ai_response=ai_response,
                csv_path=csv_path,
                session_id=session_id
            )
            
            # Add message to session
            self._sessions[session_id].append(message)
            self._total_messages_stored += 1
            
            # FIXED: Limit messages per session
            if len(self._sessions[session_id]) > self._max_messages_per_session:
                # Remove oldest messages
                removed_count = len(self._sessions[session_id]) - self._max_messages_per_session
                self._sessions[session_id] = self._sessions[session_id][-self._max_messages_per_session:]
                logger.debug(f"Removed {removed_count} old messages from session {session_id}")
            
            # Move session to end (LRU)
            self._sessions.move_to_end(session_id)
            
            logger.debug(f"Added message to session {session_id}. "
                        f"Session has {len(self._sessions[session_id])} messages")
    
    def get_session_context(self, session_id: str, max_messages: int = 3) -> str:
        """
        Get conversation context from session with thread safety.
        FIXED: Proper locking and error handling.
        
        Args:
            session_id (str): Session identifier
            max_messages (int): Maximum number of previous messages to include
            
        Returns:
            str: Formatted conversation context
        """
        with self._lock:
            if session_id not in self._sessions:
                return ""
            
            messages = self._sessions[session_id]
            if not messages:
                return ""
            
            # Get last N messages
            recent_messages = messages[-max_messages:]
            
            # Move session to end (LRU)
            self._sessions.move_to_end(session_id)
            
            # Format context
            context_parts = []
            for i, msg in enumerate(recent_messages, 1):
                context_parts.append(f"Previous Q{i}: {msg.user_message}")
                context_parts.append(f"Previous A{i}: {msg.ai_response[:200]}...")  # Truncate long responses
            
            return "\n".join(context_parts)
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session information with thread safety.
        
        Args:
            session_id (str): Session identifier
            
        Returns:
            dict: Session information or None if not found
        """
        with self._lock:
            if session_id not in self._sessions:
                return None
            
            messages = self._sessions[session_id]
            if not messages:
                return None
            
            first_message = messages[0]
            last_message = messages[-1]
            
            return {
                'session_id': session_id,
                'message_count': len(messages),
                'created_at': first_message.timestamp.isoformat(),
                'last_activity': last_message.timestamp.isoformat(),
                'csv_path': last_message.csv_path
            }
    
    def remove_session(self, session_id: str) -> bool:
        """
        Remove a session with thread safety.
        
        Args:
            session_id (str): Session identifier
            
        Returns:
            bool: True if session was removed, False if not found
        """
        with self._lock:
            return self._remove_session(session_id)
    
    def _remove_session(self, session_id: str) -> bool:
        """
        Internal method to remove a session (must be called with lock held).
        
        Args:
            session_id (str): Session identifier
            
        Returns:
            bool: True if session was removed, False if not found
        """
        if session_id in self._sessions:
            del self._sessions[session_id]
            self._sessions_cleaned_up += 1
            logger.debug(f"Removed session: {session_id}")
            return True
        return False
    
    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions with thread safety.
        FIXED: Proper cleanup with statistics.
        
        Returns:
            int: Number of sessions cleaned up
        """
        with self._lock:
            current_time = datetime.now()
            sessions_to_remove = []
            
            for session_id, messages in self._sessions.items():
                if messages and (current_time - messages[-1].timestamp) > self._session_timeout:
                    sessions_to_remove.append(session_id)
            
            # Remove expired sessions
            for session_id in sessions_to_remove:
                self._remove_session(session_id)
            
            self._last_cleanup = current_time
            
            if sessions_to_remove:
                logger.info(f"Cleaned up {len(sessions_to_remove)} expired sessions")
            
            return len(sessions_to_remove)
    
    def _cleanup_if_needed(self) -> None:
        """
        Perform cleanup if enough time has passed.
        """
        current_time = datetime.now()
        if (current_time - self._last_cleanup) > self._cleanup_interval:
            self.cleanup_expired_sessions()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get session manager statistics with thread safety.
        
        Returns:
            dict: Session statistics
        """
        with self._lock:
            total_messages = sum(len(messages) for messages in self._sessions.values())
            
            return {
                'active_sessions': len(self._sessions),
                'total_messages': total_messages,
                'total_sessions_created': self._total_sessions_created,
                'total_messages_stored': self._total_messages_stored,
                'sessions_cleaned_up': self._sessions_cleaned_up,
                'max_sessions': self._max_sessions,
                'max_messages_per_session': self._max_messages_per_session,
                'session_timeout_hours': self._session_timeout.total_seconds() / 3600,
                'last_cleanup': self._last_cleanup.isoformat()
            }
    
    def get_all_sessions(self) -> List[Dict[str, Any]]:
        """
        Get information about all active sessions.
        
        Returns:
            list: List of session information dictionaries
        """
        with self._lock:
            return [
                self.get_session_info(session_id) 
                for session_id in self._sessions.keys()
            ]
    
    def clear_all_sessions(self) -> int:
        """
        Clear all sessions (for testing or emergency cleanup).
        
        Returns:
            int: Number of sessions cleared
        """
        with self._lock:
            session_count = len(self._sessions)
            self._sessions.clear()
            self._sessions_cleaned_up += session_count
            logger.warning(f"Cleared all {session_count} sessions")
            return session_count

# FIXED: Global instance with proper initialization
session_manager = ThreadSafeSessionManager(
    max_sessions=1000,
    max_messages_per_session=50,
    session_timeout_hours=24,
    cleanup_interval_minutes=30
) 