# LLao1/llao1/core/reasoning.py
from typing import List, Dict, Tuple, Any, Generator
from llao1.core.llm_interface import make_ollama_api_call
from llao1.core.tools import execute_code, web_search, fetch_page_content
from llao1.utils.config import DEFAULT_THINKING_TOKENS, DEFAULT_MODEL
import json
import time
from llao1.core.prompts import SYSTEM_PROMPT
from llao1.models.image_utils import encode_image_base64


def generate_reasoning_steps(
    prompt: str,
    thinking_tokens: int = DEFAULT_THINKING_TOKENS,
    model: str = DEFAULT_MODEL,
    image_path: str = None,
) -> Generator[Tuple[List[Tuple[str, str, float, str, str, Any]], float], None, None]:
    """
    Generates reasoning steps using the LLM, with tool usage.

    Args:
        prompt: The user query.
        thinking_tokens: The token limit for each reasoning step.
        model: The ollama model.
        image_path: path to the image for multimodal calls.

    Returns:
        A generator yielding tuples of step details and total thinking time.
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
        {
            "role": "assistant",
            "content": "Thank you! I will now think step by step following my instructions, starting at the beginning after decomposing the problem.",
        },
    ]

    if image_path:
        try:
            base64_image = encode_image_base64(image_path)
            messages.append({"role": "user", "content": base64_image})
        except Exception as e:
            messages.append(
                {"role": "user", "content": f"Error encoding image: {str(e)}. Proceeding with text only."}
            )

    steps = []
    step_count = 1
    total_thinking_time = 0

    while True:
        start_time = time.time()
        step_data = make_ollama_api_call(
            messages,
            thinking_tokens,
            model=model,
        )
        end_time = time.time()
        thinking_time = end_time - start_time
        total_thinking_time += thinking_time

        if 'tool' in step_data:
            if step_data['tool'] == 'code_executor':
                tool_result = execute_code(step_data['tool_input'])
            elif step_data['tool'] == 'web_search':
                num_results = step_data.get('num_results', 5)
                tool_result = web_search(step_data['tool_input'], num_results)
            elif step_data['tool'] == 'fetch_page_content':
                ids = step_data['tool_input']
                if not isinstance(ids, list):
                    ids = [ids]
                tool_result = fetch_page_content(ids)
            else:
                tool_result = f"Error: Unknown tool '{step_data['tool']}'"
            step_data['tool_result'] = tool_result

        # Use .get with default values to avoid KeyError
        steps.append(
            (
                f"Step {step_count}: {step_data.get('title', 'No Title')}",
                step_data.get('content', 'No Content'),
                thinking_time,
                step_data.get('tool'),
                step_data.get('tool_input'),
                step_data.get('tool_result'),
            )
        )

        messages.append({"role": "assistant", "content": json.dumps(step_data)})
        if 'tool_result' in step_data:
            messages.append(
                {"role": "system", "content": f"Tool result: {step_data['tool_result']}"}
            )

        if step_data.get('next_action') == 'final_answer' or step_count > 15:
            break
        step_count += 1
        yield steps, None  # Yield steps for streaming before continuing, to avoid long waits.

    # Generate final answer
    messages.append(
        {
            "role": "user",
            "content": "Please provide the final answer based solely on your reasoning above. Do not use JSON formatting. Only provide the text response without any titles or preambles. Retain any formatting as instructed by the original prompt, such as exact formatting for free response or multiple choice. If you are providing a number, provide a formatted version after the raw one.",
        }
    )

    start_time = time.time()
    final_data = make_ollama_api_call(messages, 1200, is_final_answer=True, model=model)
    end_time = time.time()
    thinking_time = end_time - start_time
    total_thinking_time += thinking_time

    steps.append(("Final Answer", final_data, thinking_time, None, None, None))

    yield steps, total_thinking_time
