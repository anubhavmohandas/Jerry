# config.py
import os
from dataclasses import dataclass
from pathlib import Path
import platform
import subprocess
import winreg
import glob
import logging
from typing import Dict, Optional, List
import pyttsx3
import speech_recognition as sr
import webbrowser
import pywhatkit as kit
from config import AssistantConfig
from platform_utils import PlatformUtils
from speech_manager import SpeechManager
from features.browser_manager import BrowserManager
from features.system_manager import SystemManager
from transformers import pipeline
import datetime
import time
import random
import json
import wikipedia
import instaloader
import requests
import pyautogui

class PlatformUtils:
    COMMON_APP_LOCATIONS = {
        "Windows": [
            "C:/Program Files",
            "C:/Program Files (x86)",
            str(Path.home() / "AppData/Local"),
            str(Path.home() / "AppData/Local/Programs"),
            "C:/Windows/System32"
        ],
        "Darwin": [  # macOS
            "/Applications",
            str(Path.home() / "Applications"),
            "/System/Applications"
        ],
        "Linux": [
            "/usr/bin",
            "/usr/local/bin",
            "/opt",
            str(Path.home() / ".local/bin")
        ]
    }

    def __init__(self):
        self.system = platform.system()
        self.app_cache = {}
        self.setup_logging()

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            filename='platform_utils.log'
        )

    @property
    def is_windows(self) -> bool:
        return self.system == "Windows"

    @property
    def is_mac(self) -> bool:
        return self.system == "Darwin"

    @property
    def is_linux(self) -> bool:
        return self.system == "Linux"

    def get_default_voice(self) -> str:
        """Get system default voice dynamically"""
        try:
            if self.is_windows:
                return self._get_windows_voices()[0]
            elif self.is_mac:
                return self._get_mac_voices()[0]
            else:
                return self._get_linux_voices()[0]
        except Exception as e:
            logging.error(f"Error getting default voice: {e}")
            return ""

    def _get_windows_voices(self) -> List[str]:
        """Get available Windows voices"""
        voices = []
        if not self.is_windows:
            return [""]
            
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                            r"SOFTWARE\Microsoft\Speech\Voices\Tokens") as key:
                i = 0
                while True:
                    try:
                        voice_key = winreg.EnumKey(key, i)
                        voices.append(f"HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\{voice_key}")
                        i += 1
                    except WindowsError:
                        break
        except Exception as e:
            logging.error(f"Error getting Windows voices: {e}")
        return voices or ["HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_EN-US_ZIRA_11.0"]


    def _get_mac_voices(self) -> List[str]:
        """Get available macOS voices"""
        try:
            result = subprocess.run(['say', '-v', '?'], capture_output=True, text=True)
            voices = [line.split()[0] for line in result.stdout.split('\n') if line]
            return [f"com.apple.speech.synthesis.voice.{voice.lower()}" for voice in voices]
        except Exception as e:
            logging.error(f"Error getting macOS voices: {e}")
            return ["com.apple.speech.synthesis.voice.samantha"]

    def _get_linux_voices(self) -> List[str]:
        """Get available Linux voices"""
        try:
            result = subprocess.run(['espeak', '--voices'], capture_output=True, text=True)
            voices = [line.split()[2] for line in result.stdout.split('\n')[1:] if line]
            return voices
        except Exception as e:
            logging.error(f"Error getting Linux voices: {e}")
            return ["default"]

    def scan_for_applications(self) -> Dict[str, str]:
        """Dynamically scan for installed applications"""
        paths = {}
        search_locations = self.COMMON_APP_LOCATIONS.get(self.system, [])
        
        for location in search_locations:
            self._scan_directory(Path(location), paths)
            
        # Cache the results
        self.app_cache = paths
        return paths

    def _scan_directory(self, directory: Path, paths: Dict[str, str]):
        """Recursively scan directory for applications"""
        try:
            if self.is_windows:
                self._scan_windows_directory(directory, paths)
            elif self.is_mac:
                self._scan_mac_directory(directory, paths)
            else:
                self._scan_linux_directory(directory, paths)
        except Exception as e:
            logging.error(f"Error scanning directory {directory}: {e}")

    def _scan_windows_directory(self, directory: Path, paths: Dict[str, str]):
        """Scan for .exe files on Windows"""
        try:
            for exe_file in directory.rglob("*.exe"):
                if not exe_file.is_file():
                    continue
                app_name = exe_file.stem.lower()
                if app_name not in paths:
                    paths[app_name] = str(exe_file)
        except Exception as e:
            logging.error(f"Error scanning Windows directory: {e}")

    def _scan_mac_directory(self, directory: Path, paths: Dict[str, str]):
        """Scan for .app bundles on macOS"""
        try:
            for app_bundle in directory.rglob("*.app"):
                if not app_bundle.is_dir():
                    continue
                app_name = app_bundle.stem.lower()
                if app_name not in paths:
                    paths[app_name] = str(app_bundle)
        except Exception as e:
            logging.error(f"Error scanning macOS directory: {e}")

    def _scan_linux_directory(self, directory: Path, paths: Dict[str, str]):
        """Scan for executables on Linux"""
        try:
            for file_path in directory.iterdir():
                if file_path.is_file() and os.access(str(file_path), os.X_OK):
                    app_name = file_path.stem.lower()
                    if app_name not in paths:
                        paths[app_name] = str(file_path)
        except Exception as e:
            logging.error(f"Error scanning Linux directory: {e}")

    def find_application(self, app_name: str) -> Optional[str]:
        """Find application path by name"""
        app_name = app_name.lower()
        
        # Check cache first
        if app_name in self.app_cache:
            return self.app_cache[app_name]
            
        # Scan for applications if not in cache
        self.scan_for_applications()
        return self.app_cache.get(app_name)

    def get_installed_apps(self) -> List[str]:
        """Get list of all installed applications"""
        if not self.app_cache:
            self.scan_for_applications()
        return list(self.app_cache.keys())

