import sys
import time
import logging
import os
import socket
import json
import subprocess
import openai
import pandas as pd
from openai import OpenAI
from llama_cpp import Llama
from elevenlabs import stream
from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings
from RealtimeSTT import AudioToTextRecorder
from duckduckgo_search import DDGS
import win32api
import win32gui



#logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


# Secrets
OPENAI_KEY = "NOT//IMPORTANT"
openai_client = OpenAI(api_key=OPENAI_KEY)
ELEVENLABS_KEY = "ENTER ELEVENLABS API KEY HERE"



# ElevenLabs setup
client = ElevenLabs(api_key=ELEVENLABS_KEY)
# Voice IDs from ElevenLabs Library
VOICE_ID = "84Fal4DSXWfp7nJ8emqQ"
PAUL_ID = "5Q0t7uMcjvnagumLfvZi"
FIN_ID = "D38z5RcWu1voky8WS1ja"

client.voices.edit_settings(
    voice_id="5Q0t7uMcjvnagumLfvZi",
    request=VoiceSettings(
        stability=1,
        similarity_boost=1,
        style=0,
        speed=1.1,
    )
)


# Llama model setup


llm = Llama(
    model_path="C:\\MODEL\\PATH\\",
    n_gpu_layers=0,
    use_mmap=False
) 

onnx_path = "C:\\HELLO_WOLFY!\\ONNX\\FILE\\PATH\\" # ONNX file PATH
if not os.path.exists(onnx_path):
    print(f"Error: Onnx file not found at {onnx_path}. Exiting...")
    exit(1)


# Initialise MPV player and socket for command injection
def start_mpv_player():
    # Path to mpv.exe — adjust if needed
    mpv_path = r"C:\\MPV\\PATH\\"  # Example: C:\Program Files\mpv\mpv.exe HAS TO BE ADDED TO PATH

    # Command arguments
    command = [
        mpv_path,
        "p_idle.mp4",
        "--loop",
        "--fullscreen",
        "--no-border",
        "--no-osd-bar",
        "--screen=2",
        "--input-ipc-server=\\\\.\\pipe\\mpvsocket"
    ]

    try:
        # Start mpv in background (do not wait for it to finish)
        process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("[MPV] Launched successfully.")
        return process
    except Exception as e:
        print(f"[MPV] Failed to launch: {e}")
        return None


MAX_TURNS = 3  # Number of user+assistant exchanges to keep
chat_history = ""

# Static prompt template
prompt_template = """You are a helpful AI assistant at the American University of Kuwait (AUK).
Answer the user's questions clearly and concisely based on AUK knowledge.
If user responds vaguely like "yes please", infer based on previous context.
If you are unsure or lack reliable information, always say "Unfortunately," at the start of your answer EVERY TIME.

"""

# For RealtimeSTT
def my_stop_callback():
    print("\nRecording Stopped!")

# Video Commander 
def trigger_video(mode):
    pipe_path = r'\\.\pipe\mpvsocket'  # Windows named pipe path
    try:
        with open(pipe_path, 'w+b', buffering=0) as pipe:
            if mode == "talking":
                command = {"command": ["loadfile", "p_talking.mp4", "replace"]}
            else:
                command = {"command": ["loadfile", "p_idle.mp4", "replace"]}

            payload = (json.dumps(command) + "\n").encode("utf-8")
            pipe.write(payload)

    except Exception as e:
        print(f"[Video Trigger] Failed to switch to '{mode}': {e}")


WM_APPCOMMAND = 0x319
APPCOMMAND_MICROPHONE_VOLUME_MUTE = 0x180000
# Play Audio Response
def play_response(answer):
    trigger_video("talking")
    audio_stream = client.text_to_speech.convert_as_stream(
        text=answer,
        voice_id=PAUL_ID, # Specify the Voice ID from above
        model_id="eleven_multilingual_v2"
    )
    stream(audio_stream)
    time.sleep(4)
    '''
    hwnd_active = win32gui.GetForegroundWindow()
    win32api.SendMessage(hwnd_active, WM_APPCOMMAND, None, APPCOMMAND_MICROPHONE_VOLUME_MUTE)
    time.sleep(5)
    hwnd_active = win32gui.GetForegroundWindow()
    win32api.SendMessage(hwnd_active, WM_APPCOMMAND, None, APPCOMMAND_MICROPHONE_VOLUME_MUTE)
    '''
    trigger_video("idle")


