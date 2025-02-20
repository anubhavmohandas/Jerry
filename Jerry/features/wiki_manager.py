import wikipedia

class WikiManager:
    @staticmethod
    def search(query: str, sentences: int = 2) -> str:
        """Search Wikipedia and return summary"""
        try:
            return wikipedia.summary(query, sentences=sentences)
        except Exception as e:
            return f"Error searching Wikipedia: {e}"