import streamlit as st

def show_chat_history():
    """
    Renders the chat history sidebar with rename and delete options.
    """
    st.header("History")
    
    if st.button("➕ New Chat", use_container_width=True):
        # Logic to start a new chat
        st.success("New chat created (logic pending).")

    st.divider()

    # --- Mock Data ---
    # In a real app, this would come from a database
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = {
            f"chat_{i}": f"Chat about topic {i}" for i in range(1, 21)
        }
    
    history_items = st.session_state.chat_history

    # --- Scrollable History List ---
    # We use a custom div with a specific class for styling
    st.markdown('<div class="history-container">', unsafe_allow_html=True)

    for chat_id, chat_title in history_items.items():
        col1, col2, col3 = st.columns([10, 1, 1])
        with col1:
            # Each chat is a button to switch to it
            if st.button(chat_title, key=f"select_{chat_id}", use_container_width=True):
                st.session_state['selected_chat_id'] = chat_id
                # Add logic to load the selected chat
        with col2:
            # Rename button
            if st.button("✏️", key=f"rename_{chat_id}", help="Rename"):
                st.info(f"Rename action for '{chat_title}' triggered.")
                # Add logic for a popup or text input for renaming
        with col3:
            # Delete button
            if st.button("🗑️", key=f"delete_{chat_id}", help="Delete"):
                st.warning(f"'{chat_title}' will be deleted.")
                # Add logic to delete from session_state and database
                # del st.session_state.chat_history[chat_id]
                # st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    # --- CSS for the scrollable container ---
    st.markdown("""
    <style>
        .history-container {
            max-height: 75vh; /* Adjust height as needed */
            overflow-y: auto;
            overflow-x: hidden;
            padding-right: 10px; /* For scrollbar spacing */
        }
        /* Simple scrollbar styling */
        .history-container::-webkit-scrollbar {
            width: 5px;
        }
        .history-container::-webkit-scrollbar-track {
            background: #f0f2f6;
        }
        .history-container::-webkit-scrollbar-thumb {
            background: #cccccc;
            border-radius: 5px;
        }
        .history-container::-webkit-scrollbar-thumb:hover {
            background: #aaaaaa;
        }
    </style>
    """, unsafe_allow_html=True)