# try``.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import speech_recognition as sr
import webbrowser
import pyttsx3
import requests
from openai import OpenAI
from gtts import gTTS
import pygame
import os
import ctypes
import time

# Constants
NEWS_API_KEY = "c82f038462a2465787f492752f8e13e1"
OPENAI_API_KEY = ""

# Initialize the app
app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, set this to your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import music library
try:
    import musicLibrary
except ImportError:
    # Create a placeholder if module doesn't exist
    class MusicLibraryPlaceholder:
        def __init__(self):
            self.music = {
                "default": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
            }
            
        def get_song(self, song_name):
            return self.music.get(song_name.lower())
            
        def add_song(self, name, link):
            if name.lower() in self.music:
                return False
            self.music[name.lower()] = link
            return True
            
        def list_songs(self):
            return list(self.music.keys())
            
    musicLibrary = MusicLibraryPlaceholder()

# Initialize speech engine
recognizer = sr.Recognizer()
engine = pyttsx3.init()

def speak_old(text):
    """Legacy speech function using pyttsx3"""
    engine.say(text)
    engine.runAndWait()

def speak(text):
    """Improved speech function using gTTS"""
    try:
        tts = gTTS(text)
        temp_file = 'temp.mp3'
        tts.save(temp_file)

        # Initialize Pygame mixer
        pygame.mixer.init()
        pygame.mixer.music.load(temp_file)
        pygame.mixer.music.play()

        # Keep the program running until the music stops playing
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        
        pygame.mixer.music.unload()
        # Clean up
        if os.path.exists(temp_file):
            os.remove(temp_file)
    except Exception as e:
        print(f"Error in speak function: {e}")
        # Fallback to the old method if needed
        speak_old(text)

def ai_process(command):
    """Process commands using OpenAI"""
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a virtual assistant named Jarvis skilled in general tasks like Alexa and Google Cloud. Give short responses please"},
                {"role": "user", "content": command}
            ]
        )
        
        return completion.choices[0].message.content
    except Exception as e:
        print(f"Error in AI processing: {e}")
        return f"I encountered an error processing your request."

def process_command(command):
    """Process user commands"""
    response = ""
    
    if "open google" in command.lower():
        webbrowser.open("https://google.com")
        response = "Opening Google"
    elif "open facebook" in command.lower():
        webbrowser.open("https://facebook.com")
        response = "Opening Facebook"
    elif "open youtube" in command.lower():
        webbrowser.open("https://youtube.com")
        response = "Opening YouTube"
    elif "open linkedin" in command.lower():
        webbrowser.open("https://linkedin.com")
        response = "Opening LinkedIn"
    elif command.lower().startswith("play"):
        try:
            song = command.lower().split("play ")[1]
            link = musicLibrary.get_song(song)
            if link:
                webbrowser.open(link)
                response = f"Playing {song}"
            else:
                response = f"I couldn't find {song} in your music library"
        except Exception as e:
            response = f"I couldn't play that song: {str(e)}"
    elif "list songs" in command.lower() or "what songs do you have" in command.lower():
        try:
            songs = musicLibrary.list_songs()
            if songs:
                response = "Here are the songs in your library: " + ", ".join(songs)
            else:
                response = "Your music library is empty"
        except Exception as e:
            response = f"I couldn't list your songs: {str(e)}"
    elif command.lower().startswith("add song"):
        try:
            # Expected format: "add song [name] [link]"
            parts = command.split(" ", 2)
            if len(parts) >= 3:
                remaining = parts[2].split(" ", 1)
                if len(remaining) == 2:
                    song_name, link = remaining
                    if musicLibrary.add_song(song_name, link):
                        response = f"Added {song_name} to your music library"
                    else:
                        response = f"{song_name} already exists in your library"
                else:
                    response = "Please provide both a song name and link"
            else:
                response = "Please specify a song name and link"
        except Exception as e:
            response = f"I couldn't add that song: {str(e)}"
    elif "shutdown" in command.lower():
        response = "Shutting down the system"
        # Safety check - requiring confirmation
        # os.system("shutdown /s /t 60")  # 60 second delay
    elif "restart" in command.lower():
        response = "Restarting the system"
        # Safety check - requiring confirmation
        # os.system("shutdown /r /t 60")  # 60 second delay
    elif "increase volume" in command.lower():
        try:
            for _ in range(5):
                ctypes.windll.user32.keybd_event(0xAF, 0, 0, 0)  # Increase volume
            response = "Volume increased"
        except Exception:
            response = "Couldn't adjust volume"
    elif "decrease volume" in command.lower():
        try:
            for _ in range(5):
                ctypes.windll.user32.keybd_event(0xAE, 0, 0, 0)  # Decrease volume
            response = "Volume decreased"
        except Exception:
            response = "Couldn't adjust volume"
    elif "open news" in command.lower():
        try:
            r = requests.get(f"https://newsapi.org/v2/top-headlines?country=us&apiKey={NEWS_API_KEY}")
            if r.status_code == 200:
                data = r.json()
                articles = data.get('articles', [])
                if articles:
                    response = "Here are the top headlines: "
                    for i, article in enumerate(articles[:3]):  # Limit to 3 headlines
                        response += f"{i+1}. {article['title']}. "
                else:
                    response = "No news articles found."
            else:
                response = "I couldn't fetch the news right now."
        except Exception as e:
            response = f"Error fetching news: {str(e)}"
    else:
        # Let OpenAI handle the request
        response = ai_process(command)
    
    return response

# FastAPI routes
@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint returning a simple HTML page"""
    return """
    <html>
        <head>
            <title>Jarvis Assistant</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; text-align: center; }
                h1 { color: #333; }
                p { color: #666; }
            </style>
        </head>
        <body>
            <h1>Welcome to Jarvis Assistant</h1>
            <p>The backend service is running. Connect via WebSocket to interact with Jarvis.</p>
        </body>
    </html>
    """

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication"""
    await websocket.accept()
    print("WebSocket connection established")
    
    try:
        while True:
            data = await websocket.receive_text()
            print(f"Received command: {data}")
            
            # Process the command
            response = process_command(data)
            
            # Send the response back to the client
            await websocket.send_text(response)
            
            # Optional: Speak the response (if running on server with audio)
            # Comment this out if running in a containerized environment
            # speak(response)
            
    except WebSocketDisconnect:
        print("WebSocket disconnected")
    except Exception as e:
        print(f"Error in WebSocket handler: {e}")
        try:
            await websocket.send_text(f"Error: {str(e)}")
        except:
            pass

# Optional: Mount static files if needed
# app.mount("/static", StaticFiles(directory="static"), name="static")

# Standalone execution for testing
if __name__ == "__main__":
    print("Starting Jarvis in standalone mode...")
    speak("Initializing Jarvis....")
    
    while True:
        r = sr.Recognizer()
        
        try:
            with sr.Microphone() as source:
                print("Listening for wake word...")
                audio = r.listen(source, timeout=5, phrase_time_limit=2)
                
            word = r.recognize_google(audio)
            if word.lower() == "jarvis":
                speak("Yes?")
                
                # Listen for command
                with sr.Microphone() as source:
                    print("Jarvis Active...")
                    audio = r.listen(source)
                    command = r.recognize_google(audio)
                    print(f"Command: {command}")
                    
                    response = process_command(command)
                    speak(response)
        
        except sr.WaitTimeoutError:
            continue
        except sr.UnknownValueError:
            continue
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(1)  # Prevent tight error loops
        ##   uvicorn try:app --reload
