import requests

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