# LLao1/llao1/ui/app.py
import streamlit as st
from llao1.core.reasoning import generate_reasoning_steps
from llao1.ui.components import display_steps
from llao1.utils.export import export_data
from llao1.utils.config import DEFAULT_THINKING_TOKENS
import os
import tempfile
import json
import base64
from PIL import Image
from io import BytesIO
import traceback


def main():
    st.set_page_config(page_title="LLao1", page_icon="🧠", layout="wide")
    st.title("LLao1")
    st.markdown("---")

    # Initialize session state for steps and errors
    if "steps" not in st.session_state:
        st.session_state["steps"] = []
    if "error" not in st.session_state:
        st.session_state["error"] = None
    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    # UI elements
    with st.sidebar:
        st.header("Settings")
        thinking_tokens = st.number_input(
            "Thinking Tokens:",
            min_value=100,
            max_value=2000,
            value=DEFAULT_THINKING_TOKENS,
            step=50,
            help="Adjust the number of tokens for each reasoning step",
        )
        model_name = st.text_input(
            "Ollama Model:",
            value="llama3.2-vision",
            help="The name of the ollama model.",
        )
        temperature = st.slider(
            "Temperature:",
            min_value=0.0,
            max_value=1.0,
            value=0.2,
            step=0.05,
            help="Controls randomness of the model output.",
        )
        image_file = st.file_uploader(
            "Upload an image (optional)", type=["png", "jpg", "jpeg"]
        )
        st.markdown("---")
        time_container = st.empty()

    user_query = st.text_area(
        "Enter your query:",
        placeholder="e.g., What is the square root of 256 plus the sine of pi/4?",
    )

    error_container = st.empty()  # For displaying errors prominently
    thinking_message_container = st.empty()  # added for thinking message

    if user_query:
        st.session_state["steps"] = []  # Clear the steps on a new query
        st.session_state["error"] = None
        thinking_message_container.markdown("Thinking...")
        response_container = st.empty()
        image_path = None

        if image_file:
            try:
                image_path = save_image_from_upload(image_file)
                if not image_path:
                    st.session_state["error"] = "Error saving image, see logs."
                    error_container.error("Error saving image, check the logs.")
                    st.stop()
            except Exception as e:
                st.session_state["error"] = f"Error saving image: {e}"
                error_container.error(f"Error saving image: {e}")
                thinking_message_container.empty()
                st.stop()

        steps_generator = generate_reasoning_steps(
            user_query,
            thinking_tokens=thinking_tokens,
            model=model_name,
            image_path=image_path,
            previous_messages=st.session_state["messages"],
            temperature=temperature,
        )
        steps = []
        total_thinking_time = 0
        step_counter = 1
        total_tokens_thinking = 0
        try:
            while True:
                try:
                    new_steps, thinking_time, step_tokens = next(
                        steps_generator
                    )  # get step tokens
                    # Filter out steps with "No Title"
                    filtered_steps = []
                    for (
                        title,
                        content,
                        time,
                        tool,
                        tool_input,
                        tool_result,
                    ) in new_steps:
                        if title.startswith("Step") and "No Title" in title:
                            print(
                                f"[DEBUG] llao1.ui.app.main :: Skipping step: {title}"
                            )
                            continue  # Skip this one
                        else:
                            filtered_steps.append(
                                (
                                    f"{title.split(': ', 1)[1] if ': ' in title else title}",
                                    content,
                                    time,
                                    tool,
                                    tool_input,
                                    tool_result,
                                )
                            )
                            step_counter += 1
                    steps = filtered_steps
                    if thinking_time is not None:
                        total_thinking_time = thinking_time
                    if step_tokens:
                        total_tokens_thinking += step_tokens
                    with response_container.container():
                        display_steps(steps)

                    st.session_state["steps"] = steps

                    # Append assistant message to the session state
                    st.session_state["messages"].append(
                        {"role": "user", "content": user_query}
                    )
                    for (
                        title,
                        content,
                        time,
                        tool,
                        tool_input,
                        tool_result,
                    ) in new_steps:
                        st.session_state["messages"].append(
                            {
                                "role": "assistant",
                                "content": json.dumps(
                                    {
                                        "title": title,
                                        "content": content,
                                        "tool": tool,
                                        "tool_input": tool_input,
                                        "tool_result": tool_result,
                                    }
                                ),
                            }
                        )

                except StopIteration:
                    print("[DEBUG] llao1.ui.app.main :: Reasoning generator finished.")
                    break
                except Exception as e:
                    print(f"[ERROR] llao1.ui.app.main :: Error in reasoning loop: {e}")
                    st.session_state["error"] = (
                        f"An unexpected error has occurred: {str(e)}"
                    )
                    error_container.error(f"An unexpected error has occurred: {str(e)}")
                    break
        except Exception as e:
            st.session_state["error"] = f"An unexpected error has occurred: {str(e)}"
            error_container.error(f"An unexpected error has occurred: {str(e)}")
            print(
                f"[ERROR] llao1.ui.app.main :: An unexpected error occurred: {traceback.format_exc()}"
            )

        finally:
            # Always try to cleanup the temp file
            if image_path:
                try:
                    print(
                        f"[DEBUG] llao1.ui.app.main :: Trying to remove temporal image: {image_path}"
                    )
                    os.remove(image_path)
                    print(
                        f"[DEBUG] llao1.ui.app.main :: Image removed successfully: {image_path}"
                    )
                except Exception as e:
                    print(
                        f"[ERROR] llao1.ui.app.main :: Error removing temporal image: {image_path} error: {e}"
                    )
            thinking_message_container.empty()  # remove thinking message
        if (
            st.session_state["steps"] and not st.session_state["error"]
        ):  # only display export button if there is data and no error.
            if st.download_button(
                label="Export Steps",
                data=export_data(user_query, st.session_state["steps"]),
                file_name="llao1_reasoning_steps.json",
                mime="application/json",
            ):
                st.write("exported")
        if total_thinking_time > 0:
            total_tokens_for_query = (step_counter - 1) * thinking_tokens
            with st.sidebar:
                time_container.markdown(
                    f"""
                **Effort spent thinking**: {total_thinking_time:.2f} units

                **# Token for the query**: {total_tokens_for_query}

                **# Tokens spent thinking**: {total_tokens_thinking}
                """
                )


def save_image_from_upload(image_file):
    """
    Saves the uploaded image to a temporary file.

    Args:
        image_file: The uploaded image file.

    Returns:
        The path to the saved image.
    """
    print(
        f"[DEBUG] llao1.ui.app.save_image_from_upload :: Function called with image: {image_file.name}"
    )

    try:
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=os.path.splitext(image_file.name)[1]
        ) as tmp_file:
            image = Image.open(image_file)
            image.save(tmp_file.name)
            print(
                f"[DEBUG] llao1.ui.app.save_image_from_upload :: Image saved to: {tmp_file.name}"
            )
            return tmp_file.name
    except Exception as e:
        print(f"[ERROR] llao1.ui.app.save_image_from_upload :: Error saving image: {e}")
        raise Exception(f"Error saving image: {e}") from e


if __name__ == "__main__":
    main()
