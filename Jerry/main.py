# main.py
import os
import random
import json
import logging
import datetime
import time
from typing import Optional
from pathlib import Path

# Local imports
from config import AssistantConfig
from platform_utils import PlatformUtils
from speech_manager import SpeechManager
from features.browser_manager import BrowserManager
from features.system_manager import SystemManager
from features.weather_manager import WeatherManager
from features.news_manager import NewsManager
from features.location_manager import LocationManager
from features.social_media_manager import SocialMediaManager
from features.wiki_manager import WikiManager
from features.screenshot_manager import ScreenshotManager

# Optional imports with error handling
try:
    from transformers import pipeline
    NLP_AVAILABLE = True
except ImportError:
    NLP_AVAILABLE = False
    print("Transformers package not installed. NLP features will be limited.")

class VirtualAssistant:
    def __init__(self):
        # Check dependencies first
        self.missing_deps, self.optional_missing = self.check_dependencies()
        if self.missing_deps:
            print(f"WARNING: Missing required dependencies: {', '.join(self.missing_deps)}")
            print("Some features will not be available.")
            print("Install with: pip install " + " ".join(self.missing_deps))
            
        if self.optional_missing:
            print(f"NOTE: Missing optional dependencies: {', '.join(self.optional_missing)}")
            print("Advanced features will be limited.")
        
        # Set NLP availability flag based on dependency check
        self.NLP_AVAILABLE = "transformers" not in self.optional_missing
        
        # Core initialization
        self.config = AssistantConfig.load_config()
        self.platform_utils = PlatformUtils()
        self.config.voice_id = self.platform_utils.get_default_voice()
        self.speech = SpeechManager(self.config.voice_id)
        self.browser = BrowserManager()
        self.system = SystemManager()
        
        # Feature managers - initialize only if dependencies available
        if "pywhatkit" not in self.missing_deps:
            self.weather = WeatherManager(self.config.weather_api_key)
            self.news = NewsManager(self.config.news_api_key)
        
        if "pyautogui" not in self.missing_deps:
            self.screenshot = ScreenshotManager()
            
        if "instaloader" not in self.missing_deps:
            self.social = SocialMediaManager()
            
        if "wikipedia" not in self.missing_deps:
            self.wiki = WikiManager()
            
        self.location = LocationManager()
        
        # App detection
        self.app_paths = self.platform_utils.get_installed_apps()
        
        # Enhanced features
        self.setup_logging()
        self.load_personality()
        self.conversation_history = []
        self.max_history_length = 10
        self.user_preferences = {}
        self.load_user_preferences()

        # Initialize NLP features as None for lazy loading
        self.sentiment_analyzer = None
        self.intent_classifier = None
        
    def check_dependencies(self):
        """Check if all required dependencies are installed"""
        missing_deps = []
        
        # Core dependencies
        try:
            import pyttsx3
        except ImportError:
            missing_deps.append("pyttsx3")
        
        try:
            import speech_recognition
        except ImportError:
            missing_deps.append("speech_recognition")
        
        # Feature dependencies
        try:
            import pywhatkit
        except ImportError:
            missing_deps.append("pywhatkit")
        
        try:
            import pyautogui
        except ImportError:
            missing_deps.append("pyautogui")
        
        try:
            import instaloader
        except ImportError:
            missing_deps.append("instaloader")
        
        try:
            import wikipedia
        except ImportError:
            missing_deps.append("wikipedia")
        
        # Optional dependencies
        optional_deps = []
        try:
            import transformers
        except ImportError:
            optional_deps.append("transformers")
        
        return missing_deps, optional_deps

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
        """Process user command with improved validation"""
        # Basic validation
        if not command or not isinstance(command, str):
            return True
            
        # Sanitize input (allow URL characters and other safe special chars)
        command = command.lower().strip()
        
        # Only block potentially dangerous characters
        dangerous_chars = set('`$(){}[]&|;\\')
        if any(c in dangerous_chars for c in command):
            self.speech.speak("I'm sorry, that command contains characters I can't process.")
            return True
            
        # Update conversation history
        self.update_conversation_history(command, "user")
            
        # Basic commands
        if "goodbye" in command or "bye" in command:
            self.speech.speak("Goodbye! Have a great day!")
            return False
            
        # Browser commands
        elif "open youtube" in command:
            if hasattr(self, 'browser'):
                self.browser.open_url("youtube.com")
            else:
                self.speech.speak("I'm sorry, browser features are unavailable due to missing dependencies.")
        elif "play" in command:
            if "pywhatkit" not in self.missing_deps:
                query = command.replace("play", "").strip()
                self.browser.search_youtube(query)
            else:
                self.speech.speak("I'm sorry, YouTube features are unavailable due to missing dependencies.")
        elif "search" in command and "google" in command:
            if hasattr(self, 'browser'):
                query = command.replace("search", "").replace("google", "").strip()
                self.browser.search_google(query)
            else:
                self.speech.speak("I'm sorry, browser features are unavailable due to missing dependencies.")
            
        # System commands
        if "shutdown" in command:
            if hasattr(self, 'system'):
                if "confirm shutdown" in command:
                    response = self.system.shutdown(confirm=True)
                else:
                    response = self.system.shutdown(confirm=False)
                    self.speech.speak(response)
            else:
                self.speech.speak("System commands are unavailable due to missing dependencies.")
        elif "cancel shutdown" in command:
            if hasattr(self, 'system'):
                response = self.system.cancel_shutdown()
                self.speech.speak(response)
            else:
                self.speech.speak("System commands are unavailable due to missing dependencies.")
        elif "restart" in command:
            if hasattr(self, 'system'):
                self.system.restart()
            else:
                self.speech.speak("System commands are unavailable due to missing dependencies.")
        elif "sleep" in command:
            if hasattr(self, 'system'):
                self.system.sleep()
            else:
                self.speech.speak("System commands are unavailable due to missing dependencies.")
            
        # Application commands
        elif "notepad" in command or "text editor" in command:
            if hasattr(self, 'platform_utils') and hasattr(self, 'system'):
                app_path = self.platform_utils.find_application("notepad" if self.platform_utils.is_windows else "textedit")
                if app_path:
                    self.system.open_app(app_path)
            else:
                self.speech.speak("Application commands are unavailable due to missing dependencies.")
                
        # Weather commands
        elif "weather" in command:
            if hasattr(self, 'weather'):
                city = "London"  # Default city, can be extracted from command
                result = self.weather.get_weather(city)
                self.speech.speak(result)
            else:
                self.speech.speak("Weather features are unavailable due to missing dependencies.")
            
        # News commands
        elif "news" in command:
            if hasattr(self, 'news'):
                self.speech.speak("Here are today's top headlines:")
                for i, headline in enumerate(self.news.get_news(), 1):
                    self.speech.speak(f"Headline {i}: {headline}")
            else:
                self.speech.speak("News features are unavailable due to missing dependencies.")
                
        # Location commands
        elif "where am i" in command:
            if hasattr(self, 'location'):
                location = self.location.get_location()
                self.speech.speak(
                    f"You are in {location['city']}, {location['region']}, {location['country']}"
                )
            else:
                self.speech.speak("Location features are unavailable due to missing dependencies.")
                
        # Wikipedia commands
        elif "wikipedia" in command:
            if hasattr(self, 'wiki'):
                query = command.replace("wikipedia", "").strip()
                result = self.wiki.search(query)
                self.speech.speak("According to Wikipedia")
                self.speech.speak(result)
            else:
                self.speech.speak("Wikipedia features are unavailable due to missing dependencies.")
                
        # Screenshot commands
        elif "screenshot" in command or "take ss" in command:
            if hasattr(self, 'screenshot'):
                self.speech.speak("Taking screenshot")
                path = self.screenshot.take_screenshot()
                self.speech.speak(f"Screenshot saved to {path}")
            else:
                self.speech.speak("Screenshot features are unavailable due to missing dependencies.")
        
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

    def _ensure_nlp_loaded(self):
        """Lazy load NLP models when first needed"""
        if not self.NLP_AVAILABLE:
            # Create simple fallback functions
            self.sentiment_analyzer = lambda text: [{"label": "NEUTRAL", "score": 0.5}]
            self.intent_classifier = lambda text, labels: {"labels": labels, "scores": [0.5] * len(labels)}
            return

        if self.sentiment_analyzer is None:
            try:
                from transformers import pipeline
                self.sentiment_analyzer = pipeline("sentiment-analysis", 
                                          model="distilbert-base-uncased-finetuned-sst-2-english")
                self.intent_classifier = pipeline("zero-shot-classification")
                logging.info("NLP models loaded successfully")
            except Exception as e:
                logging.error(f"NLP setup error: {e}")
                # Create simple fallback functions
                self.sentiment_analyzer = lambda text: [{"label": "NEUTRAL", "score": 0.5}]
                self.intent_classifier = lambda text, labels: {"labels": labels, "scores": [0.5] * len(labels)}

    def analyze_sentiment(self, text):
        """Analyze sentiment with lazy loading"""
        self._ensure_nlp_loaded()
        try:
            return self.sentiment_analyzer(text)[0]
        except Exception as e:
            logging.error(f"Sentiment analysis error: {e}")
            return {"label": "NEUTRAL", "score": 0.5}

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
        """Main assistant loop with microphone verification"""
        # Check if required speech modules are available
        if "speech_recognition" in self.missing_deps or "pyttsx3" in self.missing_deps:
            print("ERROR: Critical voice dependencies missing.")
            print(f"Please install: pip install {' '.join(['speech_recognition', 'pyttsx3'])}")
            return
            
        # Check microphone before starting
        if not self.speech.verify_microphone():
            print("ERROR: Microphone not functioning properly.")
            print("Please check your microphone settings and restart.")
            return
        
        self.wish_user()
        
        running = True
        while running:
            command = self.speech.listen()
            if command:
                running = self.process_command(command)
                
if __name__ == "__main__":
    assistant = VirtualAssistant()
    assistant.run()