#!/usr/bin/env python3
"""Simple WebSocket client for testing robot status updates."""

import asyncio
import sys

import websockets


async def listen(robot_id: str):
    uri = f"ws://localhost:8000/ws/robots/{robot_id}"
    print(f"Connecting to {uri}...")

    async with websockets.connect(uri) as ws:
        print("Connected! Waiting for updates...\n")
        
        while True:
            message = await ws.recv()
            print(f"📡 Received: {message}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ws_client.py <robot_id>")
        sys.exit(1)

    robot_id = sys.argv[1]
    asyncio.run(listen(robot_id))
