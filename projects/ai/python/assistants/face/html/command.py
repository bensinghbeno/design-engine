# command.py
import asyncio
import sys
import websockets

async def send_command(cmd):
    try:
        async with websockets.connect("ws://localhost:8765") as websocket:
            await websocket.send(cmd)
            print(f"✅ Sent command: {cmd}")
    except Exception as e:
        print(f"❌ Failed to connect/send: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 command.py [smile|laugh|talk|normal]")
    else:
        asyncio.run(send_command(sys.argv[1]))
