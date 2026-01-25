import asyncio
import websockets
import json
import logging
import config

logger = logging.getLogger(__name__)


class GeminiLiveClient:
    """
    Client for Gemini Multimodal Live API (WebSockets).
    Handles authentication, session setup, and bidirectional streaming.
    """

    HOST = "generativelanguage.googleapis.com"
    URI = f"wss://{HOST}/ws/google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContent?key={config.GEMINI_API_KEY}"

    def __init__(self, model_name: str = "gemini-2.0-flash-exp"):
        self.model_name = model_name
        self.ws = None
        self._running = False
        self.on_audio_data = None  # Callback (bytes) -> void
        self.on_text_data = None  # Callback (str) -> void
        self.on_turn_complete = None  # Callback () -> void

    async def connect(self):
        """Establish WebSocket connection and handshake"""
        try:
            logger.info(f"Connecting to Gemini Live: {self.URI[:40]}...")
            self.ws = await websockets.connect(self.URI)
            self._running = True

            # 1. Setup Handshake
            setup_msg = {
                "setup": {
                    "model": f"models/{self.model_name}",
                    "generation_config": {"response_modalities": ["AUDIO"]},
                }
            }
            await self.ws.send(json.dumps(setup_msg))

            # 2. Wait for confirmation
            raw_resp = await self.ws.recv()
            logger.info(f"Live Session Setup: {raw_resp}")

            # Start background listener
            asyncio.create_task(self._receive_loop())

        except Exception as e:
            logger.error(f"Live Connection Failed: {e}")
            self._running = False
            raise e

    async def disconnect(self):
        """Close connection"""
        self._running = False
        if self.ws:
            await self.ws.close()

    async def send_audio(self, pcm_data: bytes):
        """Send raw PCM audio chunk (Client -> Server)"""
        if not self._running or not self.ws:
            return

        # Wrap in RealtimeInput format
        msg = {
            "realtime_input": {
                "media_chunks": [
                    {
                        "mime_type": "audio/pcm",
                        "data": config.base64_encode_bytes(pcm_data),
                    }
                ]
            }
        }
        await self.ws.send(json.dumps(msg))

    async def send_text(self, text: str):
        """Send text prompt (Client -> Server)"""
        if not self._running or not self.ws:
            return

        msg = {
            "client_content": {
                "turns": [{"role": "user", "parts": [{"text": text}]}],
                "turn_complete": True,
            }
        }
        await self.ws.send(json.dumps(msg))

    async def _receive_loop(self):
        """Background loop to handle incoming streams"""
        try:
            async for raw_msg in self.ws:
                if not self._running:
                    break

                response = json.loads(raw_msg)
                server_content = response.get("serverContent")

                if server_content:
                    # Handle Audio/Text
                    model_turn = server_content.get("modelTurn")
                    if model_turn:
                        parts = model_turn.get("parts", [])
                        for part in parts:
                            # Audio
                            if "inlineData" in part:
                                b64_data = part["inlineData"]["data"]
                                pcm_bytes = config.base64_decode(
                                    b64_data
                                )  # Helper needed
                                if self.on_audio_data:
                                    self.on_audio_data(pcm_bytes)

                            # Text (Captions/Logs)
                            if "text" in part:
                                if self.on_text_data:
                                    self.on_text_data(part["text"])

                    # Handle Turn End
                    if server_content.get("turnComplete"):
                        if self.on_turn_complete:
                            self.on_turn_complete()

        except Exception as e:
            logger.error(f"Live Receive Error: {e}")
            self._running = False
