import webbrowser
import pywhatkit as kit

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
