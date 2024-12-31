# LLao1/llao1/ui/components.py
import streamlit as st
import json

def display_steps(steps):
    """
    Displays the reasoning steps in a structured manner.
    """
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

        # Ensure content is a string
        if not isinstance(content, str):
            content = json.dumps(content)

        if title.startswith("Final Answer"):
            st.markdown(f"### {title}")
            if '```' in content:
                parts = content.split('```')
                for index, part in enumerate(parts):
                    if index % 2 == 0:
                        st.markdown(part)
                    else:
                        if '\n' in part:
                            lang_line, code = part.split('\n', 1)
                            lang = lang_line.strip()
                        else:
                            lang = ''
                            code = part
                        st.code(part, language=lang)
            else:
                st.write(content.replace('\n', '<br>'), unsafe_allow_html=True)
        else:
            with st.expander(title, expanded=True):
                st.write(content.replace('\n', '<br>'), unsafe_allow_html=True)
                if tool:
                    st.markdown(f"**Tool Used:** {tool}")
                    st.markdown(f"**Tool Input:** `{tool_input}`")
                    st.markdown(f"**Tool Result:** {str(tool_result)[:200] + '...' if len(str(tool_result)) > 200 else tool_result}")
        st.markdown(f"*Thinking time: {thinking_time:.2f} seconds*")
