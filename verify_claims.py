import os
import dotenv
import click
import sys
from rich.console import Console
from litellm import completion, litellm
from litellm.exceptions import AuthenticationError, BadRequestError
from content_fetcher import ContentFetcher

# Initialize console and load environment variables
console = Console()
# Try to load .env.local first, then fall back to .env
env_file = '.env.local' if os.path.exists('.env.local') else '.env'
dotenv.load_dotenv(env_file)

# Constants
DEFAULT_MODEL = os.getenv("LLM_MODEL", "deepseek/deepseek-chat")
DEFAULT_TEMPERATURE = 0.7
PROMPT_PATH = "analyze_claims.md"


def load_prompt(prompt_path: str) -> str:
    """
    Load and return the content of a prompt file.
    
    Args:
        prompt_path: Path to the prompt file
        
    Returns:
        str: Content of the prompt file
        
    Raises:
        FileNotFoundError: If the prompt file doesn't exist
    """
    try:
        with open(prompt_path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        console.print(f"[red]Error: Prompt file {prompt_path} not found[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error reading prompt file: {str(e)}[/red]")
        sys.exit(1)

def analyze_claims(
    path_or_url: str | None = None,
    model_name: str | None = None,
    temperature: float = DEFAULT_TEMPERATURE
) -> None:
    """Analyze claims in content from file, URL or stdin using an LLM."""
    # Initialize content fetcher
    fetcher = ContentFetcher(max_file_size_mb=64, request_timeout=15)

    # Get content from file/URL or stdin
    try:
        content = (
            fetcher.fetch_url_content(path_or_url)['content'] if path_or_url 
            else sys.stdin.read()
        )
        if not content:
            console.print(f"[red]Error: No content found in {path_or_url or 'stdin'}[/red]")
            return
    except Exception as e:
        console.print(f"[red]Error fetching content: {str(e)}[/red]")
        return

    # Run LLM analysis
    try:
        response = completion(
            model=model_name or DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": load_prompt(PROMPT_PATH).format()},
                {"role": "user", "content": content}
            ],
            temperature=temperature,
            metadata={"source": path_or_url or "stdin", 
                     "model": model_name or DEFAULT_MODEL,
                     "temperature": temperature}
        )
        console.print("\n[bold green]Claims Analysis:[/bold green]")
        console.print(response.choices[0].message.content)
    except Exception as e:
        console.print(f"[red]Error during analysis: {str(e)}[/red]")
        return

@click.command()
@click.argument('source', required=False, type=str)
@click.option('--model', '-m', help=f'Model to use for analysis (default: {DEFAULT_MODEL})')
@click.option('--temperature', '-t', type=float, default=DEFAULT_TEMPERATURE, 
              help=f'Temperature for LLM generation (default: {DEFAULT_TEMPERATURE})')
def main(source: str, model: str, temperature: float):
    """Analyze claims in content from a file path, URL or stdin using an LLM."""
    analyze_claims(source, model, temperature)

if __name__ == "__main__":
    main()