# Usage example:
if __name__ == "__main__":
    platform_utils = PlatformUtils()
    
    # Get all installed applications
    apps = platform_utils.get_installed_apps()
    print("Installed applications:", apps)
    
    # Find specific application
    chrome_path = platform_utils.find_application("chrome")
    if chrome_path:
        print("Chrome found at:", chrome_path)
    
    # Get system voices
    voices = platform_utils.get_default_voice()
    print("Available system voice:", voices)

# speech_manager.py

class SpeechManager:
    def __init__(self, voice_id: str):
        self.engine = pyttsx3.init()
        self.engine.setProperty('voice', voice_id)
        self.recognizer = sr.Recognizer()
        
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

# features/browser_manager.py

class BrowserManager:
    @staticmethod
    def open_url(url: str):
        webbrowser.open(url)
        
    @staticmethod
    def search_youtube(query: str):
        kit.playonyt(query)
        
    @staticmethod
    def search_google(query: str):
        webbrowser.open(f"https://www.google.com/search?q={query}")

# features/system_manager.py

class SystemManager:
    @staticmethod
    def shutdown():
        if platform.system() == "Windows":
            os.system("shutdown /s /t 5")
        else:
            os.system("sudo shutdown -h now")
            
    @staticmethod
    def restart():
        if platform.system() == "Windows":
            os.system("shutdown /r /t 5")
        else:
            os.system("sudo shutdown -r now")
            
    @staticmethod
    def sleep():
        if platform.system() == "Windows":
            os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
        else:
            os.system("pmset sleepnow")
            
    @staticmethod
    def open_app(app_path: str):
        """Open application based on platform with improved handling"""
        try:
            system = platform.system()
            if system == "Windows":
                os.startfile(app_path)
            elif system == "Darwin":  # macOS
                subprocess.call(['open', app_path])
            elif system == "Linux":
                subprocess.call(['xdg-open', app_path])
            else:
                print(f"Unsupported platform: {system}")
        except FileNotFoundError:
            print(f"Application not found: {app_path}")
        except PermissionError:
            print(f"Permission denied when opening: {app_path}")
        except Exception as e:
            print(f"Error opening application: {e}")
            
    @staticmethod
    def close_app(app_name: str):
        """Close application based on platform"""
        if platform.system() == "Windows":
            os.system(f"taskkill /f /im {app_name}")
        else:
            os.system(f"pkill {app_name}")

