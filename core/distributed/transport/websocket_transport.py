"""
WebSocket Transport – Windows Compatible (FIXED)
"""

import asyncio
import json
import threading
import time
import sqlite3
from typing import Dict, Callable, Optional
import websockets
from core.logger import get_logger

logger = get_logger()

class WebSocketTransport:
    def __init__(self, host: str = "0.0.0.0", port: int = 8765, db_path: str = "outbox.db"):
        self.host = host
        self.port = port
        self.db_path = db_path
        self._init_db()
        self._connections: Dict[str, websockets.WebSocketServerProtocol] = {}
        self._message_handler: Optional[Callable] = None
        self._server_thread = None

    def _init_db(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS outbox (
                message_id TEXT PRIMARY KEY,
                worker_id TEXT,
                payload TEXT,
                status TEXT,
                retries INTEGER DEFAULT 0,
                created_at REAL,
                last_attempt REAL
            )
        ''')
        conn.commit()
        conn.close()

    def start(self, message_handler: Callable):
        self._message_handler = message_handler
        self._server_thread = threading.Thread(target=self._run_server, daemon=True)
        self._server_thread.start()
        logger.info(f"WebSocket transport started on ws://{self.host}:{self.port}")

    def _run_server(self):
        asyncio.run(self._async_server())

    async def _async_server(self):
        async def handler(websocket):
            await self._handle_client(websocket)

        async with websockets.serve(handler, self.host, self.port):
            logger.info(f"WebSocket server running on ws://{self.host}:{self.port}")
            await asyncio.Future()

    async def _handle_client(self, websocket):
        worker_id = None
        try:
            raw = await asyncio.wait_for(websocket.recv(), timeout=10)
            data = json.loads(raw)
            
            if data.get("type") != "register":
                await websocket.close(1008, "First message must be register")
                return
            
            worker_id = data.get("payload", {}).get("worker_id")
            if not worker_id:
                await websocket.close(1008, "Missing worker_id")
                return
            
            self._connections[worker_id] = websocket
            logger.info(f"✅ Worker '{worker_id}' registered")
            await websocket.send(json.dumps({"type": "ack", "id": data.get("id")}))
            
            async for raw in websocket:
                try:
                    msg = json.loads(raw)
                    msg_type = msg.get("type")
                    
                    if msg_type == "heartbeat":
                        await websocket.send(json.dumps({"type": "ack", "id": msg.get("id")}))
                    elif msg_type == "job_result":
                        if self._message_handler:
                            from core.distributed.common.message import Message
                            message_obj = Message.from_dict(msg)
                            self._message_handler(message_obj, worker_id)
                    else:
                        if self._message_handler:
                            from core.distributed.common.message import Message
                            message_obj = Message.from_dict(msg)
                            self._message_handler(message_obj, worker_id)
                except Exception as e:
                    logger.error(f"Error: {e}")
                    
        except asyncio.TimeoutError:
            logger.error("Registration timeout")
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Worker {worker_id} disconnected")
        except Exception as e:
            logger.error(f"Handler error: {e}")
        finally:
            if worker_id and worker_id in self._connections:
                del self._connections[worker_id]

    def send_to_worker(self, worker_id: str, msg) -> bool:
        ws = self._connections.get(worker_id)
        if ws:
            if hasattr(msg, 'to_dict'):
                data = msg.to_dict()
            else:
                data = msg
            asyncio.run_coroutine_threadsafe(
                ws.send(json.dumps(data)),
                asyncio.get_event_loop()
            )
            return True
        return False

    def stop(self):
        logger.info("WebSocket transport stopped")