import os
import platform
import subprocess

class SystemManager:
    @staticmethod
    def shutdown(self, confirm=False, require_phrase=True):
        if require_phrase and not confirm:
            return "Please confirm by saying 'confirm shutdown'"
            
        if platform.system() == "Windows":
            os.system("shutdown /s /t 60")
            return "Shutting down in 60 seconds. To cancel, say 'cancel shutdown'"
        else:
            os.system("sudo shutdown -h +1")
            return "Shutting down in 60 seconds. To cancel, use 'sudo shutdown -c'"

    @staticmethod
    def cancel_shutdown():
        """Cancel a pending shutdown"""
        if platform.system() == "Windows":
            os.system("shutdown /a")
        else:
            os.system("sudo shutdown -c")
        return "Shutdown canceled"
            
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
