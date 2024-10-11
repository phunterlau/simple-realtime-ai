import asyncio
import logging
import json
import time
import base64
from openai_client import OpenAIRealtimeClient
from agent_tools import function_map, tools

from audio_handler import AsyncMicrophone, play_audio
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)

# Explicitly set logging level for imported modules
logging.getLogger('tools').setLevel(logging.DEBUG)
logging.getLogger('agent_tools').setLevel(logging.DEBUG)

# Load personalization settings
personalization_file = os.getenv("PERSONALIZATION_FILE", "./personalization.json")
with open(personalization_file, "r") as f:
    personalization = json.load(f)

# Extract names from personalization
ai_assistant_name = personalization.get("ai_assistant_name", "Assistant")
human_name = personalization.get("human_name", "User")

# Define session instructions constant
SESSION_INSTRUCTIONS = f"You are {ai_assistant_name}, a helpful assistant. Respond concisely to {human_name}."

async def process_ws_messages(client, mic):
    assistant_reply = ""
    audio_chunks = []
    response_in_progress = False
    function_call = None
    function_call_args = ""

    while True:
        try:
            event = await client.receive_event()

            if event["type"] == "response.created":
                mic.start_receiving()
                response_in_progress = True
            elif event["type"] == "response.output_item.added":
                item = event.get("item", {})
                if item.get("type") == "function_call":
                    function_call = item
                    function_call_args = ""
            elif event["type"] == "response.function_call_arguments.delta":
                delta = event.get("delta", "")
                function_call_args += delta
            elif event["type"] == "response.function_call_arguments.done":
                if function_call:
                    function_name = function_call.get("name")
                    call_id = function_call.get("call_id")
                    try:
                        args = json.loads(function_call_args) if function_call_args else {}
                    except json.JSONDecodeError:
                        logging.error(f"Failed to parse function arguments: {function_call_args}")
                        args = {}
                    if function_name in function_map:
                        logging.info(f"🛠️ Calling function: {function_name} with args: {args}")
                        try:
                            result = await function_map[function_name](function_name, **args)
                            logging.info(f"🛠️ Function call result: {result}")
                        except Exception as e:
                            logging.error(f"Error executing function {function_name}: {str(e)}")
                            result = {"error": f"Error executing function '{function_name}': {str(e)}"}
                    else:
                        logging.error(f"Function '{function_name}' not found in function_map")
                        result = {"error": f"Function '{function_name}' not found."}
                    function_call_output = {
                        "type": "conversation.item.create",
                        "item": {
                            "type": "function_call_output",
                            "call_id": call_id,
                            "output": json.dumps(result),
                        },
                    }
                    await client.send_event(function_call_output)
                    await client.send_event({"type": "response.create"})
                    function_call = None
                    function_call_args = ""
            elif event["type"] == "response.text.delta":
                assistant_reply += event.get("delta", "")
                print(f"{ai_assistant_name}: {event.get('delta', '')}", end="", flush=True)
            elif event["type"] == "response.audio.delta":
                audio_chunks.append(base64.b64decode(event["delta"]))
            elif event["type"] == "response.done":
                logging.info(f"{ai_assistant_name}'s response complete.")
                if audio_chunks:
                    audio_data = b"".join(audio_chunks)
                    logging.info(f"Playing {len(audio_data)} bytes of audio data")
                    await play_audio(audio_data)
                assistant_reply = ""
                audio_chunks = []
                response_in_progress = False
                mic.stop_receiving()
                mic.start_recording()
                logging.info("Resumed recording after response")
            elif event["type"] == "input_audio_buffer.speech_started":
                logging.info(f"Speech detected, {ai_assistant_name} is listening...")
            elif event["type"] == "input_audio_buffer.speech_stopped":
                mic.stop_recording()
                logging.info("Speech ended, processing...")
                await client.send_event({"type": "input_audio_buffer.commit"})

        except Exception as e:
            logging.exception(f"Error processing WebSocket message: {e}")
            if 'audio_chunks' in locals() and audio_chunks:
                logging.warning(f"Discarding {len(audio_chunks)} incomplete audio chunks due to error")
                audio_chunks = []
            break

async def run_conversation():
    client = OpenAIRealtimeClient(SESSION_INSTRUCTIONS, tools)
    mic = AsyncMicrophone()

    try:
        await client.connect()
        process_task = asyncio.create_task(process_ws_messages(client, mic))

        logging.info(f"Conversation started. Speak freely, and {ai_assistant_name} will respond.")
        mic.start_recording()
        logging.info("Recording started. Listening for speech...")

        while True:
            if mic.is_recording and not mic.is_receiving:
                audio_data = mic.get_audio_data()
                if audio_data and len(audio_data) > 0:
                    await client.send_audio(audio_data)
            await asyncio.sleep(0.1)  # Small delay to prevent busy-waiting

    except KeyboardInterrupt:
        logging.info("Keyboard interrupt received. Closing the connection.")
    except Exception as e:
        logging.exception(f"An unexpected error occurred: {e}")
    finally:
        mic.stop_recording()
        mic.close()
        await client.close()
        if 'process_task' in locals():
            process_task.cancel()
            try:
                await process_task
            except asyncio.CancelledError:
                pass

def main():
    try:
        asyncio.run(run_conversation())
    except KeyboardInterrupt:
        logging.info("Program terminated by user")
    except Exception as e:
        logging.exception(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    print(f"Press Ctrl+C to exit the conversation with {ai_assistant_name}.")
    main()