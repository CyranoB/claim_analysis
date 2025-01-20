from smolagents import Tool
import html2text
import os
from tavily import TavilyClient

class TavilySearchTool(Tool):
    name = "tavily_search_tool"
    description = """Performs a Tavily web search based on your query and returns a string of the top search results."""
    inputs = {
        "query": {"type": "string", "description": "The search query to perform."}
    }
    output_type = "string"
    max_results = 5

    def __init__(self, max_results=5):
        super().__init__(self)
        self.tavily_api_key = os.getenv("TAVILY_API_KEY")
        self.max_results = max_results
        if self.tavily_api_key:
            self.client = TavilyClient(api_key=self.tavily_api_key)

    def forward(self, query: str) -> str:
        if self.tavily_api_key is None:
            raise ValueError(
                "Missing Tavily API key. Make sure you have 'TAVILY_API_KEY' in your env variables."
            )
        
        try:
            # Using the SDK's search method
            response = self.client.search(
                query=query,
                max_results=self.max_results,
                search_depth="basic"
            )
            
            results = []
            # Initialize HTML to text converter
            h = html2text.HTML2Text()
            h.ignore_links = False
            h.ignore_images = True
            h.body_width = 0
            
            for item in response.get('results', []):
                title = h.handle(item.get('title', 'N/A'))
                content = h.handle(item.get('content', 'N/A'))
                url = item.get('url', 'N/A')
                
                result = f"Title: {title.strip()}\n"
                result += f"URL: {url}\n"
                result += f"Content: {content.strip()}\n"
                results.append(result)
            
            return "\n\n".join(results)
            
        except Exception as e:
            return f"Error occurred: {str(e)}"

if __name__ == "__main__":
    import dotenv
    dotenv.load_dotenv()

    # Create an instance of the search tool
    search_tool = TavilySearchTool()
    
    # Test with a simple query
    test_query = "Who received the IEEE Frank Rosenblatt Award in 2010?"
    print(f"\nSearching for: {test_query}\n")
    
    try:
        results = search_tool.forward(test_query)
        print("Search Results:")
        print("-" * 50)
        print(results)
    except ValueError as e:
        print(f"Error: {e}") 