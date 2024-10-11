import asyncio
import json
import logging
import os
import base64
import websockets
from websockets.exceptions import ConnectionClosedError
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

class OpenAIRealtimeClient:
    def __init__(self, session_instructions, tools):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("Please set the OPENAI_API_KEY in your .env file.")
        self.url = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "OpenAI-Beta": "realtime=v1",
        }
        self.session_instructions = session_instructions
        self.tools = tools
        self.websocket = None
        self.audio_append_count = 0
        self.last_audio_append_log_time = 0
        self.AUDIO_APPEND_LOG_INTERVAL = 1
        self.AUDIO_APPEND_LOG_TIME_INTERVAL = 1

    async def connect(self):
        self.websocket = await websockets.connect(self.url, extra_headers=self.headers)
        logging.info("Connected to the server.")

        # Initialize the session
        session_update = {
            "type": "session.update",
            "session": {
                "modalities": ["text", "audio"],
                "instructions": self.session_instructions,
                "voice": "alloy",
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.5,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 400,
                },
                "tools": self.tools,
            },
        }
        await self.send_event(session_update)

    async def send_event(self, event):
        if not self.websocket:
            raise ValueError("WebSocket connection not established.")
        await self.websocket.send(json.dumps(event))
        self.log_ws_event("Outgoing", event)

    async def receive_event(self):
        if not self.websocket:
            raise ValueError("WebSocket connection not established.")
        message = await self.websocket.recv()
        event = json.loads(message)
        self.log_ws_event("Incoming", event)
        return event

    async def send_audio(self, audio_data):
        base64_audio = base64.b64encode(audio_data).decode("utf-8")
        if base64_audio:
            audio_event = {
                "type": "input_audio_buffer.append",
                "audio": base64_audio,
            }
            await self.send_event(audio_event)
            
            # Update audio append count and log if necessary
            self.audio_append_count += 1
            current_time = time.time()
            if (self.audio_append_count % self.AUDIO_APPEND_LOG_INTERVAL == 0 and 
                current_time - self.last_audio_append_log_time >= self.AUDIO_APPEND_LOG_TIME_INTERVAL):
                logging.debug(f"Sent {self.audio_append_count} audio append events")
                self.last_audio_append_log_time = current_time
        else:
            logging.debug("No audio data to send")

    async def close(self):
        if self.websocket:
            await self.websocket.close()

    @staticmethod
    def log_ws_event(direction, event):
        event_type = event.get("type", "Unknown")
        if event_type != "input_audio_buffer.append":  # Skip logging for audio append events
            event_emojis = {
                "session.update": "🛠️",
                "session.created": "🔌",
                "session.updated": "🔄",
                "input_audio_buffer.commit": "✅",
                "input_audio_buffer.speech_started": "🗣️",
                "input_audio_buffer.speech_stopped": "🤫",
                "input_audio_buffer.cleared": "🧹",
                "input_audio_buffer.committed": "📨",
                "conversation.item.create": "📥",
                "conversation.item.delete": "🗑️",
                "conversation.item.truncate": "✂️",
                "conversation.item.created": "📤",
                "conversation.item.deleted": "🗑️",
                "conversation.item.truncated": "✂️",
                "response.create": "➡️",
                "response.created": "📝",
                "response.output_item.added": "➕",
                "response.output_item.done": "✅",
                "response.text.delta": "✍️",
                "response.text.done": "📝",
                "response.audio.delta": "🔊",
                "response.audio.done": "🔇",
                "response.done": "✔️",
                "response.cancel": "⛔",
                "response.function_call_arguments.delta": "📥",
                "response.function_call_arguments.done": "📥",
                "rate_limits.updated": "⏳",
                "error": "❌",
                "conversation.item.input_audio_transcription.completed": "📝",
                "conversation.item.input_audio_transcription.failed": "⚠️",
            }
            emoji = event_emojis.get(event_type, "❓")
            icon = "⬆️ - Out" if direction == "Outgoing" else "⬇️ - In"
            logging.debug(f"{emoji} {icon} {event_type}")