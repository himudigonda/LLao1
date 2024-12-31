# LLao1/llao1/core/llm_interface.py
import ollama
import json
import time
from typing import List, Dict, Any


def make_ollama_api_call(
    messages: List[Dict[str, str]],
    max_tokens: int,
    model: str = "llama3.2-vision",
    is_final_answer: bool = False,
    temperature: float = 0.2,
):
    """
    Makes an API call to Ollama with retries and error handling.

    Args:
        messages: List of message dictionaries for the LLM.
        max_tokens: Maximum number of tokens to generate.
        model: The Ollama model to use. Defaults to "llama3.2-vision".
        is_final_answer: Whether this is the final answer call. Defaults to False.
        temperature: The temperature parameter for the LLM.

    Returns:
        Response from Ollama
    """
    for attempt in range(3):
        try:
            if is_final_answer:
              response = ollama.chat(
                    model=model,
                    messages=messages,
                    options={"temperature": temperature, "num_predict": max_tokens},
                    stream=False,
                )
              return response['message']['content']
            else:
                response = ollama.chat(
                    model=model,
                    messages=messages,
                    options={"temperature": temperature, "num_predict": max_tokens},
                    format="json",
                    stream=False,
                )
                return json.loads(response["message"]["content"])

        except Exception as e:
            if attempt == 2:
                if is_final_answer:
                    return {
                        "title": "Error",
                        "content": f"Failed to generate final answer after 3 attempts. Error: {str(e)}",
                    }
                else:
                    return {
                        "title": "Error",
                        "content": f"Failed to generate step after 3 attempts. Error: {str(e)}",
                        "next_action": "final_answer",
                    }
            time.sleep(1)  # Wait for 1 second before retrying
