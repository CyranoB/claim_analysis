from smolagents import Tool
import requests
from urllib.parse import quote

class JinaReaderTool(Tool):
    name = "jina_reader_tool"
    description = """Reads and extracts clean, LLM-friendly content from a webpage using Jina Reader API. 
    Provide a URL and it will return the main content in a clean, readable format."""
    inputs = {
        "url": {"type": "string", "description": "The URL of the webpage to read and extract content from."}
    }
    output_type = "string"

    def __init__(self):
        super().__init__(self)
        self.base_url = "https://r.jina.ai/"

    def forward(self, url: str) -> str:
        try:
            # Encode the URL and append it to the Jina Reader base URL
            encoded_url = quote(url, safe='')
            reader_url = f"{self.base_url}{encoded_url}"
            
            # Request markdown format
            headers = {
                'Accept': 'text/markdown',
                'Content-Type': 'application/json'
            }
            
            # Make the request to Jina Reader
            response = requests.get(reader_url, headers=headers)
            
            if response.status_code == 200:
                return response.text
            else:
                return f"Error: Failed to read webpage. Status code: {response.status_code}. Response: {response.text[:200]}"
            
        except Exception as e:
            return f"Error occurred while reading webpage: {str(e)}"


if __name__ == "__main__":
    # Create an instance of the reader tool
    reader_tool = JinaReaderTool()
    
    # Test with a sample URL
    test_url = "https://arxiv.org/html/2310.19923v4"
    print(f"\nReading content from: {test_url}\n")
    
    try:
        content = reader_tool.forward(test_url)
        print("Extracted Content:")
        print("-" * 50)
        print(content)
    except Exception as e:
        print(f"Error: {e}") 