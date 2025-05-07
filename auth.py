
import streamlit as st
import json

import os
USER_DB = os.path.join(os.path.dirname(__file__), "users.json")

def login_form():
    st.markdown("<div class='login-card'>", unsafe_allow_html=True)
    st.markdown("<div class='login-header'>🔒 Login to WorkSight</div>", unsafe_allow_html=True)

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        with open(USER_DB) as f:
            users = json.load(f)
        if email in users and users[email] == password:
            st.session_state.logged_in = True
            st.session_state.user_email = email
            st.rerun()
        else:
            st.error("Invalid email or password.")
    st.markdown("</div>", unsafe_allow_html=True)

def is_logged_in():
    return st.session_state.get("logged_in", False)

def logout():
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.rerun()
