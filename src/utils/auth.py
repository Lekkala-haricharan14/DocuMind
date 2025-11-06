import os
import json
import base64
import streamlit as st
from dotenv import load_dotenv
from streamlit_oauth import OAuth2Component

load_dotenv()

CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = os.getenv("OAUTH_REDIRECT_URI")

AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"


# ✅ Cache OAuth component instance so Streamlit doesn’t re-create it
@st.cache_resource
def get_oauth_component():
    if not CLIENT_ID or not CLIENT_SECRET or not REDIRECT_URI:
        st.error("Google OAuth environment variables missing.")
        return None

    return OAuth2Component(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        authorize_endpoint=AUTHORIZE_URL,
        token_endpoint=TOKEN_URL,
    )


def decode_id_token(token: dict) -> dict:
    """Decodes the JWT ID token to extract user info."""
    try:
        id_token = token.get("id_token")
        if not id_token:
            return {}

        # JWT format: header.payload.signature
        parts = id_token.split(".")
        if len(parts) < 2:
            return {}

        payload = parts[1]

        # Add padding if needed
        payload += "=" * (-len(payload) % 4)

        decoded_payload = base64.urlsafe_b64decode(payload)
        return json.loads(decoded_payload)

    except Exception as e:
        st.error(f"Error decoding token: {e}")
        return {}


def google_oauth_login() -> dict | None:
    """Handles Google OAuth login and returns user info."""
    
    oauth_component = get_oauth_component()
    if oauth_component is None:
        return None

    # ✅ If user not logged in yet → Show login button
    if "token" not in st.session_state:
        result = oauth_component.authorize_button(
            name="Login with Google",
            icon="https://www.google.com/favicon.ico",
            redirect_uri=REDIRECT_URI,
            scope="openid email profile",
            key="google_login",
            use_container_width=True,
        )

        # ✅ If Google responded with token
        if result and "token" in result:
            st.session_state["token"] = result["token"]
            st.rerun()

        return None

    # ✅ User is logged in — get token
    token = st.session_state["token"]

    # ✅ Decode user info only once
    if "user_info" not in st.session_state:
        user_info = decode_id_token(token)
        if user_info:
            st.session_state["user_info"] = user_info

    # ✅ Logout button (sidebar)
    if st.sidebar.button("Logout"):
        for key in ["token", "user_info"]:
            st.session_state.pop(key, None)
        st.rerun()

    return st.session_state.get("user_info")
