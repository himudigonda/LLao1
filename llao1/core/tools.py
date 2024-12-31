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
    print(f"[DEBUG] llao1.core.tools.execute_code :: Function called with code: {code}")
    try:
        result = subprocess.run(
            ["python3", "-c", code],
            capture_output=True,
            text=True,
            timeout=5,
            env={"PYTHONPATH": os.getcwd()},
        )
        if result.returncode == 0:
            print(f"[DEBUG] llao1.core.tools.execute_code :: Code executed successfully. Output: {result.stdout}")
            return result.stdout
        else:
            print(f"[ERROR] llao1.core.tools.execute_code :: Code execution failed. Error: {result.stderr}")
            return f"Error: {result.stderr}"
    except subprocess.TimeoutExpired:
        print(f"[ERROR] llao1.core.tools.execute_code :: Code execution timed out")
        return "Error: Code execution timed out"
    except Exception as e:
        print(f"[ERROR] llao1.core.tools.execute_code :: An error occurred during code execution: {e}")
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
    print(f"[DEBUG] llao1.core.tools.web_search :: Function called with query: {query}, num_results: {num_results}")
    if not exa:
      print(f"[ERROR] llao1.core.tools.web_search :: Exa API Key is not set.")
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
        print(f"[DEBUG] llao1.core.tools.web_search :: Exa API search results: {search_results}")

        formatted_results = []
        for idx, result in enumerate(search_results.results):
            title = result.title or 'No title found'
            snippet = result.text or 'No snippet found'
            url = result.url or 'No URL found'
            id = result.id or 'No ID found'
            formatted_results.append(
                f"Result {idx + 1}:\nID: {id}\nTitle: {title}\nSnippet: {snippet}\nURL: {url}\n"
            )
        formatted_results_str = "\n".join(formatted_results)
        print(f"[DEBUG] llao1.core.tools.web_search :: Formatted search results: {formatted_results_str}")
        return formatted_results_str
    except Exception as e:
        print(f"[ERROR] llao1.core.tools.web_search :: An error occurred while using Exa API: {e}")
        return f"An error occurred while using Exa API: {str(e)}"


def fetch_page_content(ids: list) -> str:
    """
    Fetches and returns the text content of web pages given their IDs using the Exa API.

    Args:
        ids: A list of Exa page IDs to fetch the content from.

    Returns:
        Formatted content of the specified web pages or an error message.
    """
    print(f"[DEBUG] llao1.core.tools.fetch_page_content :: Function called with ids: {ids}")
    if not exa:
      print(f"[ERROR] llao1.core.tools.fetch_page_content :: Exa API Key is not set.")
      return "Error: Exa API Key is not set."
    try:
        page_contents = exa.get_contents(ids, text=True)
        print(f"[DEBUG] llao1.core.tools.fetch_page_content :: Exa API page contents: {page_contents}")

        formatted_contents = []
        for page in page_contents.results:
            title = page.title or "No title found"
            text = page.text or "No text found"
            formatted_contents.append(f"Title: {title}\nContent: {text}\n")

        formatted_contents_str = "\n".join(formatted_contents)
        print(f"[DEBUG] llao1.core.tools.fetch_page_content :: Formatted page contents: {formatted_contents_str}")
        return formatted_contents_str
    except Exception as e:
        print(f"[ERROR] llao1.core.tools.fetch_page_content :: An error occurred while retrieving page content: {e}")
        return f"An error occurred while retrieving page content: {str(e)}"
