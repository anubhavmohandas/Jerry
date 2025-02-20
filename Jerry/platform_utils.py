# platform_utils.py
import os
import platform
import subprocess
import logging
import winreg
from pathlib import Path
from typing import Dict, Optional, List

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
        
    @classmethod
    def is_windows_system(cls) -> bool:
        return platform.system() == "Windows"

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
                    except OSError:  # More general exception than WindowsError
                        break
        except (OSError, PermissionError) as e:
            logging.error(f"Error accessing Windows voice registry: {e}")
            # Fallback to default voice
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

    def scan_for_applications(self, max_depth=3, timeout=60) -> Dict[str, str]:
        """Dynamically scan for installed applications with timeout"""
        paths = {}
        search_locations = self.COMMON_APP_LOCATIONS.get(self.system, [])
        
        # Start timing
        start_time = time.time()
        
        for location in search_locations:
            if time.time() - start_time > timeout:
                logging.warning(f"Application scan timed out after {timeout} seconds")
                break
                
            self._scan_directory(Path(location), paths, depth=0, max_depth=max_depth)
            
        # Cache the results
        self.app_cache = paths
        return paths

    def _scan_directory(self, directory: Path, paths: Dict[str, str], depth=0, max_depth=3):
        """Recursively scan directory for applications with depth limit"""
        # Don't go too deep
        if depth > max_depth:
            return
            
        try:
            if self.is_windows:
                self._scan_windows_directory(directory, paths)
            elif self.is_mac:
                self._scan_mac_directory(directory, paths)
            else:
                self._scan_linux_directory(directory, paths)
                
            # Scan subdirectories
            if depth < max_depth:
                for subdir in directory.iterdir():
                    if subdir.is_dir():
                        self._scan_directory(subdir, paths, depth + 1, max_depth)
        except PermissionError:
            logging.debug(f"Permission denied: {directory}")
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
