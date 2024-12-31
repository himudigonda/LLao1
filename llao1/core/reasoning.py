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
    previous_messages: List[Dict[str,str]] = None,
    temperature: float = 0.2
) -> Generator[Tuple[List[Tuple[str, str, float, str, str, Any]], float, int], None, None]:
    """
    Generates reasoning steps using the LLM, with tool usage.

    Args:
        prompt: The user query.
        thinking_tokens: The token limit for each reasoning step.
        model: The ollama model.
        image_path: path to the image for multimodal calls.
        previous_messages: List of previous messages to maintain context
        temperature: temperature for the LLM.

    Returns:
        A generator yielding tuples of step details, total thinking time, and tokens used.
    """
    print(f"[DEBUG] llao1.core.reasoning.generate_reasoning_steps :: Function called with prompt: {prompt}, thinking_tokens: {thinking_tokens}, model: {model}, image_path: {image_path}")

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
        {
            "role": "assistant",
            "content": "Thank you! I will now think step by step following my instructions, starting at the beginning after decomposing the problem.",
        },
    ]
    if previous_messages:
        print(f"[DEBUG] llao1.core.reasoning.generate_reasoning_steps :: Adding previous messages to context")
        messages.extend(previous_messages)

    print(f"[DEBUG] llao1.core.reasoning.generate_reasoning_steps :: Initial messages: {messages}")

    if image_path:
        print(f"[INFO] llao1.core.reasoning.generate_reasoning_steps :: Encoding image at path: {image_path}")
        try:
            base64_image = encode_image_base64(image_path)
            messages.append({"role": "user", "content": base64_image})
            print(f"[DEBUG] llao1.core.reasoning.generate_reasoning_steps :: Image encoded and added to messages")
        except Exception as e:
            messages.append(
                {"role": "user", "content": f"Error encoding image: {str(e)}. Proceeding with text only."}
            )
            print(f"[ERROR] llao1.core.reasoning.generate_reasoning_steps :: Error encoding image: {e}")


    steps = []
    step_count = 1
    total_thinking_time = 0
    print(f"[INFO] llao1.core.reasoning.generate_reasoning_steps :: Starting reasoning loop")
    tokens_used = 0

    while True:
        print(f"[DEBUG] llao1.core.reasoning.generate_reasoning_steps :: Starting step {step_count}")
        start_time = time.time()
        print(f"[DEBUG] llao1.core.reasoning.generate_reasoning_steps :: Calling make_ollama_api_call with messages: {messages}, tokens: {thinking_tokens}, model: {model}")

        current_thinking_tokens = thinking_tokens

        if any(tool in messages[-1]['content'] for tool in ['code_executor','web_search', 'fetch_page_content']):
             current_thinking_tokens += 100 # Increase tokens if tool is used
             print(f"[DEBUG] llao1.core.reasoning.generate_reasoning_steps :: Increasing tokens by 100 since tool is used. Tokens: {current_thinking_tokens}")
        step_data = make_ollama_api_call(
            messages,
            current_thinking_tokens,
            model=model,
            temperature=temperature
        )
        end_time = time.time()
        thinking_time = end_time - start_time
        total_thinking_time += thinking_time
        print(f"[DEBUG] llao1.core.reasoning.generate_reasoning_steps :: Received step data: {step_data}, thinking_time: {thinking_time}")

        if 'tool' in step_data:
            print(f"[INFO] llao1.core.reasoning.generate_reasoning_steps :: Tool usage detected: {step_data['tool']}")
            if step_data['tool'] == 'code_executor':
                print(f"[DEBUG] llao1.core.reasoning.generate_reasoning_steps :: Executing code: {step_data['tool_input']}")
                tool_result = execute_code(step_data['tool_input'])
            elif step_data['tool'] == 'web_search':
                num_results = step_data.get('num_results', 5)
                print(f"[DEBUG] llao1.core.reasoning.generate_reasoning_steps :: Performing web search with query: {step_data['tool_input']}, num_results: {num_results}")
                tool_result = web_search(step_data['tool_input'], num_results)
            elif step_data['tool'] == 'fetch_page_content':
                ids = step_data['tool_input']
                if not isinstance(ids, list):
                    ids = [ids]
                print(f"[DEBUG] llao1.core.reasoning.generate_reasoning_steps :: Fetching page content with IDs: {ids}")
                tool_result = fetch_page_content(ids)
            else:
                tool_result = f"Error: Unknown tool '{step_data['tool']}'"
                print(f"[ERROR] llao1.core.reasoning.generate_reasoning_steps :: Unknown tool: {step_data['tool']}")
            step_data['tool_result'] = tool_result
            print(f"[DEBUG] llao1.core.reasoning.generate_reasoning_steps :: Tool result: {tool_result}")


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
        print(f"[DEBUG] llao1.core.reasoning.generate_reasoning_steps :: Step data appended: {steps[-1]}")


        messages.append({"role": "assistant", "content": json.dumps(step_data)})
        print(f"[DEBUG] llao1.core.reasoning.generate_reasoning_steps :: Assistant message added: {json.dumps(step_data)}")
        if 'tool_result' in step_data:
            messages.append(
                {"role": "system", "content": f"Tool result: {step_data['tool_result']}"}
            )
            print(f"[DEBUG] llao1.core.reasoning.generate_reasoning_steps :: Tool result added to messages: {step_data['tool_result']}")
        tokens_used += current_thinking_tokens


        if step_data.get('next_action') == 'final_answer' or step_count > 15:
            print(f"[INFO] llao1.core.reasoning.generate_reasoning_steps :: Final answer detected or max steps reached. Breaking loop.")
            break
        step_count += 1
        print(f"[INFO] llao1.core.reasoning.generate_reasoning_steps :: Yielding steps and continuing to next step. Current steps: {steps}")
        yield steps, None, tokens_used # Yield steps for streaming before continuing, to avoid long waits.

    # Generate final answer
    print(f"[INFO] llao1.core.reasoning.generate_reasoning_steps :: Generating final answer")
    messages.append(
        {
            "role": "user",
            "content": "Please provide the final answer based solely on your reasoning above. Do not use JSON formatting. Only provide the text response without any titles or preambles. Retain any formatting as instructed by the original prompt, such as exact formatting for free response or multiple choice. If you are providing a number, provide a formatted version after the raw one.",
        }
    )
    print(f"[DEBUG] llao1.core.reasoning.generate_reasoning_steps :: Final answer prompt added to messages")

    start_time = time.time()
    print(f"[DEBUG] llao1.core.reasoning.generate_reasoning_steps :: Calling make_ollama_api_call for final answer. Model: {model}")
    final_data = make_ollama_api_call(messages, 1200, is_final_answer=True, model=model, temperature=temperature)
    end_time = time.time()
    thinking_time = end_time - start_time
    total_thinking_time += thinking_time
    print(f"[DEBUG] llao1.core.reasoning.generate_reasoning_steps :: Final answer received: {final_data}, thinking_time: {thinking_time}")


    steps.append(("Final Answer", final_data, thinking_time, None, None, None))
    print(f"[DEBUG] llao1.core.reasoning.generate_reasoning_steps :: Final answer appended to steps. Current steps: {steps}")


    print(f"[INFO] llao1.core.reasoning.generate_reasoning_steps :: Yielding final steps and total_thinking_time: {total_thinking_time}")
    yield steps, total_thinking_time, tokens_used # return total tokens
    print(f"[DEBUG] llao1.core.reasoning.generate_reasoning_steps :: Function finished")
