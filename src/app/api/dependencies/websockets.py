from typing import Annotated

from fastapi import Depends

from src import core


class WebSocketController:
    def __init__(self):
        self.manager = core.websockets.get_websocket_manager()
        self.router = core.websockets.get_websocket_router()


Controller = Annotated[WebSocketController, Depends()]
