# LLao1/llao1/utils/export.py
import json
from typing import List, Tuple, Any

def export_data(user_query: str, steps: List[Tuple[str, str, float, str, str, Any]]) -> str:
    """
    Exports the user query and reasoning steps to a JSON formatted string.

    Args:
        user_query: The original user input.
        steps: A list of tuples containing step information.

    Returns:
        A JSON string containing the exported data.
    """
    exported_data = {
        "query": user_query,
        "steps": [
            {
                "title": title,
                "content": content,
                "thinking_time": thinking_time,
                "tool": tool,
                "tool_input": tool_input,
                "tool_result": tool_result
            }
            for title, content, thinking_time, tool, tool_input, tool_result in steps
        ],
    }
    return json.dumps(exported_data, indent=4)
