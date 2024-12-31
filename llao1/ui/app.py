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
    st.set_page_config(page_title="LLao1", page_icon="🧠", layout="centered")
    st.title("LLao1")
    st.markdown("---")

    # Initialize session state for steps and errors
    if 'steps' not in st.session_state:
      st.session_state['steps'] = []
    if 'error' not in st.session_state:
      st.session_state['error'] = None


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
            help="The name of the ollama model."
        )
        image_file = st.file_uploader("Upload an image (optional)", type=['png', 'jpg', 'jpeg'])


    user_query = st.text_area(
        "Enter your query:", placeholder="e.g., What is the square root of 256 plus the sine of pi/4?"
    )

    error_container = st.empty() #For displaying errors prominently


    if user_query:
        st.session_state['steps'] = [] # Clear the steps on a new query
        st.session_state['error'] = None
        with st.spinner("Generating response..."):
            response_container = st.empty()
            time_container = st.empty()
            image_path = None

            if image_file:
                try:
                  image_path = save_image_from_upload(image_file)
                  if not image_path:
                      st.session_state['error'] = "Error saving image, see logs."
                      error_container.error("Error saving image, check the logs.")
                      st.stop()
                except Exception as e:
                   st.session_state['error'] = f"Error saving image: {e}"
                   error_container.error(f"Error saving image: {e}")
                   st.stop()

            steps_generator = generate_reasoning_steps(
                    user_query,
                    thinking_tokens=thinking_tokens,
                    model=model_name,
                    image_path=image_path,
                )
            steps = []
            total_thinking_time = 0
            step_counter = 1
            total_tokens_thinking = 0
            try:
              while True:
                    try:
                        new_steps, thinking_time, step_tokens = next(steps_generator) # get step tokens
                        # Filter out steps with "No Title"
                        filtered_steps = []
                        for title, content, time, tool, tool_input, tool_result in new_steps:
                            if title.startswith("Step") and "No Title" in title:
                                print(f"[DEBUG] llao1.ui.app.main :: Skipping step: {title}")
                                continue # Skip this one
                            else:
                                filtered_steps.append((f"{title.split(': ', 1)[1] if ': ' in title else title}", content, time, tool, tool_input, tool_result))
                                step_counter += 1
                        steps = filtered_steps
                        if thinking_time is not None:
                            total_thinking_time = thinking_time
                        if step_tokens:
                            total_tokens_thinking += step_tokens
                        with response_container.container():
                            display_steps(steps)
                        # time_container.markdown(f"**Total thinking time: {total_thinking_time:.2f} seconds**")

                        st.session_state['steps'] = steps


                    except StopIteration:
                        print("[DEBUG] llao1.ui.app.main :: Reasoning generator finished.")
                        break
                    except Exception as e:
                       print(f"[ERROR] llao1.ui.app.main :: Error in reasoning loop: {e}")
                       st.session_state['error'] = f"An unexpected error has occurred: {str(e)}"
                       error_container.error(f"An unexpected error has occurred: {str(e)}")
                       break

            except Exception as e:
              st.session_state['error'] = f"An unexpected error has occurred: {str(e)}"
              error_container.error(f"An unexpected error has occurred: {str(e)}")
              print(f"[ERROR] llao1.ui.app.main :: An unexpected error occurred: {traceback.format_exc()}")

            finally:
                # Always try to cleanup the temp file
                if image_path:
                    try:
                        print(f"[DEBUG] llao1.ui.app.main :: Trying to remove temporal image: {image_path}")
                        os.remove(image_path)
                        print(f"[DEBUG] llao1.ui.app.main :: Image removed successfully: {image_path}")
                    except Exception as e:
                        print(f"[ERROR] llao1.ui.app.main :: Error removing temporal image: {image_path} error: {e}")

            if total_thinking_time > 0:
              total_tokens_for_query =  (step_counter-1) * thinking_tokens
              time_container.markdown(f"""
              **Time spent thinking**: {total_thinking_time:.2f} seconds
              
              **Tokens spent thinking**: {total_tokens_thinking} tokens
              """)

        if st.session_state['steps'] and not st.session_state['error']: # only display export button if there is data and no error.
            if st.download_button(
                label="Export Steps",
                data=export_data(user_query, st.session_state['steps']),
                file_name="llao1_reasoning_steps.json",
                mime="application/json",
            ):
              st.write("exported")


def save_image_from_upload(image_file):
    """
    Saves the uploaded image to a temporary file.

    Args:
        image_file: The uploaded image file.

    Returns:
        The path to the saved image.
    """
    print(f"[DEBUG] llao1.ui.app.save_image_from_upload :: Function called with image: {image_file.name}")

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(image_file.name)[1]) as tmp_file:
            image = Image.open(image_file)
            image.save(tmp_file.name)
            print(f"[DEBUG] llao1.ui.app.save_image_from_upload :: Image saved to: {tmp_file.name}")
            return tmp_file.name
    except Exception as e:
        print(f"[ERROR] llao1.ui.app.save_image_from_upload :: Error saving image: {e}")
        raise Exception(f"Error saving image: {e}") from e



if __name__ == "__main__":
    main()
