# frontend/modules/model_management.py
import streamlit as st
import requests
from backend.core.models import ProviderType

API_BASE_URL = "http://127.0.0.1:8000/api/management"

def get_providers():
    try:
        response = requests.get(f"{API_BASE_URL}/providers/")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"获取供应商列表失败: {e}")
        return []

def handle_model_management():
    st.header("🤖 模型与供应商管理")

    st.subheader("供应商列表")
    providers = get_providers()
    if providers:
        for provider in providers:
            with st.expander(f"{provider['name']} ({provider['provider_type']})"):
                st.write(f"**Base URL:** {provider['base_url']}")
                st.write(f"**API Key:** {'*' * 10 if provider['api_key'] else 'N/A'}")
                
                st.markdown("**模型:**")
                if provider['models']:
                    for model in provider['models']:
                        st.text(f"- {model['name']}")
                else:
                    st.text("暂无模型")

    st.subheader("添加新供应商")
    with st.form("new_provider_form", clear_on_submit=True):
        name = st.text_input("供应商名称")
        provider_type = st.selectbox("供应商类型", [p.value for p in ProviderType])
        base_url = st.text_input("Base URL")
        api_key = st.text_input("API Key (可选)", type="password")
        submitted = st.form_submit_button("添加供应商")
        if submitted:
            if not name or not base_url:
                st.warning("供应商名称和 Base URL 是必填项。")
            else:

                new_provider = {
                    "name": name,
                    "provider_type": provider_type,
                    "base_url": base_url,
                    "api_key": api_key if api_key else None,
                }
                try:
                    response = requests.post(f"{API_BASE_URL}/providers/", json=new_provider)
                    if response.status_code == 200:
                        st.success("供应商添加成功！")
                        st.rerun()
                    else:
                        st.error(f"添加失败: {response.text}")
                except requests.exceptions.RequestException as e:
                    st.error(f"请求失败: {e}")

    st.subheader("为供应商添加新模型")
    if providers:
        provider_options = {p['name']: p['id'] for p in providers}
        selected_provider_name = st.selectbox("选择一个供应商", list(provider_options.keys()))
        
        with st.form("new_model_form", clear_on_submit=True):
            model_name = st.text_input("模型名称 (例如, gpt-4o)")
            # In a real app, you'd have all the fields here
            submitted_model = st.form_submit_button("添加模型")
            if submitted_model:
                if not model_name:
                    st.warning("模型名称是必填项。")
                else:
                    provider_id = provider_options[selected_provider_name]
                    new_model = {"name": model_name} # Simplified for now
                    try:
                        response = requests.post(f"{API_BASE_URL}/providers/{provider_id}/models/", json=new_model)
                        if response.status_code == 200:
                            st.success(f"模型 '{model_name}' 添加成功！")
                            st.rerun()
                        else:
                            st.error(f"添加模型失败: {response.text}")
                    except requests.exceptions.RequestException as e:
                        st.error(f"请求失败: {e}")