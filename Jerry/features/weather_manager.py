import requests
import logging

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
