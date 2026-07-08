"""In-memory session store for Phase 6 - Session Context Memory."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Message:
    """A single message in a conversation."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class Session:
    """A chat session with conversation history."""
    session_id: str
    messages: List[Message] = field(default_factory=list)
    last_mentioned_scheme: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    last_active: float = field(default_factory=time.time)
    
    def add_message(self, role: str, content: str) -> None:
        """Add a message to the session."""
        self.messages.append(Message(role=role, content=content))
        self.last_active = time.time()
    
    def get_recent_messages(self, limit: int = 5) -> List[Dict[str, str]]:
        """Get recent messages for context (last N turns)."""
        recent = self.messages[-limit:] if len(self.messages) > limit else self.messages
        return [{"role": msg.role, "content": msg.content} for msg in recent]
    
    def is_expired(self, ttl_seconds: int = 3600) -> bool:
        """Check if session has expired based on TTL."""
        return (time.time() - self.last_active) > ttl_seconds


class SessionStore:
    """In-memory store for chat sessions."""
    
    def __init__(self, ttl_seconds: int = 3600, max_messages: int = 20):
        """
        Initialize session store.
        
        Args:
            ttl_seconds: Time-to-live for inactive sessions (default: 1 hour)
            max_messages: Maximum messages per session (default: 20)
        """
        self.sessions: Dict[str, Session] = {}
        self.ttl_seconds = ttl_seconds
        self.max_messages = max_messages
    
    def create_session(self, session_id: Optional[str] = None) -> Session:
        """
        Create a new session.
        
        Args:
            session_id: Optional session ID (generates UUID if not provided)
            
        Returns:
            New Session object
        """
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        session = Session(session_id=session_id)
        self.sessions[session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """
        Get an existing session by ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session object if exists and not expired, None otherwise
        """
        session = self.sessions.get(session_id)
        if session is None:
            return None
        
        if session.is_expired(self.ttl_seconds):
            del self.sessions[session_id]
            return None
        
        return session
    
    def get_or_create_session(self, session_id: str) -> Session:
        """
        Get existing session or create new one.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session object
        """
        session = self.get_session(session_id)
        if session is None:
            session = self.create_session(session_id)
        return session
    
    def cleanup_expired(self) -> int:
        """
        Remove expired sessions from store.
        
        Returns:
            Number of sessions removed
        """
        expired_ids = [
            sid for sid, session in self.sessions.items()
            if session.is_expired(self.ttl_seconds)
        ]
        for sid in expired_ids:
            del self.sessions[sid]
        return len(expired_ids)
    
    def clear_all(self) -> None:
        """Clear all sessions (useful for testing)."""
        self.sessions.clear()
