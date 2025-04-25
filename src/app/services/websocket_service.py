from fastapi import WebSocket, WebSocketDisconnect, HTTPException
from src.core.websocket import manager, Event, SessionRole
from src.app.api.v1.handlers import SessionEventHandler
from src.app.models import User
from src.core.uow import UnitOfWork
from src.core.repositories.mongo.session import SessionRepository
from uuid import uuid4


class WebSocketService:
    def __init__(self):
        self.session_repo = SessionRepository()

    async def validate_session(self, session_id: str, current_user: User):
        """Проверка существования сессии, создание если не существует"""
        async with UnitOfWork(use_mongodb=True) as uow:
            # Пробуем найти существующую сессию
            session = await self.session_repo.read_by_id(uow, session_id)
            
            # Если сессия не найдена, создаем новую
            if not session:
                session = await self.session_repo.create(
                    uow,
                    {
                        "_id": str(uuid4()),
                        "quiz_id": session_id,  # Временно используем session_id как quiz_id
                        "host_id": str(current_user.id),
                        "status": "active",
                        "settings": {},
                        "participants": []
                    }
                )
            
            return session

    @staticmethod
    def determine_role(session, current_user: User) -> SessionRole:
        """Определение роли пользователя в сессии"""
        return SessionRole.HOST if str(session.host_id) == str(current_user.id) else SessionRole.PARTICIPANT

    async def handle_connection(
        self,
        websocket: WebSocket,
        session_id: str,
        current_user: User
    ):
        # Валидация сессии и определение роли
        session = await self.validate_session(session_id, current_user)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
            
        role = self.determine_role(session, current_user)
        
        handler = SessionEventHandler(session_id, current_user, role)
        
        try:
            # Подключаем к WebSocket
            await manager.connect(
                websocket=websocket,
                session_id=session_id,
                user_id=str(current_user.id),
                username=current_user.telegram_username,
                role=role
            )
            
            # Оповещаем о подключении нового участника
            join_event = await handler.handle_join(websocket)
            await manager.broadcast_to_session(session_id, join_event)
            
            try:
                while True:
                    # Получаем и обрабатываем сообщения
                    data = await websocket.receive_json()
                    event = Event(**data)
                    
                    # Проверяем права доступа
                    await manager.validate_event_permissions(websocket, event)
                    
                    # Обрабатываем событие и получаем список событий для отправки
                    events_to_send = await handler.handle_event(event)
                    
                    # Отправляем все события участникам сессии
                    for ev in events_to_send:
                        await manager.broadcast_to_session(session_id, ev)
                    
            except WebSocketDisconnect:
                await self.handle_disconnect(websocket, handler)
                
        except Exception as e:
            await manager.disconnect(websocket)
            raise e

    @staticmethod
    async def handle_disconnect(websocket: WebSocket, handler: SessionEventHandler):
        if handler:
            # Оповещаем об отключении участника
            leave_event = await handler.handle_leave()
            await manager.broadcast_to_session(handler.session_id, leave_event)
        await manager.disconnect(websocket)


websocket_service = WebSocketService() 