import requests

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
