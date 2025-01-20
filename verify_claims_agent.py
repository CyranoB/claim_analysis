import click
from smolagents import CodeAgent, ToolCallingAgent, DuckDuckGoSearchTool, UserInputTool, GoogleSearchTool, HfApiModel, LiteLLMModel, VisitWebpageTool
from dotenv import load_dotenv
import litellm
from langfuse.decorators import observe
from brave_search_tool import BraveSearchTool
from calculator_tool import CalculatorTool
from tavily_search_tool import TavilySearchTool
from content_fetcher_tool import ContentFetcherTool
load_dotenv()


@click.command()
@click.argument('content_source')
@click.option('--is-file', '-f', is_flag=True, default=False, help='Treat the content source as a file path')
@click.option('--max-steps', '-s', default=15, help='Maximum number of steps for the agent')
@click.option('--planning-interval', '-p', default=5, help='Interval for agent planning steps')
@click.option('--verbose', '-v', is_flag=True, default=False, help='Enable verbose output')
@click.option('--model', '-m', default='deepseek/deepseek-chat', help='LiteLLM model identifier to use')
@click.option('--agent-type', '-a', type=click.Choice(['tool', 'code']), default='tool', help='Type of agent to use (tool=ToolCallingAgent, code=CodeAgent)')
def main(content_source, is_file, max_steps, planning_interval, verbose, model, agent_type):
    model = LiteLLMModel(model_id=model)
    
    # Read content from file if specified
    if is_file:
        try:
            with open(content_source, 'r') as f:
                content = f.read()
        except Exception as e:
            raise click.ClickException(f"Error reading file: {str(e)}")
    else:
        content = content_source

    # Read the analysis framework
    try:
        with open('analyze_claims.md', 'r') as f:
            analysis_framework = f.read()
    except Exception as e:
        raise click.ClickException(f"Error reading analysis framework: {str(e)}")
    
    question = f"{analysis_framework}\n\nAnalyze this content according to the framework above:\n\n{content}"
    
    tools = [
        TavilySearchTool(max_results=5), 
        ContentFetcherTool(),
        CalculatorTool()
    ]

    if agent_type == 'tool':
        agent = ToolCallingAgent(
            tools=tools, 
            model=model, 
            planning_interval=planning_interval, 
            max_steps=max_steps
        )
    else:  # code agent
        agent = CodeAgent(
            tools=tools,
            model=model,
            max_steps=max_steps
        )

    result = agent.run(question)
    
    if verbose:
        print("\nAgent Logs:")
        print(agent.logs)
        
        print("\nAgent Memory:")
        print(agent.write_inner_memory_from_logs())
        
    return result

if __name__ == '__main__':
    main()
