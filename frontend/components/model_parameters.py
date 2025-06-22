import streamlit as st
import requests

# This should be moved to a central config file later
API_BASE_URL = "http://127.0.0.1:8000/api/management"

@st.cache_data(ttl=300)
def get_available_models():
    """Fetches the list of available models from the backend API."""
    try:
        # This endpoint needs to be implemented in the backend
        response = requests.get(f"{API_BASE_URL}/models/")
        response.raise_for_status()
        # Assuming the API returns a list of model dictionaries
        models = response.json()
        # Create a display name -> model_id mapping
        return {f"{m.get('provider', 'N/A')} - {m.get('name', 'N/A')}": m.get('id') for m in models}
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to load models: {e}")
        return {"No models available": None}
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return {"Error": None}

def show_model_parameters():
    """
    Renders the model parameter settings in the sidebar.
    """
    st.header("Model Settings")

    # Model Selection
    model_options = get_available_models()
    selected_model_name = st.selectbox(
        "Model",
        options=list(model_options.keys())
    )
    st.session_state['selected_model'] = model_options.get(selected_model_name)

    # Temperature
    st.session_state['temperature'] = st.slider(
        "Temperature",
        min_value=0.0, max_value=2.0, value=0.7, step=0.05,
        help="Controls randomness. Higher values make output more random."
    )

    # Top P
    st.session_state['top_p'] = st.slider(
        "Top P",
        min_value=0.0, max_value=1.0, value=0.9, step=0.05,
        help="Nucleus sampling. Considers tokens with top p probability mass."
    )

    # Top K
    st.session_state['top_k'] = st.slider(
        "Top K",
        min_value=0, max_value=100, value=40, step=1,
        help="Filters to the k most likely next tokens."
    )

    # Stop Sequences
    st.session_state['stop_sequences'] = st.text_input(
        "Stop Sequences",
        placeholder="e.g., Human:, AI:",
        help="Comma-separated list of sequences to stop generation."
    )

    # JSON Schema Output
    with st.expander("Formatted Output (JSON Schema)"):
        st.session_state['json_schema'] = st.text_area(
            "JSON Schema",
            placeholder='{"type": "object", "properties": {"name": {"type": "string"}}}',
            height=200
        )