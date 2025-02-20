from pathlib import Path
import datetime
import pyautogui

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