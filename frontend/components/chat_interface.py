import streamlit as st

def render_message(message):
    """
    Renders a single chat message with action buttons.
    """
    is_user = message["role"] == "user"
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        # Action buttons for each message
        col1, col2, col3, col4 = st.columns([1, 1, 1, 10])
        
        with col1:
            st.button("✏️", key=f"edit_{message['id']}", help="Edit")
        with col2:
            st.button("📋", key=f"copy_{message['id']}", help="Copy")
        with col3:
            st.button("🗑️", key=f"delete_{message['id']}", help="Delete")
        
        if not is_user:
            # AI-specific actions
            with col4:
                st.button("🔄", key=f"regen_{message['id']}", help="Regenerate")
                st.button("🌿", key=f"branch_{message['id']}", help="Branch")


def show_chat_interface():
    """
    Renders the main chat interface, including messages and the input form.
    """
    st.header("Chat")

    # Initialize chat history in session state if it doesn't exist
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"id": 1, "role": "assistant", "content": "Hello! How can I help you today?"}
        ]

    # Display existing messages
    for message in st.session_state.messages:
        render_message(message)

    # Chat input form
    with st.form(key="chat_input_form", clear_on_submit=True):
        col1, col2, col3 = st.columns([5, 1, 1])
        
        with col1:
            user_input = st.text_area("Your message:", key="user_input_area", height=100)
        
        with col2:
            st.form_submit_button(label="Send")
            uploaded_file = st.file_uploader("Attach file", type=None, key="file_uploader", label_visibility="collapsed")
        
        with col3:
            # Placeholder for image upload, might need a different approach
            uploaded_image = st.file_uploader("Upload image", type=['png', 'jpg', 'jpeg'], key="image_uploader", label_visibility="collapsed")

    if user_input:
        # This is where we'll handle the logic for sending the message
        # to the backend and getting a response.
        st.session_state.messages.append({"id": len(st.session_state.messages) + 1, "role": "user", "content": user_input})
        # In a real app, we would then get a response from the AI
        st.rerun()