# Acronym Catching and Fixing
import re
def fix_acronyms(text):
    # Match "A U K", "a.uk", "a u.k", "aUK", etc.
    auk_pattern = r'\b(?:a[\s\.\-]*)[uU][\s\.\-]*[kK]\b'
    
    # Match "O K", "O.K.", "o.k", etc. and replace with AUK (common mishearing)
    okay_pattern = r'\b[oO][\s\.\-]*[kK]\b'

    # Normalize both
    text = re.sub(auk_pattern, 'AUK', text, flags=re.IGNORECASE)
    text = re.sub(okay_pattern, 'AUK', text, flags=re.IGNORECASE)
    # Enforce consistent identifiers
    text = re.sub("I.CSE", "IGCSE",text)
    text = re.sub("A.K", "AUK",text)
    text = re.sub("AU.", "AUK",text)
    text = text.replace("IHCSE", "IGCSE")
    text = text.replace("the UK", "AUK")
    text = text.replace ("Who's", "Who is")
    text = text.replace("Q8", "Kuwait")
    text = text.replace("measures", "Majors")
    text = text.replace("Qatar", "Kuwait")
    text = text.replace("Kurdistan", "Kuwait")
    text = re.sub(r"\bAUK\b", "American University of Kuwait", text)


    return text


# AVOIDING Token Overflow
def estimate_token_count(text):
    # Roughly 1 token per 4 characters for English text
    return len(text) / 4


MAX_TOKENS_TOTAL = 512
MAX_RESPONSE_TOKENS = 200
MAX_PROMPT_TOKENS = MAX_TOKENS_TOTAL - MAX_RESPONSE_TOKENS  # 312

def trim_chat_history_to_token_limit(chat_history, prompt_template, max_tokens=MAX_PROMPT_TOKENS):
    combined = chat_history.strip().split("\n")
    trimmed = []

    # Add lines from the end until we hit the token limit
    current_tokens = estimate_token_count(prompt_template)
    for line in reversed(combined):
        tokens = estimate_token_count(line + "\n")
        if current_tokens + tokens > max_tokens:
            break
        trimmed.insert(0, line)  # Prepend to maintain order
        current_tokens += tokens

    return "\n".join(trimmed)


# Sensitive Data Detection 
def is_sensitive_or_factual(text):
    keywords = [
        "president", "dean", "director", "vice president", "email", "contact",
        "event", "address", "office", "who is", "location", "when", "where",
        "tuition", "fees", "schedule", "number", "phone", "website", "faculty", "majors"
    ]
    return any(k in text.lower() for k in keywords)

search_client= DDGS()
# Text Processing
def process_text(text):
    global chat_history
    global detected

    if not text.strip():
        print("No speech detected. Skipping...")
        return

    text = fix_acronyms(text)
    print(f"Recorded text: {text}")
    #print("Hellooooo")

     #Add to history
    chat_history += f"\nUser: {text}\n"
    chat_history = trim_chat_history_to_token_limit(chat_history, prompt_template)
    #print(chat_history.splitlines()[-1])
    chat_recent = chat_history.splitlines()[-1]
   

    # Main model response
    prompt = f"{prompt_template}\n{chat_recent}Assistant:"
    response = llm(prompt, stop=["User:", "</s>", "[INST]", "[/INST]","Assistant:"], max_tokens=200)
    assistant_reply = response["choices"][0]["text"].strip()


    locc = ""
    for char in assistant_reply:
        if char == ":":
            break
        else:
            locc +=char

    # For Web Fallback INSTEAD of AI Fallback
    # 🌐 Web Fallback for factual queries
    # if is_sensitive_or_factual(text):
    #     print("🌐 Web fallback triggered for better accuracy...")
    #     web_info = search_web(text)

    #     # Inject live info into retry prompt
    #     retry_prompt = f"""
    #     The user asked: "{text}"

    #     The following information was found online:
    #     {web_info}

    #     Based on this, provide a clear and factual response:
    #     """
    #     retry_response = llm(
    #         retry_prompt,
    #         stop=["User:", "</s>", "[INST]", "[/INST]"],
    #         max_tokens=180
    #     )
    #     assistant_reply = retry_response["choices"][0]["text"].strip()
    #     if any(term in assistant_reply.lower() for term in ["q8", "kurdistan", "qatar"]):
    #         assistant_reply = "I'm sorry, I couldn't find reliable current information about the AUK president."
    #     print(f"\n✅ Verified Assistant says: {assistant_reply}")
    """
    if is_sensitive_or_factual(text):
        print("🤖 ChatGPT fallback triggered...")
        assistant_reply = query_chatgpt_fallback(text)
        print(f"✅ Verified Assistant says: {assistant_reply}")"""
    

    low_conf= "Unfortunately,"
    words = assistant_reply.split()
    #print(words)

    if "president" in text.lower() and "american university of kuwait" in text.lower():
        assistant_repp = "The president of the American University of Kuwait (AUK) is Dr. Rawda Awwad."

        play_response(assistant_repp)
        print(f"\nAssistant says: {assistant_repp}")
      #  start_recorder()
   
        ####################### WEB SEARCH CAPABILITY ######################
        # Can be used to use DuckDuckGo for looking up the question when the llms confidence is low
        # Outputs the first web result it finds
        #If removed, the AI will instead apologise and state that they are unsure of the answer instead.
    
        
    elif low_conf in words:
        print(" Low confidence detected ; using web search...")
        global search_query
        global yay
        search_query= locc
        results = search_client.text(
            keywords=search_query,
            region="wt_wt",
            safesearch="off",
            max_results=1
        )
        print(results)
        output= results[0]["body"]
        
        print(f"\nAssistant says:" + results[0]["body"])
        play_response(output)
       # start_recorder()
    
    #######################################################################################
             
    else:   
        print(f"\nAssistant says: {assistant_reply}")
        play_response(assistant_reply)
       # start_recorder()

