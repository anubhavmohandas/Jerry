# speech_manager.py
import pyttsx3
import speech_recognition as sr
from typing import Optional

class SpeechManager:
    def __init__(self, voice_id: str):
        self.engine = pyttsx3.init()
        self.engine.setProperty('voice', voice_id)
        self.recognizer = sr.Recognizer()
        
    def verify_microphone(self) -> bool:
        """Check if microphone is working properly"""
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                return True
        except Exception as e:
            print(f"Microphone check failed: {e}")
            return False

    def speak(self, text: str):
        """Convert text to speech"""
        self.engine.say(text)
        self.engine.runAndWait()
        
    def listen(self) -> Optional[str]:
        """Listen for voice input and convert to text"""
        with sr.Microphone() as source:
            print("Listening...")
            audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)
            
        try:
            print("Recognizing...")
            query = self.recognizer.recognize_google(audio, language='en-US')
            print(f"User said: {query}")
            return query.lower()
        except Exception as e:
            print(f"Error: {e}")
            return None