# main.py

class VirtualAssistant:
    def __init__(self):
        # Core initialization from original implementation
        self.config = AssistantConfig.load_config()
        self.platform_utils = PlatformUtils()
        self.config.voice_id = self.platform_utils.get_default_voice()
        self.speech = SpeechManager(self.config.voice_id)
        self.browser = BrowserManager()
        self.system = SystemManager()
        self.app_paths =platform_utils.get_installed_apps()
        
        # Additional managers
        self.weather = WeatherManager(self.config.weather_api_key)
        self.news = NewsManager(self.config.news_api_key)
        self.location = LocationManager()
        self.social = SocialMediaManager()
        self.wiki = WikiManager()
        self.screenshot = ScreenshotManager()
        
        # Enhanced AI features
        self.setup_logging()
        self.setup_nlp()
        self.load_personality()
        self.conversation_history = []
        self.max_history_length = 10
        self.user_preferences = {}
        self.load_user_preferences()

        # Don't load NLP models at startup
        self.sentiment_analyzer = None
        self.intent_classifier = None

    def wish_user(self):
        """Greet user based on time of day"""
        hour = datetime.datetime.now().hour
        time_str = time.strftime("%I:%M %p")
        
        if 0 <= hour < 12:
            greeting = f"Good Morning! It's {time_str}"
        elif 12 <= hour < 16:
            greeting = f"Good Afternoon! It's {time_str}"
        elif 16 <= hour < 20:
            greeting = f"Good Evening! It's {time_str}"
        else:
            greeting = f"Hello! It's {time_str}"
            
        self.speech.speak(f"{greeting}. I am {self.config.name}, how may I assist you?")

    def process_command(self, command: str) -> bool:
        """Process user command with input validation"""
        # Basic validation
        if not command or not isinstance(command, str):
            return True
            
        # Sanitize input
        command = command.lower().strip()
        
        # Prevent injection by limiting to alphanumeric and basic punctuation
        if not all(c.isalnum() or c.isspace() or c in '.,?!-:;' for c in command):
            self.speech.speak("I'm sorry, I didn't understand that command.")
            return True
            
        # Update conversation history
        self.update_conversation_history(command, "user")
            
        # Basic commands
        if "goodbye" in command or "bye" in command:
            self.speech.speak("Goodbye! Have a great day!")
            return False
            
        # Browser commands
        elif "open youtube" in command:
            self.browser.open_url("youtube.com")
        elif "play" in command:
            query = command.replace("play", "").strip()
            self.browser.search_youtube(query)
        elif "search" in command and "google" in command:
            query = command.replace("search", "").replace("google", "").strip()
            self.browser.search_google(query)
            
        # System commands
        elif "shutdown" in command:
            self.system.shutdown()
        elif "restart" in command:
            self.system.restart()
        elif "sleep" in command:
            self.system.sleep()
            
        # Application commands
        elif "notepad" in command or "text editor" in command:
            app_path = self.app_paths.get("notepad" if PlatformUtils.is_windows() else "textedit")
            if app_path:
                self.system.open_app(app_path)
                
        # Weather commands
        elif "weather" in command:
            city = "London"  # Default city, can be extracted from command
            result = self.weather.get_weather(city)
            self.speech.speak(result)
            
        # News commands
        elif "news" in command:
            self.speech.speak("Here are today's top headlines:")
            for i, headline in enumerate(self.news.get_news(), 1):
                self.speech.speak(f"Headline {i}: {headline}")
                
        # Location commands
        elif "where am i" in command:
            location = self.location.get_location()
            self.speech.speak(
                f"You are in {location['city']}, {location['region']}, {location['country']}"
            )
                
        # Wikipedia commands
        elif "wikipedia" in command:
            query = command.replace("wikipedia", "").strip()
            result = self.wiki.search(query)
            self.speech.speak("According to Wikipedia")
            self.speech.speak(result)
                
        # Screenshot commands
        elif "screenshot" in command or "take ss" in command:
            self.speech.speak("Taking screenshot")
            path = self.screenshot.take_screenshot()
            self.speech.speak(f"Screenshot saved to {path}")
        
        # If no specific command matched, try to generate a response
        else:
            response = self.generate_response(command)
            self.speech.speak(response)
            
        return True

    def setup_logging(self):
        """Configure logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            filename=f'{self.config.name.lower()}_ai.log'
        )

    def load_personality(self):
        """Load personality traits and responses"""
        self.personality = {
            "traits": {
                "friendliness": 0.8,
                "formality": 0.5,
                "humor": 0.6
            },
            "responses": {
                "greeting": [
                    f"Hello! I'm {self.config.name}. How can I assist you today?",
                    f"Hi there! {self.config.name} at your service!",
                    "Greetings! How may I help you?"
                ],
                "farewell": [
                    "Goodbye! It was a pleasure chatting with you.",
                    "Take care! Feel free to come back anytime.",
                    "Until next time! Have a great day!"
                ],
                "confusion": [
                    "I'm not quite sure I understood that. Could you rephrase?",
                    "Could you explain that differently?",
                    "I'm still learning, could you clarify?"
                ]
            }
        }

    def save_user_preferences(self):
        """Save user preferences to file"""
        try:
            with open(f'{self.config.name.lower()}_preferences.json', 'w') as f:
                json.dump(self.user_preferences, f)
        except Exception as e:
            logging.error(f"Error saving preferences: {e}")

    def load_user_preferences(self):
        """Load user preferences from file"""
        try:
            if os.path.exists(f'{self.config.name.lower()}_preferences.json'):
                with open(f'{self.config.name.lower()}_preferences.json', 'r') as f:
                    self.user_preferences = json.load(f)
        except Exception as e:
            logging.error(f"Error loading preferences: {e}")

    def update_conversation_history(self, text, speaker):
        """Update conversation history"""
        self.conversation_history.append({
            'text': text,
            'speaker': speaker,
            'timestamp': datetime.datetime.now().isoformat()
        })
        
        # Maintain max history length
        if len(self.conversation_history) > self.max_history_length:
            self.conversation_history.pop(0)

    def generate_response(self, text):
        """Generate a response based on input"""
        sentiment = self.analyze_sentiment(text)
        
        if sentiment["label"] == "POSITIVE":
            return random.choice([
                "That sounds great!",
                "I'm glad to hear that.",
                "Wonderful!"
            ])
        elif sentiment["label"] == "NEGATIVE":
            return random.choice([
                "I'm sorry you're feeling that way.",
                "That sounds challenging.",
                "I hope things get better."
            ])
        
        return "I'm not sure how to respond to that, but I'm here to help!"

    def run(self):
        """Main assistant loop"""
        self.wish_user()
        
        running = True
        while running:
            command = self.speech.listen()
            if command:
                running = self.process_command(command)

    

    def setup_logging(self):
        """Configure logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            filename=f'{self.config.name.lower()}_ai.log'
        )

    def setup_nlp(self):
        """Initialize NLP capabilities"""
        try:
            # Sentiment analysis
            self.sentiment_analyzer = pipeline("sentiment-analysis", 
                                            model="distilbert-base-uncased-finetuned-sst-2-english")
            
            # Intent classification
            self.intent_classifier = pipeline("zero-shot-classification")
            
            logging.info("NLP models loaded successfully")
        except Exception as e:
            logging.error(f"NLP setup error: {e}")

    def load_personality(self):
        """Load personality traits and responses"""
        self.personality = {
            "traits": {
                "friendliness": 0.8,
                "formality": 0.5,
                "humor": 0.6
            },
            "responses": {
                "greeting": [
                    f"Hello! I'm {self.config.name}. How can I assist you today?",
                    f"Hi there! {self.config.name} at your service!",
                    "Greetings! How may I help you?"
                ],
                "farewell": [
                    "Goodbye! It was a pleasure chatting with you.",
                    "Take care! Feel free to come back anytime.",
                    "Until next time! Have a great day!"
                ],
                "confusion": [
                    "I'm not quite sure I understood that. Could you rephrase?",
                    "Could you explain that differently?",
                    "I'm still learning, could you clarify?"
                ]
            }
        }

    def save_user_preferences(self):
        """Save user preferences to file"""
        try:
            with open(f'{self.config.name.lower()}_preferences.json', 'w') as f:
                json.dump(self.user_preferences, f)
        except Exception as e:
            logging.error(f"Error saving preferences: {e}")

    def load_user_preferences(self):
        """Load user preferences from file"""
        try:
            if os.path.exists(f'{self.config.name.lower()}_preferences.json'):
                with open(f'{self.config.name.lower()}_preferences.json', 'r') as f:
                    self.user_preferences = json.load(f)
        except Exception as e:
            logging.error(f"Error loading preferences: {e}")

    def update_conversation_history(self, text, speaker):
        """Update conversation history"""
        self.conversation_history.append({
            'text': text,
            'speaker': speaker,
            'timestamp': datetime.now().isoformat()
        })
        
        # Maintain max history length
        if len(self.conversation_history) > self.max_history_length:
            self.conversation_history.pop(0)

    def _ensure_nlp_loaded(self):
        """Lazy load NLP models when first needed"""
        if self.sentiment_analyzer is None:
            try:
                self.sentiment_analyzer = pipeline("sentiment-analysis", 
                                            model="distilbert-base-uncased-finetuned-sst-2-english")
                self.intent_classifier = pipeline("zero-shot-classification")
                logging.info("NLP models loaded successfully")
            except ImportError:
                logging.error("Transformers package not installed. NLP features disabled.")
                # Create simple fallback functions
                self.sentiment_analyzer = lambda text: [{"label": "NEUTRAL", "score": 0.5}]
                self.intent_classifier = lambda text, labels: {"labels": labels, "scores": [0.5] * len(labels)}
            except Exception as e:
                logging.error(f"NLP setup error: {e}")
                # Create simple fallback functions as above

    def analyze_sentiment(self, text):
        """Analyze sentiment with lazy loading"""
        self._ensure_nlp_loaded()
        try:
            return self.sentiment_analyzer(text)[0]
        except Exception as e:
            logging.error(f"Sentiment analysis error: {e}")
            return {"label": "NEUTRAL", "score": 0.5}

    def generate_response(self, text):
        """Generate a generic response based on input"""
        # Simple fallback response generation
        sentiment = self.analyze_sentiment(text)
        
        if sentiment["label"] == "POSITIVE":
            return random.choice([
                "That sounds great!",
                "I'm glad to hear that.",
                "Wonderful!"
            ])
        elif sentiment["label"] == "NEGATIVE":
            return random.choice([
                "I'm sorry you're feeling that way.",
                "That sounds challenging.",
                "I hope things get better."
            ])
        
        return "I'm not sure how to respond to that."

    def run(self):
        """Enhanced assistant run method"""
        # Greet user
        greeting = random.choice(self.personality["responses"]["greeting"])
        self.speech.speak(greeting)
        
        # Main conversation loop
        running = True
        while running:
            # Listen for command
            command = self.speech.listen()
            
            if not command:
                continue
            
            # Check for exit
            if "goodbye" in command or "bye" in command:
                farewell = random.choice(self.personality["responses"]["farewell"])
                self.speech.speak(farewell)
                break
            
            # Process command with enhanced intelligence
            try:
                # Update conversation history
                self.update_conversation_history(command, "user")
                
                # Process command (existing method)
                running = self.process_command(command)
                
            except Exception as e:
                logging.error(f"Error processing command: {e}")
                confusion_response = random.choice(self.personality["responses"]["confusion"])
                self.speech.speak(confusion_response)

