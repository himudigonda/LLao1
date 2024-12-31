# LLao1/llao1/core/tools.py
import subprocess
import os
from exa_py import Exa

# Initialize Exa client if the key is set, otherwise set it to None
EXA_API_KEY = os.environ.get("EXA_API_KEY")
exa = Exa(api_key=EXA_API_KEY) if EXA_API_KEY else None

def execute_code(code: str) -> str:
    """
    Executes Python code in a sandboxed subprocess environment.

    Args:
        code: The Python code to execute.

    Returns:
        The output of the code execution or an error message.
    """
    try:
        result = subprocess.run(
            ["python3", "-c", code],
            capture_output=True,
            text=True,
            timeout=5,
            env={"PYTHONPATH": os.getcwd()},
        )
        return result.stdout if result.returncode == 0 else f"Error: {result.stderr}"
    except subprocess.TimeoutExpired:
        return "Error: Code execution timed out"
    except Exception as e:
        return f"Error: {str(e)}"


def web_search(query: str, num_results: int = 5) -> str:
    """
    Performs a web search using the Exa API.

    Args:
        query: The search query.
        num_results: The number of search results to retrieve.

    Returns:
        Formatted search results.
    """
    if not exa:
      return "Error: Exa API Key is not set."
    try:
        search_results = exa.search_and_contents(
            query,
            type="auto",
            use_autoprompt=True,
            num_results=num_results,
            highlights=True,
            text=True
        )

        formatted_results = []
        for idx, result in enumerate(search_results.results):
            title = result.title or 'No title found'
            snippet = result.text or 'No snippet found'
            url = result.url or 'No URL found'
            id = result.id or 'No ID found'
            formatted_results.append(
                f"Result {idx + 1}:\nID: {id}\nTitle: {title}\nSnippet: {snippet}\nURL: {url}\n"
            )
        return "\n".join(formatted_results)
    except Exception as e:
        return f"An error occurred while using Exa API: {str(e)}"


def fetch_page_content(ids: list) -> str:
    """
    Fetches and returns the text content of web pages given their IDs using the Exa API.

    Args:
        ids: A list of Exa page IDs to fetch the content from.

    Returns:
        Formatted content of the specified web pages or an error message.
    """
    if not exa:
        return "Error: Exa API Key is not set."
    try:
        page_contents = exa.get_contents(ids, text=True)

        formatted_contents = []
        for page in page_contents.results:
            title = page.title or "No title found"
            text = page.text or "No text found"
            formatted_contents.append(f"Title: {title}\nContent: {text}\n")

        return "\n".join(formatted_contents)
    except Exception as e:
        return f"An error occurred while retrieving page content: {str(e)}"
