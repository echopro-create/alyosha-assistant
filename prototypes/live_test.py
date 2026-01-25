import asyncio
import websockets
import json
import base64
import os
import sys

# Add parent directory to path to import config
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
import config

HOST = "generativelanguage.googleapis.com"
MODEL = "gemini-2.0-flash-exp"
URI = f"wss://{HOST}/ws/google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContent?key={config.GEMINI_API_KEY}"


async def run_live_test():
    print(f"Connecting to {URI[:50]}...")
    async with websockets.connect(URI) as ws:
        print("Connected!")

        # 1. Setup Message
        setup_msg = {
            "setup": {
                "model": f"models/{MODEL}",
                "generation_config": {"response_modalities": ["AUDIO"]},
            }
        }
        await ws.send(json.dumps(setup_msg))
        print("Sent Setup.")

        # 2. Receive Initial Response (Setup Complete)
        raw_resp = await ws.recv()
        print(f"Setup Response: {raw_resp}")

        # 3. Send a text message to trigger audio response
        client_content = {
            "client_content": {
                "turns": [
                    {
                        "role": "user",
                        "parts": [
                            {
                                "text": "Hello Gemini! This is a test. Say 'System Operational' if you hear me."
                            }
                        ],
                    }
                ],
                "turn_complete": True,
            }
        }
        await ws.send(json.dumps(client_content))
        print("Sent Text Message.")

        # 4. Listen for Audio
        print("Listening for response...")
        try:
            async for msg in ws:
                response = json.loads(msg)

                # Check for audio
                server_content = response.get("serverContent")
                if server_content:
                    model_turn = server_content.get("modelTurn")
                    if model_turn:
                        parts = model_turn.get("parts", [])
                        for part in parts:
                            if "inlineData" in part:
                                mime = part["inlineData"]["mimeType"]
                                data = part["inlineData"]["data"]
                                print(
                                    f"Received Audio Chunk: {len(data)} bytes ({mime})"
                                )
                            if "text" in part:
                                print(f"Received Text: {part['text']}")

                    if server_content.get("turnComplete"):
                        print("Turn Complete. Exiting.")
                        break
        except Exception as e:
            print(f"Error reading loop: {e}")


if __name__ == "__main__":
    # Create prototypes dir if not exists
    os.makedirs(os.path.dirname(__file__), exist_ok=True)
    asyncio.run(run_live_test())