class WeatherManager:
    def __init__(self, api_key: str):
        self.api_key = api_key
        
    def get_weather(self, city: str) -> str:
        """Get weather information for a city"""
        if not self.api_key:
            return "Weather functionality is not available (missing API key)"
            
        try:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={self.api_key}&units=metric"
            response = requests.get(url, timeout=5)  # Add timeout
            
            if response.status_code == 401:
                return "Weather API key is invalid"
            elif response.status_code == 404:
                return f"City '{city}' not found"
            elif response.status_code != 200:
                return f"Weather service unavailable (Error {response.status_code})"
                
            data = response.json()
            temp = data['main']['temp']
            desc = data['weather'][0]['description']
            return f"The temperature in {city} is {temp}°C with {desc}"
        except requests.ConnectionError:
            return "Couldn't connect to weather service. Check your internet connection."
        except requests.Timeout:
            return "Weather service request timed out. Please try again later."
        except Exception as e:
            logging.error(f"Error getting weather: {e}")
            return "Sorry, I couldn't fetch the weather information"

# features/news_manager.py
class NewsManager:
    def __init__(self, api_key: str):
        self.api_key = api_key
        
    def get_news(self) -> list:
        """Get top news headlines"""
        try:
            url = f"https://newsapi.org/v2/top-headlines?sources=techcrunch&apiKey={self.api_key}"
            response = requests.get(url)
            data = response.json()
            
            if response.status_code == 200:
                return [article["title"] for article in data["articles"][:5]]
            return ["Sorry, I couldn't fetch the news"]
        except Exception as e:
            return [f"Error getting news: {e}"]

