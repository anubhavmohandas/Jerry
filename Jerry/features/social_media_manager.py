import instaloader

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