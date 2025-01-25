from yt_dlp import YoutubeDL
import click
import re
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs
from typing import List

class YouTubeTranscriptDownloader:
    YOUTUBE_PATTERNS = [
        r'^https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+',
        r'^https?://(?:www\.)?youtu\.be/[\w-]+',
        r'^https?://(?:www\.)?youtube\.com/embed/[\w-]+',
        r'^https?://(?:www\.)?youtube\.com/v/[\w-]+',
    ]

    def __init__(self, url: str):
        if not self.is_youtube_url(url):
            raise ValueError('Invalid YouTube URL')
        self.url = url
        self.video_id = self.get_video_id(url)

    @staticmethod
    def is_youtube_url(url: str) -> bool:
        return any(re.match(pattern, url) for pattern in YouTubeTranscriptDownloader.YOUTUBE_PATTERNS)

    def get_video_info(self) -> dict:
        ydl_opts = {
            'quiet': True,
            'skip_download': True,
        }
        with YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(f"https://www.youtube.com/watch?v={self.video_id}", download=False)

    def get_title(self) -> str:
        try:
            info_dict = self.get_video_info()
            return info_dict.get('title', 'Unknown Title')
        except Exception as e:
            raise RuntimeError(f"Failed to get video title: {e}")

    def get_description(self) -> str:
        try:
            info_dict = self.get_video_info()
            return info_dict.get('description', 'No Description')
        except Exception as e:
            raise RuntimeError(f"Failed to get video description: {e}")

    def get_video_id(self, url: str) -> str:
        parsed_url = urlparse(url)
        if parsed_url.hostname in ('youtu.be', 'www.youtu.be'):
            return parsed_url.path[1:]
        if parsed_url.hostname in ('youtube.com', 'www.youtube.com'):
            if parsed_url.path == '/watch':
                return parse_qs(parsed_url.query).get('v', [None])[0]
            if parsed_url.path.startswith(('/embed/', '/v/')):
                return parsed_url.path.split('/')[2]
        raise ValueError('Invalid YouTube URL')

    def paginate_transcript(self, language: str = None) -> str:
        try:
            transcripts = YouTubeTranscriptApi.list_transcripts(self.video_id)
            
            # Get list of available transcripts
            try:
                manual_transcripts = transcripts._manually_created_transcripts
                auto_transcripts = transcripts._generated_transcripts
                all_langs = list(manual_transcripts.keys()) + list(auto_transcripts.keys())
            except Exception as e:
                all_langs = []
            
            # Try English first if no specific language requested
            if not language:
                try:
                    if 'en' in all_langs:
                        transcript = transcripts.find_transcript(['en'])
                    else:
                        # Get first available manual transcript
                        if manual_transcripts:
                            first_lang = list(manual_transcripts.keys())[0]
                            transcript = transcripts.find_transcript([first_lang])
                        # Fall back to auto-generated transcript
                        elif auto_transcripts:
                            first_lang = list(auto_transcripts.keys())[0]
                            transcript = transcripts.find_transcript([first_lang])
                        else:
                            raise RuntimeError("No transcripts available")
                except Exception as e:
                    raise RuntimeError(f"Failed to find transcript: {str(e)}")
            else:
                # If specific language requested, try that
                transcript = transcripts.find_transcript([language])
            
            return ' '.join(entry['text'] for entry in transcript.fetch())
        except Exception as e:
            error_msg = f"Failed to download transcript: {str(e)}"
            if 'all_langs' in locals() and all_langs:
                error_msg += f"\nAvailable languages: {', '.join(all_langs)}"
            raise RuntimeError(error_msg)

    def download_transcript(self, language: str = None, page_size: int = 1000) -> List[str]:
        if page_size <= 0:
            raise ValueError("Page size must be positive")
        
        transcript_text = self.paginate_transcript(language)
        return [transcript_text[i:i + page_size] for i in range(0, len(transcript_text), page_size)]

@click.command()
@click.argument('urls', nargs=-1)  # Accept multiple URLs
@click.option('--language', '-l', help='Language of the transcript (default: try English, then original language)')
@click.option('--page-size', '-p', default=1000, help='Number of characters per page (default: 1000)')
def main(urls: tuple, language: str, page_size: int):
    """Download and print transcripts of YouTube videos with pagination."""
    if not urls:
        # Test cases if no URLs provided
        test_urls = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Rick Astley - Never Gonna Give You Up
            "https://www.youtube.com/watch?v=jNQXAC9IVRw",  # Me at the zoo (First YouTube video)
            "https://www.youtube.com/watch?v=HGNdAW-inVg",  # No 'en' transcript, 'fr'only
        ]
        urls = test_urls
        click.echo("No URLs provided. Running test cases...\n")
    
    for url in urls:
        click.echo(f"\nProcessing: {url}")
        click.echo("-" * 50)
        
        try:
            downloader = YouTubeTranscriptDownloader(url)
            
            try:
                title = downloader.get_title()
                click.echo(f"Title: {title}")
            except RuntimeError as e:
                click.echo(f"Warning: {str(e)}", err=True)
            
            try:
                description = downloader.get_description()
                click.echo(f"Description: {description}\n")
            except RuntimeError as e:
                click.echo(f"Warning: {str(e)}", err=True)

            click.echo("Transcript:")
            pages = downloader.download_transcript(language, page_size)
            for i, page in enumerate(pages, 1):
                click.echo(f"\nPage {i}:")
                click.echo(page)
                
        except ValueError as e:
            click.echo(f"Invalid input: {str(e)}", err=True)
            continue
        except RuntimeError as e:
            click.echo(f"Error: {str(e)}", err=True)
            continue
        
        click.echo("\n" + "="*50 + "\n")  # Separator between videos

if __name__ == "__main__":
    main()
