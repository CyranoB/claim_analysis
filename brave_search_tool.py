from smolagents import Tool
import html2text

class BraveSearchTool(Tool):
    name = "web_search"
    description = """Performs a Brave web search based on your query (think a Google search) then returns a string of the top search results"""
    inputs = {
        "query": {"type": "string", "description": "The search query to perform."}
    }
    output_type = "string"
    max_results = 5

    def __init__(self, max_results=5):
        super().__init__(self)
        import os
        self.brave_search_api_key   = os.getenv("BRAVE_SEARCH_API_KEY")

    def forward(self, query: str) -> str:
        import requests
        from urllib.parse import quote

        if self.brave_search_api_key is None:
            raise ValueError(
                "Missing Brave Search key. Make sure you have 'BRAVE_SEARCH_API_KEY' in your env variables."
            )
        
        url = f"https://api.search.brave.com/res/v1/web/search?q={quote(query)}&count={self.max_results}"
        headers = {
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip',
            'X-Subscription-Token': self.brave_search_api_key
        }

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            results = []
            # Initialize HTML to text converter
            h = html2text.HTML2Text()
            h.ignore_links = False
            h.ignore_images = True
            h.body_width = 0  # Disable line wrapping
            
            for item in data.get('web', {}).get('results', []):
                title = h.handle(item.get('title', 'N/A'))
                description = h.handle(item.get('description', 'N/A'))
                
                result = f"Title: {title.strip()}\n"
                result += f"URL: {item.get('url', 'N/A')}\n"
                result += f"Description: {description.strip()}\n"
                results.append(result)
            
            return "\n\n".join(results)
        else:
            return f"Error: Search request failed with status code {response.status_code}"
        



if __name__ == "__main__":

    import dotenv
    dotenv.load_dotenv()

    # Create an instance of the search tool
    search_tool = BraveSearchTool()
    
    # Test with a simple query
    test_query = "What is Python programming language?"
    print(f"\nSearching for: {test_query}\n")
    
    try:
        results = search_tool.forward(test_query)
        print("Search Results:")
        print("-" * 50)
        print(results)
    except ValueError as e:
        print(f"Error: {e}")
        


