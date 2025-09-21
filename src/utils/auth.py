
# src/utils/auth.py

import os
import json
import base64
import streamlit as st
from dotenv import load_dotenv
from streamlit_oauth import OAuth2Component

# --- Configuration ---
load_dotenv()
CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = os.getenv("OAUTH_REDIRECT_URI")

AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"

@st.cache_resource
def get_oauth_component():
    """Returns a singleton instance of the OAuth2Component."""
    return OAuth2Component(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        authorize_endpoint=AUTHORIZE_URL,
        token_endpoint=TOKEN_URL,
    )

def decode_id_token(token: dict) -> dict:
    """Decodes the Base64-encoded ID token from Google to get user info."""
    try:
        id_token = token.get("id_token")
        # The user info is the second part of the JWT (header.payload.signature)
        payload = id_token.split(".")[1]
        # The payload is Base64 encoded, but might have incorrect padding
        payload += "=" * (-len(payload) % 4)
        decoded_payload = base64.urlsafe_b64decode(payload)
        return json.loads(decoded_payload)
    except Exception as e:
        st.error(f"Error decoding token: {e}")
        return {}

def google_oauth_login() -> dict | None:
    """Manages the Google OAuth2 login flow."""
    oauth_component = get_oauth_component()

    if "token" not in st.session_state:
        result = oauth_component.authorize_button(
            name="Login with Google",
            icon="https://www.google.com/favicon.ico",
            redirect_uri=REDIRECT_URI,
            scope="openid email profile",
            key="google_login",
            use_container_width=True,
        )
        if result and "token" in result:
            st.session_state.token = result.get("token")
            st.rerun()
    else:
        token = st.session_state["token"]
        
        if "user_info" not in st.session_state:
            # Manually decode the id_token to get user info
            user_info = decode_id_token(token)
            if user_info:
                st.session_state.user_info = user_info
        
        if st.sidebar.button("Logout"):
            del st.session_state["token"]
            if "user_info" in st.session_state:
                del st.session_state["user_info"]
            st.rerun()
            
        return st.session_state.get("user_info")

    return None