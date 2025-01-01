# LLao1: An Advanced Multi-Modal Reasoning Agent

## Overview

[Watch Demo on YouTube](https://youtu.be/cw4-_47YymU)


LLao1 is a sophisticated, open-source AI reasoning agent designed to tackle complex, multi-step problems. It leverages Large Language Models (LLMs) via Ollama, coupled with powerful tools like code execution, web search, and web page content fetching. The core principle behind LLao1 is transparent, step-by-step reasoning, making it easy to understand the process behind every answer. This agent is not just a black box; it demonstrates a deliberate and auditable thought process.

LLao1 excels at tasks that require:
*   **Complex reasoning:** Breaking down problems into manageable steps.
*   **Tool usage:** Utilizing external tools for enhanced capabilities.
*   **Multi-modality:** Processing text and images in tandem.
*   **Transparency:** Providing clear, explainable reasoning.
*   **Iterative exploration**: Actively consider multiple answers and alternative paths.
*   **Self-correction**: If reasoning is incorrect, the agent revisits previous steps with a different approach to correct it.
*   **Best-practices**: Incorporates best practices in LLM agent development, not just following a list of instructions blindly.

## Key Features

*   **Step-by-Step Reasoning:** LLao1 decomposes complex problems into logical steps, each with a title, content, and a decision about the next action.
*   **Tool Integration:** Supports code execution (`code_executor`), web searching (`web_search`), and web page content fetching (`fetch_page_content`).
*   **Multi-Modal Support:** Can process both text and image inputs, making it suitable for various applications.
*   **JSON-Based Communication:** Leverages JSON for structured communication between reasoning steps and tool interactions.
*   **Ollama Integration:** Seamlessly integrates with local Ollama installations for privacy and speed.
*   **Streamlit UI:** Provides an interactive web interface for easy interaction and visualization of reasoning steps.
*   **Export Functionality:** Allows exporting the entire reasoning process as a JSON file.
*   **Error Handling:** Robust error handling at every stage, including the LLM, tool execution, and image processing.
*   **Configurable Settings:** Allows for user customization of model, thinking tokens, and temperature via the UI and constants.
*   **Context-Aware:** Maintain context across conversations.
*   **Real-time Updates:** Reasoning steps appear dynamically as they are generated.

## Architecture

LLao1's architecture is modular and designed for extensibility:

1.  **User Interface (`llao1/ui/app.py`):** A Streamlit application that provides the user interface for inputting prompts, viewing results, configuring settings, and exporting the reasoning process.

2.  **Reasoning Core (`llao1/core/reasoning.py`):** The main logic for generating reasoning steps.
    *   It takes a user prompt, system prompt and previous messages, and generates step-by-step reasoning using the specified LLM.
    *   It decides when to use available tools and keeps track of previous conversations.
    *   It uses `make_ollama_api_call` to communicate with the LLM and parses the response.

3.  **LLM Interface (`llao1/core/llm_interface.py`):** Manages communication with the Ollama API.
    *   Handles retries and errors during API calls to ensure reliability.
    *   Manages JSON-formatted responses from LLM.

4.  **Tools (`llao1/core/tools.py`):** Implements various tools that the LLM can use.
    *   `execute_code`: Executes Python code in a subprocess.
    *   `web_search`: Performs web searches using the Exa API (requires an API key).
    *   `fetch_page_content`: Retrieves web page content based on IDs from web search results.

5. **Prompts (`llao1/core/prompts.py`):**  Defines the system prompt used to guide the LLM's reasoning behavior.
    *   It emphasizes step-by-step explanations and use of tools when necessary.

6.  **Image Utils (`llao1/models/image_utils.py`):** Provides functionality for encoding images into base64 strings, enabling multi-modal input to LLM.

7.  **Configuration (`llao1/utils/config.py`):** Stores default values for LLM and reasoning parameters, such as thinking tokens and default model.

8.  **Export (`llao1/utils/export.py`):** Provides the functionality to export the reasoning process to JSON format.

## Technical Deep Dive

### Reasoning Process
*   The `generate_reasoning_steps` function in `llao1/core/reasoning.py` is the heart of the reasoning engine.
*   It maintains a conversational context by managing a list of messages (`messages`) between user and assistant.
*   It handles multi-modal input, encoding images to base64 if needed.
*   For each reasoning step, it calls the LLM via `make_ollama_api_call` and parses the response.
*   It handles tool calls and adds the results to context.
*   It uses a JSON-formatted response structure from the LLM, expecting a 'title', 'content', 'next\_action', and optionally 'tool', 'tool\_input' and 'tool\_result' keys.
*   It yields the reasoning steps incrementally and also provides total execution time and tokens used.

### Tool Implementation
*   **Code Execution (`execute_code`):** Executes Python code in a sandboxed subprocess using `subprocess.run`. The subprocess runs with `capture_output=True` to capture stdout and stderr, and with a 5 second timeout using `timeout=5`. A custom `PYTHONPATH` is set to allow imports from current working directory.
*   **Web Search (`web_search`):** Leverages the `exa-py` library to perform searches with highlights. It uses `exa.search_and_contents` with `type="auto"` and `use_autoprompt=True` to get accurate results, also returning the ID, title, and text of the search results. The `num_results` parameter lets the user specify the number of search results.
*   **Page Content Fetching (`fetch_page_content`):** Uses the `exa-py` library to fetch page contents given a list of ids returned from `web_search` using `exa.get_contents` with `text=True`, allowing the bot to check the most up to date information. It formats the response with the title and text content of the pages.

### LLM Interaction
*   The `make_ollama_api_call` function in `llao1/core/llm_interface.py` manages interactions with Ollama using `ollama.chat`.
*   It handles API call retries (3 attempts) using a `for` loop with `time.sleep(1)` between retries to ensure reliability.
*   It increases token usage by 100 if any tool is called to increase precision.
*   It handles JSON decoding with `json.loads`. If the decoding fails, a error message is generated.
*   The system prompt in `llao1/core/prompts.py` enforces the desired reasoning behavior and also allows the tool usage.

### User Interface (`llao1/ui/app.py` and `llao1/ui/components.py`)
*   The UI is built using **Streamlit**, a Python framework for creating interactive web applications.
*   The main application logic is in `llao1/ui/app.py`, where Streamlit's functions for layouts, session state management, and UI elements are used.
*   **Layout:** The UI is split into a sidebar (for settings) and a main panel (for the user prompt and reasoning steps).
*   **Settings:** The sidebar provides input fields for configuring LLM settings:
    *   `st.number_input`: For adjusting `thinking_tokens`, controlling the length of each reasoning step.
    *   `st.text_input`: For specifying the `Ollama Model`, allowing users to pick the desired model.
    *   `st.slider`: For adjusting the LLM `temperature`, changing how random the responses will be.
    *   `st.file_uploader`: For uploading image files, supporting PNG, JPG, and JPEG formats.
*   **Session State:** Streamlit's session state (`st.session_state`) is used to maintain state across interactions, namely `steps`, `error` and `messages`. It is crucial for multi-turn conversations to maintain context.
*   **User Prompt:** A `st.text_area` element takes the user's query.
*   **Real-Time Display:**
    *   The reasoning steps are displayed using `display_steps`, dynamically updated as they become available with a `st.empty` container.
    *   The steps are displayed using `st.expander` elements to show the title and the full content in a collapsible fashion, making it easy to hide them when desired.
    *   The `display_steps` function in `llao1/ui/components.py` is responsible for structuring and formatting each step's content for display.
    *   For each step, if the tool is used, the tool, the input and the result is displayed.
    *   For the final answer, the title and content are displayed without an expander.
    *   The thinking time is displayed in each step and also in the sidebar.
*   **Error Handling:** A `st.empty` element is used to display errors prominently.  The session state is used to keep track of errors to not lose the state in case of an error.
*   **Image Handling:**
    *   The image is saved to a temporal file using `tempfile.NamedTemporaryFile`.
    *   The method `save_image_from_upload` uses `PIL` to open and save the file, converting into `.jpg`.
    *   After the process is complete, the temporal file is deleted.
*   **Export Functionality:** A `st.download_button` allows exporting the data to a JSON file using `llao1.utils.export.export_data`.
*   **Feedback:** The UI provides feedback to users with a `st.empty` container for a "Thinking" message while the reasoning engine is working. Once the final answer is generated, this container disappears.
*   **Metrics:** The UI calculates the total time and tokens consumed during reasoning, displaying them in the sidebar (`st.sidebar`).

### Image Encoding
*   The `encode_image_base64` in `llao1/models/image_utils.py` handles image encoding to base64 for multi-modal LLMs. The method uses the `PIL` library to open and save the image to a `BytesIO` object in JPEG format and then it is encoded to base64. It handles errors if the file can't be encoded or does not exist.

### Configuration and Environment Variables
*   The `llao1/utils/config.py` defines `DEFAULT_THINKING_TOKENS` and `DEFAULT_MODEL`.
*   The `EXA_API_KEY` environment variable is used to configure the Exa API client for web searching, if the API is available.

### Error Handling
*   The project incorporates robust error handling at various points, including image processing, tool execution, API calls and JSON decoding.
*   Errors are caught using `try/except` blocks and are displayed in the Streamlit UI using `st.error`.
*   Logs are printed for debugging purposes, giving context to the errors, using Python's print function.

## Getting Started

### Prerequisites

1.  **Python 3.10+:** Ensure you have Python 3.10 or higher installed.

2.  **Ollama:** Install Ollama and have an LLM model downloaded.  It is recommended to use `llama3.2-vision`.  See [Ollama's website](https://ollama.com) for installation instructions.

3.  **Exa API Key (Optional):** If you wish to use web search functionality, obtain an API key from [Exa](https://exa.ai) and set it as an environment variable `EXA_API_KEY`.

4.  **Pip:** Ensure you have pip installed.

### Installation

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/himudigonda/LLao1
    cd LLao1
    ```

2.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### Running the Application

0. **Export `EXA_API_KEY` and `HUGGINGFACE_API_KEY`.**
   ```bash
   export EXA_API_KEY="thisisafakekeyuseyourkey"
   export HUGGINGFACE_API_KEY="thisisnotthekeylol"
   ``` 
1.  **Make `run.sh` executable**
    ```bash
    chmod +x ./run.sh
    ```

2.  **Run `run.sh`:**
    ```bash
    ./run.sh
    ```

3.  **Access via Browser:**
    Open your web browser and go to the URL that Streamlit provides.

## Usage

1.  Enter your query in the text box.
2.  (Optional) Upload an image.
3.  Configure settings (thinking tokens, model name, temperature).
4.  The reasoning steps will be displayed in real-time using collapsible expander components.
5.  Use the "Export Steps" button to download the reasoning process as a JSON file.

## Example Usage

*   **Complex Calculation:** *"What is the result of (145 * 23) divided by the square root of 256?"*

*   **Web Research:** *"What are the most recent news about AI?"*

*   **Web Research with Specific Results**: *"Search for Python tutorials about asyncio, give me 3 results"*

*   **Web Research and Page Content Analysis:** *"Search for the latest news about autonomous vehicles. Get the page content for the first and second search result."*

*   **Code Execution:** *"Execute the following Python code and show the output: print(2**10 + 2048)"*

*   **Multi-Modal Task:** *"Describe what is in this image" (with an uploaded image)*

## Contributing

Contributions are welcome! Please submit a pull request with your proposed changes.

## License

This project is licensed under the [MIT License](LICENSE).
