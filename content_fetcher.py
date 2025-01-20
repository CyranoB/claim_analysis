import logging
import os
import requests
from typing import List, Dict, Optional, Callable, Union
from urllib.parse import urlparse
import mimetypes

from yt import YouTubeTranscriptDownloader

class ContentFetcher:
    def __init__(
        self, 
        user_agent: Optional[str] = None,
        max_file_size_mb: int = 10,
        request_timeout: int = 10,
        allowed_schemes: Optional[List[str]] = None
    ):
        """
        Initialize ContentFetcher with security parameters.
        
        Args:
            user_agent: Custom user agent string
            max_file_size_mb: Maximum file size in MB for local files
            request_timeout: Timeout in seconds for web requests
            allowed_schemes: List of allowed URL schemes (default: http, https)
        """
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': user_agent or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                                      'Chrome/91.0.4472.124 Safari/537.36'
        })
        self.max_file_size = max_file_size_mb * 1024 * 1024  # Convert MB to bytes
        self.request_timeout = request_timeout
        self.allowed_schemes = allowed_schemes or ['http', 'https']

    def _validate_url(self, url: str) -> bool:
        """
        Validate URL scheme and format.
        
        Args:
            url: URL to validate
            
        Returns:
            bool: True if URL is valid, False otherwise
        """
        try:
            parsed = urlparse(url)
            return bool(
                parsed.scheme and 
                parsed.netloc and 
                parsed.scheme.lower() in self.allowed_schemes
            )
        except Exception as e:
            logging.error(f"Invalid URL format: {url}, error: {e}")
            return False

    def _check_file_size(self, file_path: str) -> bool:
        """
        Check if file size is within allowed limits.
        
        Args:
            file_path: Path to the file
            
        Returns:
            bool: True if file size is acceptable, False otherwise
        """
        try:
            file_size = os.path.getsize(file_path)
            if file_size > self.max_file_size:
                logging.warning(
                    f"File size ({file_size / 1024 / 1024:.2f}MB) exceeds "
                    f"limit of {self.max_file_size / 1024 / 1024:.2f}MB"
                )
                return False
            return True
        except OSError as e:
            logging.error(f"Error checking file size: {e}")
            return False

    def fetch_with_jina(self, url: str) -> Optional[Dict]:    
        jina_url = 'https://r.jina.ai/'
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'X-Return-Format': 'markdown'
        }
        data = {
            'url': url
        }
        try:
            response = self.session.post(
                jina_url, 
                headers=headers, 
                json=data, 
                timeout=self.request_timeout
            )
            response.raise_for_status()
            json_response = response.json()
            return {
                "title": json_response.get("data", {}).get("title"),
                "description": json_response.get("data", {}).get("description", ""),
                "url": json_response.get("data", {}).get("url"),
                "content": json_response.get("data", {}).get("content"),
                "links": json_response.get("data", {}).get("links", {}),
                "error": None
            }
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to fetch {url} with Jina: {e}")
            return None

    def fetch_url_content(self, url: str) -> Dict[str, Optional[str]]:
        """
        Fetch content from a URL or local file, handling YouTube, web content, and local files.
        
        Args:
            url: URL or file path to fetch content from
            
        Returns:
            Dict containing title, description, content and URL/path
        """
        if os.path.exists(url):
            return self._fetch_file_content(url)
        if YouTubeTranscriptDownloader.is_youtube_url(url):
            return self._fetch_youtube_content(url)
        return self._fetch_web_content(url)

    def _fetch_youtube_content(self, url: str) -> Dict[str, Optional[str]]:
        """
        Fetch and process YouTube content.
        
        Args:
            url: YouTube URL
            
        Returns:
            Dict containing video title, description, transcript and URL
        """
        print(f"Fetching YouTube transcript for {url}")
        try:
            yt_downloader = YouTubeTranscriptDownloader(url)
            title = yt_downloader.get_title()
            description = yt_downloader.get_description()
            transcript = yt_downloader.download_transcript()
            
            processed_transcript = (
                self._process_youtube_transcript(transcript) 
                if isinstance(transcript, list) 
                else transcript
            )
            
            return {
                "title": title,
                "description": description,
                "content": processed_transcript,
                "url": url
            }
        except Exception as e:
            logging.error(f"Failed to fetch YouTube transcript for {url}: {e}")
            return self._create_empty_response(url)

    def _fetch_web_content(self, url: str) -> Dict[str, Optional[str]]:
        """
        Fetch general web content using Jina with URL validation.
        
        Args:
            url: Web URL
            
        Returns:
            Dict containing page title, description, content and URL
        """
        if not self._validate_url(url):
            return self._create_empty_response(url, error="Invalid URL")

        print(f"Fetching {url} with Jina")
        try:
            return self.fetch_with_jina(url)
        except Exception as e:
            logging.error(f"Failed to fetch {url} with Jina: {e}")
            return self._create_empty_response(url, error=str(e))

    def _create_empty_response(
        self, 
        url: str, 
        error: Optional[str] = None
    ) -> Dict[str, Optional[str]]:
        """Create a standardized empty response with optional error message."""
        return {
            "title": None,
            "description": None,
            "content": None,
            "url": url,
            "error": error
        }

    def _process_youtube_transcript(self, transcript_list: List[Union[Dict, str]]) -> str:
        """
        Convert YouTube transcript list into a single coherent text.
        
        Args:
            transcript_list: List of transcript entries from youtube_transcript_api
            
        Returns:
            str: Processed transcript text with timestamps
        """
        processed_text = []
        for idx, entry in enumerate(transcript_list):
            # Calculate timestamp based on position in transcript
            timestamp = idx * 30  # Approximate 30 seconds per entry
            minutes = timestamp // 60
            seconds = timestamp % 60
            
            # Extract text from entry
            text = entry.get('text', '') if isinstance(entry, dict) else str(entry)
            
            # Format entry with timestamp
            timestamp_str = f"[{minutes:02d}:{seconds:02d}]"
            processed_text.append(f"{timestamp_str} {text}")
        
        return '\n'.join(processed_text)

    def _fetch_file_content(self, file_path: str) -> Dict[str, Optional[str]]:
        """
        Fetch content from a local file with size validation.
        
        Args:
            file_path: Path to the local file
            
        Returns:
            Dict containing file name as title, content and file path as URL
        """
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")

            if not self._check_file_size(file_path):
                return self._create_empty_response(
                    file_path, 
                    error="File size exceeds maximum allowed size"
                )

            # Check file type
            mime_type, _ = mimetypes.guess_type(file_path)
            if mime_type and not mime_type.startswith(('text/', 'application/pdf')):
                return self._create_empty_response(
                    file_path, 
                    error="Unsupported file type"
                )

            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                
            return {
                "title": os.path.basename(file_path),
                "description": None,
                "content": content,
                "url": file_path,
                "error": None
            }
        except Exception as e:
            logging.error(f"Failed to read file {file_path}: {e}")
            return self._create_empty_response(file_path, error=str(e))

    def fetch_content(
        self, 
        urls: List[str], 
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[Dict[str, Optional[str]]]:
        """
        Fetch content from a list of URLs.

        :param urls: List of URLs to fetch content from
        :param progress_callback: Optional callback to update progress.
                                  It receives two integers: current and total.
        :return: List of dictionaries containing URL and content
        """
        results = []
        total = len(urls)
        for idx, url in enumerate(urls, start=1):
            try:
                content = self.fetch_url_content(url)
                results.append(content)
            except Exception as e:
                logging.error(f"Error fetching content from {url}: {str(e)}")
                results.append({'url': url, 'content': None})
            if progress_callback:
                progress_callback(idx, total)
        return results



# Example usage
if __name__ == "__main__":
    # Example usage with security parameters
    fetcher = ContentFetcher(
        max_file_size_mb=64,  # 64MB limit
        request_timeout=15,   # 15 second timeout
    )   
    urls = [
        "https://www.youtube.com/watch?v=Ub78DA8wyf8",
        "https://narwhalproject.org/wp-content/uploads/2024/12/Class-of-2014.pdf",
        "https://arxiv.org/html/2408.03314v1"
    ]
    
    def update_progress(current, total):
        print(f"Fetched {current}/{total} URLs")

    results = fetcher.fetch_content(urls, progress_callback=update_progress)
    for result in results:
        print(f"URL: {result['url']}")
        print(f"Title: {result['title']}")
        print(f"Description: {result['description']}")
        if result['content']:
            print(f"Content preview: {result['content'][:200]}...")
        else:
            print("Content: Not available")
        print("---")