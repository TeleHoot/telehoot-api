from typing import Dict, Set, Optional
from fastapi import WebSocket, WebSocketException
from pydantic import BaseModel
import enum

class EventType(enum.StrEnum):
    JOIN = "join"
    LEAVE = "leave"
    START = "start"
    ANSWER = "answer"
    NEXT = "next"
    FINISH = "finish"
    ERROR = "error"
    END = "end"


class SessionRole(enum.StrEnum):
    HOST = "host"
    PARTICIPANT = "participant"


# События, которые может отправлять только хост
HOST_ONLY_EVENTS = {
    EventType.START,
    EventType.NEXT,
    EventType.FINISH,
    EventType.END
}


class Event(BaseModel):
    type: EventType
    data: dict
    session_id: str


class SessionMember(BaseModel):
    user_id: str
    username: str
    role: SessionRole
    websocket_id: str


class ConnectionManager:
    def __init__(self):
        # Map of session_id to set of WebSocket connections
        self.active_sessions: Dict[str, Set[WebSocket]] = {}
        # Map of WebSocket to session_id for quick lookup
        self.connection_sessions: Dict[WebSocket, str] = {}
        # Map of session_id to dict of user_id -> SessionMember
        self.session_members: Dict[str, Dict[str, SessionMember]] = {}
        # Map of websocket_id to WebSocket
        self.websockets: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, session_id: str, user_id: str, username: str, role: SessionRole):
        await websocket.accept()
        
        # Generate unique ID for the websocket
        websocket_id = str(id(websocket))
        
        # Initialize session structures if needed
        if session_id not in self.active_sessions:
            self.active_sessions[session_id] = set()
            self.session_members[session_id] = {}
        
        # Add connection
        self.active_sessions[session_id].add(websocket)
        self.connection_sessions[websocket] = session_id
        self.websockets[websocket_id] = websocket
        
        # Add member info
        self.session_members[session_id][user_id] = SessionMember(
            user_id=user_id,
            username=username,
            role=role,
            websocket_id=websocket_id
        )

    async def disconnect(self, websocket: WebSocket):
        session_id = self.connection_sessions.get(websocket)
        if session_id:
            self.active_sessions[session_id].remove(websocket)
            
            # Remove member info
            user_to_remove = None
            for user_id, member in self.session_members[session_id].items():
                if member.websocket_id == str(id(websocket)):
                    user_to_remove = user_id
                    break
            
            if user_to_remove:
                del self.session_members[session_id][user_to_remove]
            
            # Cleanup empty session
            if not self.active_sessions[session_id]:
                del self.active_sessions[session_id]
                del self.session_members[session_id]
            
            del self.connection_sessions[websocket]
            del self.websockets[str(id(websocket))]

    def get_member_role(self, websocket: WebSocket) -> Optional[SessionRole]:
        session_id = self.connection_sessions.get(websocket)
        if not session_id:
            return None
            
        for member in self.session_members[session_id].values():
            if member.websocket_id == str(id(websocket)):
                return member.role
        return None

    async def validate_event_permissions(self, websocket: WebSocket, event: Event):
        role = self.get_member_role(websocket)
        if not role:
            raise WebSocketException(code=4003, reason="Member not found in session")
            
        if event.type in HOST_ONLY_EVENTS and role != SessionRole.HOST:
            raise WebSocketException(code=4003, reason="Operation not permitted for participant role")

    async def broadcast_to_session(self, session_id: str, event: Event):
        if session_id in self.active_sessions:
            dead_connections = set()
            for connection in self.active_sessions[session_id]:
                try:
                    await connection.send_json(event.dict())
                except:
                    dead_connections.add(connection)
            
            # Clean up dead connections
            for dead_conn in dead_connections:
                await self.disconnect(dead_conn)

            # If this is an END event, close all connections after broadcasting
            if event.type == EventType.END:
                for connection in self.active_sessions[session_id].copy():
                    await self.disconnect(connection)

    async def send_personal_message(self, websocket: WebSocket, event: Event):
        try:
            await websocket.send_json(event.dict())
        except:
            await self.disconnect(websocket)

    def get_session_connections_count(self, session_id: str) -> int:
        """Get number of active connections in a session"""
        return len(self.active_sessions.get(session_id, set()))

    def get_session_host(self, session_id: str) -> Optional[SessionMember]:
        """Get the host of a session"""
        if session_id not in self.session_members:
            return None
        
        for member in self.session_members[session_id].values():
            if member.role == SessionRole.HOST:
                return member
        return None


# Global connection manager instance
manager = ConnectionManager() 