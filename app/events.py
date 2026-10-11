"""
Real-time event publisher for Minaram Cup Tournament Management System.
Supports Server-Sent Events (SSE) and asynchronous notification across
the desktop manager and connected website clients.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Set

logger = logging.getLogger("minaram_cup.events")

class EventBroadcaster:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.subscribers: Set[asyncio.Queue] = set()
            cls._instance._loop = None
        return cls._instance

    def set_loop(self, loop: asyncio.AbstractEventLoop):
        self._loop = loop

    def broadcast(self, event_type: str, entity_id: Optional[int] = None, data: Optional[Dict[str, Any]] = None):
        """Broadcast a tournament update event to all connected clients."""
        payload = {
            "type": event_type,
            "entity_id": entity_id,
            "data": data or {},
            "timestamp": datetime.now().isoformat(),
        }
        json_data = json.dumps(payload)

        # Notify all active SSE queues
        dead_queues = set()
        for q in list(self.subscribers):
            try:
                q.put_nowait(json_data)
            except Exception:
                dead_queues.add(q)

        self.subscribers.difference_update(dead_queues)
        logger.info(f"Broadcasted live event: {event_type} (listeners: {len(self.subscribers)})")

    def broadcast_from_thread(self, event_type: str, entity_id: Optional[int] = None, data: Optional[Dict[str, Any]] = None):
        """Thread-safe broadcast helper when called from desktop GUI or worker thread."""
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self.broadcast, event_type, entity_id, data)
        else:
            self.broadcast(event_type, entity_id, data)

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self.subscribers.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue):
        self.subscribers.discard(q)


broadcaster = EventBroadcaster()