# features/location_manager.py
class LocationManager:
    @staticmethod
    def get_location() -> dict:
        """Get current location based on IP"""
        try:
            ip = requests.get('https://api.ipify.org').text
            url = f'https://get.geojs.io/v1/ip/geo/{ip}.json'
            response = requests.get(url)
            data = response.json()
            return {
                'city': data.get('city', 'Unknown'),
                'country': data.get('country', 'Unknown'),
                'region': data.get('region', 'Unknown')
            }
        except Exception as e:
            return {'error': str(e)}

# features/social_media_manager.py

class SocialMediaManager:
    def __init__(self):
        self.insta = instaloader.Instaloader()
        
    def get_instagram_profile(self, username: str) -> str:
        """Return Instagram profile URL"""
        return f"https://www.instagram.com/{username}"
        
    def download_profile_pic(self, username: str) -> bool:
        """Download Instagram profile picture"""
        try:
            self.insta.download_profile(username, profile_pic_only=True)
            return True
        except Exception as e:
            print(f"Error downloading profile picture: {e}")
            return False

# features/wiki_manager.py
class WikiManager:
    @staticmethod
    def search(query: str, sentences: int = 2) -> str:
        """Search Wikipedia and return summary"""
        try:
            return wikipedia.summary(query, sentences=sentences)
        except Exception as e:
            return f"Error searching Wikipedia: {e}"