###################################WAKEWORD FUNCTIONS######################################

def on_wakeword_detected():
    global detected
    print("\nWake word detected!")
    detected = True

def on_recording_start():
    time.sleep(0.5)


def on_wakeword_timeout():
    global detected
    if not detected:
        print(f"Timeout. Say 'Hello Wolfy' to begin.")


################################################################################


# Manual Mode (Retired) WITHOUT Fallbacks
def manual_recorder():
    mode = input("Type 'm' for manual text input, or press [Enter] to use microphone: ").lower()

    if mode == 'm':
        while True:
            user_input = input("Type your question: ")
            if user_input.strip().lower() == "exit":
                break
            process_text(user_input)
    else:
        recorder = AudioToTextRecorder(
            wake_words="",
            use_microphone=True,
            debug_mode=True,
            device="cpu",
            on_recording_stop=my_stop_callback,
            post_speech_silence_duration=0.4,
            min_length_of_recording=2.0,
        )
        recorder.start()

        while True:
            input("\nPress [Enter] to start recording...")
            print("Recording... Speak now!")
            recorder.start_recording_event.set()

            time.sleep(1)

            input("Press [Enter] again to stop recording...")
            recorder.stop_recording_event.set()

            print("Processing...")
            text = recorder.text()
            process_text(text)


def gpt_recorder():
    mode = input("Type 'm' for manual text input, or press [Enter] to use microphone: ").lower()

    if mode == 'm':
        while True:
            user_input = input("Type your question: ")
            if user_input.strip().lower() == "exit":
                break
            process_text(user_input)
    else:
        recorder = AudioToTextRecorder(
            wake_words="",
            use_microphone=True,
            debug_mode=True,
            spinner=False,
            device="cpu",
            on_recording_stop=my_stop_callback,
            post_speech_silence_duration=0.4,
            min_length_of_recording=2.0
        )
        while True:
            input("\n🎤 Press [Enter] to start recording...")
            print("Recording... Speak now!")
            recorder.start()
            recorder.start_recording_event.set()
            time.sleep(0.5)

            input("⏹️  Press [Enter] again to stop recording...")
            recorder.stop_recording_event.set()

            print("🧠 Processing...")
            text = recorder.text()

            if not text.strip():
                print("⚠️ No speech detected. Try again.\n")
                continue

            process_text(text)


if __name__ == '__main__':
    mpv_process = start_mpv_player()
    try:
        recorder = AudioToTextRecorder(  ###For manual recording, comment out everything until "except Keyboard Interrupt" and replace with manual_recorder() etc.
            wake_words="Hello_Wolfy!",
            openwakeword_model_paths=onnx_path,
            openwakeword_inference_framework="onnx",
            wakeword_backend="oww",
            
            on_wakeword_detected=on_wakeword_detected,
            on_recording_start=on_recording_start,
            on_wakeword_timeout=on_wakeword_timeout,
           # on_wakeword_detection_start=on_wakeword_detection_start,
            post_speech_silence_duration=1,
            min_length_of_recording=2.0,
            wake_word_buffer_duration=0.3,
            silero_sensitivity=0.4
        ) 


        print('Say "Hello Wolfy" to start recording.')

        while True:
            text = recorder.text()   
            if not text:
                continue
            else: 
                process_text(text)
                time.sleep(1)

            print('\nSay "Hello Wolfy" to start recording.')

    except KeyboardInterrupt:
        print("\nTerminated.")
        recorder.shutdown()