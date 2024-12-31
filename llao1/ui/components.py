# LLao1/llao1/ui/components.py
import streamlit as st
import json

def display_steps(steps):
    """
    Displays the reasoning steps in a structured manner.
    """
    print(f"[DEBUG] llao1.ui.components.display_steps :: Function called with steps: {steps}")
    for step in steps:
        # Unpack step information, handling both old and new formats
        if len(step) == 3:
            title, content, thinking_time = step
            tool, tool_input, tool_result = None, None, None
        elif len(step) == 6:
            title, content, thinking_time, tool, tool_input, tool_result = step
        else:
            st.error(f"Unexpected step format: {step}")
            continue

        if title.startswith("Final Answer"):
            with st.container():
              print(f"[DEBUG] llao1.ui.components.display_steps :: Displaying Final Answer: {title}")
              st.markdown(f"### {title}")
              st.markdown(content)
              st.markdown(f"*Thinking time: {thinking_time:.2f} seconds*")
        else:
            with st.expander(title, expanded=False): # default to closed
                print(f"[DEBUG] llao1.ui.components.display_steps :: Displaying Step: {title}")
                st.markdown(content)
                if tool:
                    st.markdown(f"**Tool Used:** {tool}")
                    st.markdown(f"**Tool Input:** ```{tool_input}```", unsafe_allow_html=True)
                    st.markdown(f"**Tool Result:** ```{tool_result}```", unsafe_allow_html=True)
                st.markdown(f"*Thinking time: {thinking_time:.2f} seconds*")

    print(f"[DEBUG] llao1.ui.components.display_steps :: Function finished.")