# features/screenshot_manager.py
class ScreenshotManager:
    def __init__(self):
        self.screenshot_dir = Path.home() / "Screenshots"
        self.screenshot_dir.mkdir(exist_ok=True)
        
    def take_screenshot(self, name: str = None) -> str:
        """Take screenshot and save with given name or timestamp"""
        try:
            if not name:
                name = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = self.screenshot_dir / f"{name}.png"
            screenshot = pyautogui.screenshot()
            screenshot.save(str(file_path))
            return str(file_path)
        except Exception as e:
            return f"Error taking screenshot: {e}"

# Update config.py to include new API keys
@dataclass
class AssistantConfig:
    """Configuration for the virtual assistant"""
    name: str = "Friday"
    voice_id: str = None
    language: str = "en-US"
    wake_word: str = "friday"
    weather_api_key: str = None
    news_api_key: str = None
    sample_rate: int = 16000
    recording_duration: int = 5
    screenshot_dir: Path = Path.home() / "Screenshots"
    
    @classmethod
    def load_config(cls):
        """Load configuration from environment variables"""
        return cls(
            weather_api_key=os.getenv("WEATHER_API_KEY"),
            news_api_key=os.getenv("NEWS_API_KEY")
        )

if __name__ == "__main__":
    assistant = VirtualAssistant()
    assistant.run()