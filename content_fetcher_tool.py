from smolagents import Tool
from content_fetcher import ContentFetcher
import requests
from urllib.parse import quote
import json

class ContentFetcherTool(Tool):
    name = "content_fetcher_tool"
    description = """Reads and extracts clean, LLM-friendly content from a file, webpage, or youtube video. 
    Provide a path or URL and it will return the main content in a clean, readable format."""
    inputs = {
        "path_or_url": {"type": "string", "description": "The path or URL of the file, webpage, or youtube video to read and extract content from."}
    }
    output_type = "string"

    def __init__(self):
        super().__init__(self)
        self.fetcher = ContentFetcher(
            max_file_size_mb=64,  # 64MB limit
            request_timeout=15,   # 15 second timeout
        )

    def forward(self, path_or_url: str) -> str:
        try:
            # Check if the input is a JSON string and extract the URL if needed
            if path_or_url.startswith('{') and 'path_or_url' in path_or_url:
                try:
                    data = json.loads(path_or_url)
                    path_or_url = data['path_or_url']
                except:
                    pass
                
            result = self.fetcher.fetch_content([path_or_url])
            if result[0]['content']:
                return result[0]['content']
            else:
                return f"Error: Failed to read content from {path_or_url}. Status code: {result[0]['error']}"
        except Exception as e:
            return f"Error occurred while reading content from {path_or_url}: {str(e)}"


if __name__ == "__main__":
    # Create an instance of the reader tool
    reader_tool = ContentFetcherTool()
    
    # List of URLs to test
    test_urls = [
        "https://arxiv.org/html/2310.19923v4",
        "https://wolf-stuff.com/blogs/wolf-facts/bernards-wolf",
        "https://www.youtube.com/watch?v=Ub78DA8wyf8"
    ]
    
    # Test each URL
    for test_url in test_urls:
        print(f"\nFetching content from: {test_url}")
        print("-" * 50)
        
        try:
            content = reader_tool.forward(test_url)
            print("Fetched Content:")
            print("-" * 50)
            print(content)
        except Exception as e:
            print(f"Error: {e}")
        
        print("-" * 50) 