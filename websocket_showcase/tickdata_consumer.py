"""
TickDataConsumer — WebSocket consumer for managing real-time tick and candle data,
and displaying live contract/trade results.

Showcase Features:
- Django Channels async consumer structure
- Real-time market data updates
- Connection lifecycle management
- Async task creation and cleanup
"""

import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer


class TickDataConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Handle new WebSocket connection."""
        await self.accept()
        print("✅ WebSocket connected")

        self.client_id = self.scope.get("query_string", b"client_id=unknown").decode()
        print(f"Client connected: {self.client_id}")

        # Groups for different live data feeds
        self.groups = [
            f"tick_data_{self.client_id}",
            f"trade_updates_{self.client_id}",
        ]
        for group in self.groups:
            await self.channel_layer.group_add(group, self.channel_name)

    async def disconnect(self, close_code):
        """Clean up on disconnect."""
        print(f"⚠️ Disconnecting {self.client_id}")
        for group in getattr(self, "groups", []):
            await self.channel_layer.group_discard(group, self.channel_name)
        await self.stop_tasks()

    async def receive(self, text_data):
        """Handle messages from the frontend."""
        try:
            data = json.loads(text_data)
            event = data.get("event")

            if event == "subscribe_ticks":
                symbol = data.get("symbol", "SYMBOL_XYZ")
                print(f"🟢 Subscribing to tick data for {symbol}")
                self.tick_task = asyncio.create_task(self.fake_tick_stream(symbol))

            elif event == "show_trade_results":
                print("📈 Simulating live trade updates")
                self.result_task = asyncio.create_task(self.fake_trade_results())

            elif event == "stop_all":
                await self.stop_tasks()
                print("🛑 All tasks stopped")

        except Exception as e:
            print("❌ Error in receive:", e)

    async def fake_tick_stream(self, symbol):
        """Simulate continuous tick data."""
        try:
            while True:
                await asyncio.sleep(1)
                price = round(100 + (5 * asyncio.get_running_loop().time() % 10), 2)
                await self.send_json({
                    "event": "tick_update",
                    "symbol": symbol,
                    "price": price,
                })
        except asyncio.CancelledError:
            print("🧹 Tick stream stopped")

    async def fake_trade_results(self):
        """Simulate live trade results (like contracts bought)."""
        results = [
            {"contract": "CALL", "status": "Won", "profit": 3.20},
            {"contract": "PUT", "status": "Lost", "profit": -2.10},
        ]
        try:
            for trade in results:
                await asyncio.sleep(2)
                await self.send_json({
                    "event": "trade_update",
                    "data": trade,
                })
        except asyncio.CancelledError:
            print("🧹 Trade result simulation stopped")

    async def stop_tasks(self):
        """Cancel all background tasks."""
        for task_name in ["tick_task", "result_task"]:
            task = getattr(self, task_name, None)
            if task and not task.done():
                task.cancel()

    async def send_json(self, payload):
        """Helper for sending JSON safely."""
        await self.send(text_data=json.dumps(payload))
