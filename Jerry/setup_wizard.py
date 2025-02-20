# setup_wizard.py
import os
import json
import platform
import speech_recognition as sr
from pathlib import Path
from typing import Dict, Optional, List, Any
import logging
from config import AssistantConfig
from platform_utils import PlatformUtils

class SetupWizard:
    """Configuration wizard for first-time setup of the virtual assistant."""
    
    def __init__(self):
        """Initialize the setup wizard."""
        self.config = AssistantConfig()
        self.platform_utils = PlatformUtils()
        self.config_file = Path.home() / ".assistant_config.json"
        self.setup_logging()
        
    def setup_logging(self):
        """Configure logging for the setup wizard."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            filename='setup_wizard.log'
        )
    
    def start_wizard(self):
        """Start the configuration wizard process."""
        print("\n" + "="*60)
        print("    VIRTUAL ASSISTANT SETUP WIZARD")
        print("="*60)
        
        print("\nWelcome to the Virtual Assistant Setup Wizard!")
        print("Let's configure your assistant to suit your needs.\n")
        
        # Check if configuration already exists
        if self.config_file.exists():
            print(f"Configuration file found at {self.config_file}")
            choice = input("Would you like to start with existing settings? (y/n): ").lower()
            if choice == 'y':
                try:
                    self.config = AssistantConfig.load_from_file(self.config_file)
                    print("Existing configuration loaded successfully.")
                except Exception as e:
                    logging.error(f"Error loading existing config: {e}")
                    print("Error loading existing configuration. Starting with defaults.")
                    self.config = AssistantConfig()
        
        # Begin configuration steps
        self.configure_basic_settings()
        self.configure_voice_settings()
        self.configure_api_keys()
        self.configure_directories()
        self.test_configuration()
        self.save_configuration()
        
        print("\n" + "="*60)
        print("    SETUP COMPLETE!")
        print("="*60)
        print(f"\nYour assistant is now configured and ready to use!")
        print(f"Configuration saved to: {self.config_file}")
        print("\nYou can edit these settings later by running this wizard again")
        print("or by manually editing the configuration file.")
        print("\nThank you for setting up your Virtual Assistant!")
        
    def configure_basic_settings(self):
        """Configure basic assistant settings."""
        print("\n" + "-"*40)
        print("BASIC SETTINGS")
        print("-"*40)
        
        # Assistant name
        name = input(f"What would you like to name your assistant? [{self.config.name}]: ")
        if name:
            self.config.name = name
            
        # Wake word
        wake_word = input(f"Set a wake word to activate your assistant [{self.config.wake_word}]: ")
        if wake_word:
            self.config.wake_word = wake_word.lower()
            
        # Language
        print("\nAvailable languages:")
        languages = ["en-US", "en-GB", "fr-FR", "de-DE", "es-ES", "it-IT"]
        for i, lang in enumerate(languages, 1):
            print(f"  {i}. {lang}")
            
        lang_choice = input(f"\nSelect language (1-{len(languages)}) [{languages.index('en-US')+1}]: ")
        if lang_choice and lang_choice.isdigit():
            idx = int(lang_choice) - 1
            if 0 <= idx < len(languages):
                self.config.language = languages[idx]
                
    def configure_voice_settings(self):
        """Configure voice and speech settings."""
        print("\n" + "-"*40)
        print("VOICE SETTINGS")
        print("-"*40)
        
        # Get available voices
        available_voices = self._get_available_voices()
        if available_voices:
            print("\nAvailable system voices:")
            for i, voice in enumerate(available_voices, 1):
                # Extract just the voice name for clarity
                voice_name = voice.split('\\')[-1] if '\\' in voice else voice
                print(f"  {i}. {voice_name}")
                
            voice_choice = input(f"\nSelect voice (1-{len(available_voices)}): ")
            if voice_choice and voice_choice.isdigit():
                idx = int(voice_choice) - 1
                if 0 <= idx < len(available_voices):
                    self.config.voice_id = available_voices[idx]
        else:
            print("No system voices detected. Using system default.")
            self.config.voice_id = self.platform_utils.get_default_voice()
            
        # Configure speech recording duration
        duration = input(f"Set maximum recording duration in seconds [{self.config.recording_duration}]: ")
        if duration and duration.isdigit():
            self.config.recording_duration = int(duration)
            
        # Configure sample rate
        sample_rate = input(f"Set audio sample rate in Hz [{self.config.sample_rate}]: ")
        if sample_rate and sample_rate.isdigit():
            self.config.sample_rate = int(sample_rate)
            
        # Test microphone
        print("\nTesting microphone...")
        mic_status = self._test_microphone()
        if mic_status:
            print("✓ Microphone is working correctly.")
        else:
            print("⚠ Microphone test failed. Please check your audio settings.")
            
    def configure_api_keys(self):
        """Configure API keys for various services."""
        print("\n" + "-"*40)
        print("API SETTINGS")
        print("-"*40)
        
        print("\nAPI keys are needed for certain features like weather and news.")
        print("You can skip this step and add them later.")
        
        # Weather API
        weather_key = input(f"OpenWeatherMap API Key [{self._mask_key(self.config.weather_api_key)}]: ")
        if weather_key:
            self.config.weather_api_key = weather_key
            
        # News API
        news_key = input(f"NewsAPI Key [{self._mask_key(self.config.news_api_key)}]: ")
        if news_key:
            self.config.news_api_key = news_key
            
    def configure_directories(self):
        """Configure directory settings."""
        print("\n" + "-"*40)
        print("DIRECTORY SETTINGS")
        print("-"*40)
        
        # Screenshot directory
        current_dir = str(self.config.screenshot_dir)
        screenshot_dir = input(f"Screenshot directory [{current_dir}]: ")
        if screenshot_dir:
            path = Path(screenshot_dir).expanduser().resolve()
            try:
                path.mkdir(parents=True, exist_ok=True)
                self.config.screenshot_dir = path
                print(f"✓ Screenshot directory set to: {path}")
            except Exception as e:
                logging.error(f"Error creating directory: {e}")
                print(f"⚠ Error setting directory: {e}")
                print(f"Using default directory: {current_dir}")
                
    def test_configuration(self):
        """Test the current configuration."""
        print("\n" + "-"*40)
        print("CONFIGURATION TEST")
        print("-"*40)
        
        tests_passed = 0
        total_tests = 3
        
        # Test 1: Configuration validation
        print("\nValidating configuration...")
        if self._validate_config():
            print("✓ Configuration validation passed.")
            tests_passed += 1
        else:
            print("⚠ Configuration has issues. Check the log for details.")
            
        # Test 2: Directory access
        print("\nTesting directory access...")
        if self._test_directory_access():
            print("✓ Directory access test passed.")
            tests_passed += 1
        else:
            print("⚠ Directory access test failed. Check permissions.")
            
        # Test 3: API key validation (if provided)
        print("\nTesting API keys...")
        api_status = self._test_api_keys()
        if api_status == "pass":
            print("✓ API key test passed.")
            tests_passed += 1
        elif api_status == "skip":
            print("- API key test skipped (no keys provided).")
            total_tests -= 1
        else:
            print("⚠ API key test failed. Keys may be invalid.")
            
        # Summary
        print(f"\nTests completed: {tests_passed}/{total_tests} passed")
        
    def save_configuration(self):
        """Save the configuration to file."""
        try:
            # Convert Path objects to strings
            config_dict = {k: str(v) if isinstance(v, Path) else v 
                          for k, v in self.config.__dict__.items()}
            
            with open(self.config_file, 'w') as f:
                json.dump(config_dict, f, indent=2)
                
            print("\n✓ Configuration saved successfully!")
            
            # Create environment variable guide
            self._create_env_guide()
            
        except Exception as e:
            logging.error(f"Error saving configuration: {e}")
            print(f"\n⚠ Error saving configuration: {e}")
            
    def _get_available_voices(self) -> List[str]:
        """Get list of available system voices."""
        try:
            if self.platform_utils.is_windows:
                return self.platform_utils._get_windows_voices()
            elif self.platform_utils.is_mac:
                return self.platform_utils._get_mac_voices()
            else:
                return self.platform_utils._get_linux_voices()
        except Exception as e:
            logging.error(f"Error getting system voices: {e}")
            return []
            
    def _test_microphone(self) -> bool:
        """Test microphone functionality."""
        try:
            recognizer = sr.Recognizer()
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=1)
                return True
        except Exception as e:
            logging.error(f"Microphone test failed: {e}")
            return False
            
    def _validate_config(self) -> bool:
        """Validate the current configuration."""
        try:
            # Check required fields
            if not self.config.name or not self.config.wake_word:
                logging.error("Missing required configuration fields")
                return False
                
            # Validate numeric values
            if not isinstance(self.config.sample_rate, int) or self.config.sample_rate <= 0:
                logging.error(f"Invalid sample rate: {self.config.sample_rate}")
                return False
                
            if not isinstance(self.config.recording_duration, int) or self.config.recording_duration <= 0:
                logging.error(f"Invalid recording duration: {self.config.recording_duration}")
                return False
                
            return True
        except Exception as e:
            logging.error(f"Configuration validation error: {e}")
            return False
            
    def _test_directory_access(self) -> bool:
        """Test access to configured directories."""
        try:
            # Test screenshot directory
            test_file = self.config.screenshot_dir / ".test_access"
            with open(test_file, 'w') as f:
                f.write("test")
            test_file.unlink()  # Delete the test file
            return True
        except Exception as e:
            logging.error(f"Directory access test failed: {e}")
            return False
            
    def _test_api_keys(self) -> str:
        """Test API keys for validity."""
        if not self.config.weather_api_key and not self.config.news_api_key:
            return "skip"
            
        # TODO: Implement actual API testing
        # For now, just check if keys look valid (non-empty)
        if (self.config.weather_api_key and len(self.config.weather_api_key) < 10) or \
           (self.config.news_api_key and len(self.config.news_api_key) < 10):
            return "fail"
            
        return "pass"
        
    def _mask_key(self, key: Optional[str]) -> str:
        """Mask API key for display."""
        if not key:
            return "(not set)"
        if len(key) <= 8:
            return "*" * len(key)
        return key[:4] + "*" * (len(key) - 8) + key[-4:]
        
    def _create_env_guide(self):
        """Create a guide for setting environment variables."""
        env_file = Path.home() / ".assistant_env_guide.txt"
        
        try:
            with open(env_file, 'w') as f:
                f.write("# Virtual Assistant Environment Variables\n")
                f.write("# You can set these variables in your environment to override config file values\n\n")
                
                if platform.system() == "Windows":
                    f.write("# Windows (Command Prompt)\n")
                    f.write("set WEATHER_API_KEY=your_key_here\n")
                    f.write("set NEWS_API_KEY=your_key_here\n\n")
                    
                    f.write("# Windows (PowerShell)\n")
                    f.write("$env:WEATHER_API_KEY=\"your_key_here\"\n")
                    f.write("$env:NEWS_API_KEY=\"your_key_here\"\n\n")
                else:
                    f.write("# Linux/macOS (Bash/Zsh)\n")
                    f.write("export WEATHER_API_KEY=your_key_here\n")
                    f.write("export NEWS_API_KEY=your_key_here\n\n")
                    
                f.write("# To make these permanent, add them to your shell profile file\n")
                f.write("# (.bashrc, .zshrc, etc.)\n")
                
            print(f"\nEnvironment variable guide created at: {env_file}")
            
        except Exception as e:
            logging.error(f"Error creating environment guide: {e}")

if __name__ == "__main__":
    wizard = SetupWizard()
    wizard.start_wizard()