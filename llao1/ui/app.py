# LLao1/llao1/ui/app.py
import streamlit as st
from llao1.core.reasoning import generate_reasoning_steps
from llao1.ui.components import display_steps
from llao1.utils.export import export_data
from llao1.utils.config import DEFAULT_THINKING_TOKENS
import os
import json
import base64
from PIL import Image
from io import BytesIO

def main():
    st.set_page_config(page_title="LLao1", page_icon="🧠", layout="wide")
    st.title("LLao1: Local Reasoning with Ollama")

    st.markdown("""
    LLao1 is an experimental application that enhances reasoning capabilities through multi-step thought processing, using a local Ollama model.
    It includes tool calling capabilities for basic code execution and web search.

    Open source [repository here](https://github.com/bklieger-groq)
    """)

    # Session state for storing the steps
    if 'steps' not in st.session_state:
      st.session_state['steps'] = None

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


    if user_query:
        st.write("Generating response...")
        response_container = st.empty()
        time_container = st.empty()
        if image_file:
          image_path = save_image_from_upload(image_file)
        else:
          image_path = None

        steps_generator = generate_reasoning_steps(
                user_query,
                thinking_tokens=thinking_tokens,
                model=model_name,
                image_path=image_path,
            )
        for steps, total_thinking_time in steps_generator:
            st.session_state['steps'] = steps
            with response_container.container():
                display_steps(steps)
            if total_thinking_time is not None:
                time_container.markdown(f"**Total thinking time: {total_thinking_time:.2f} seconds**")

        if st.session_state['steps']:
            if st.download_button(
                label="Export Steps",
                data=export_data(user_query, st.session_state['steps']),
                file_name="llao1_reasoning_steps.json",
                mime="application/json",
            ):
              st.write("exported")

def save_image_from_upload(image_file):
    try:
        image = Image.open(image_file)
        temp_dir = "data"
        os.makedirs(temp_dir, exist_ok=True)
        temp_file_path = os.path.join(temp_dir, image_file.name)
        image.save(temp_file_path)
        return temp_file_path

    except Exception as e:
        st.error(f"Error saving image: {e}")
        return None


if __name__ == "__main__":
    main()
