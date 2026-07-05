"""
Authentication screens: Login, Register, Forgot Password.
"""
import streamlit as st

from auth.authentication import register_user, authenticate_user, reset_password


def render_auth_page():
    st.markdown(
        """
        <div style="text-align:center; margin-top: 30px;">
            <div style="font-size:42px;">🎧</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="auth-wrapper">', unsafe_allow_html=True)
    st.markdown(
        '<div class="auth-logo"><span class="gradient-text">PDF to Audio AI</span></div>',
        unsafe_allow_html=True,
    )

    view = st.session_state.get("auth_view", "login")

    if view == "login":
        st.markdown('<div class="auth-subtitle">Welcome back. Log in to continue listening.</div>', unsafe_allow_html=True)
        _render_login()
    elif view == "register":
        st.markdown('<div class="auth-subtitle">Create your account to get started.</div>', unsafe_allow_html=True)
        _render_register()
    else:
        st.markdown('<div class="auth-subtitle">Reset your password.</div>', unsafe_allow_html=True)
        _render_forgot_password()

    st.markdown("</div>", unsafe_allow_html=True)


def _render_login():
    with st.form("login_form", clear_on_submit=False):
        email = st.text_input("Email", placeholder="you@example.com")
        password = st.text_input("Password", type="password", placeholder="••••••••")
        submitted = st.form_submit_button("Log In", use_container_width=True)

    if submitted:
        user, message = authenticate_user(email, password)
        if user:
            st.session_state["logged_in"] = True
            st.session_state["user_id"] = user.id
            st.session_state["user_name"] = user.full_name
            st.session_state["user_email"] = user.email
            st.session_state["current_page"] = "Dashboard"
            st.success(message)
            st.rerun()
        else:
            st.error(message)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Create an account", use_container_width=True):
            st.session_state["auth_view"] = "register"
            st.rerun()
    with col2:
        if st.button("Forgot password?", use_container_width=True):
            st.session_state["auth_view"] = "forgot_password"
            st.rerun()


def _render_register():
    with st.form("register_form"):
        full_name = st.text_input("Full Name", placeholder="Faizol Kolapo")
        email = st.text_input("Email", placeholder="you@example.com")
        password = st.text_input("Password", type="password", placeholder="At least 6 characters")
        confirm_password = st.text_input("Confirm Password", type="password", placeholder="Re-enter password")
        submitted = st.form_submit_button("Create Account", use_container_width=True)

    if submitted:
        if password != confirm_password:
            st.error("Passwords do not match.")
        else:
            success, message = register_user(full_name, email, password)
            if success:
                st.success(message)
                st.session_state["auth_view"] = "login"
                st.rerun()
            else:
                st.error(message)

    if st.button("Already have an account? Log in", use_container_width=True):
        st.session_state["auth_view"] = "login"
        st.rerun()


def _render_forgot_password():
    with st.form("forgot_password_form"):
        email = st.text_input("Account Email", placeholder="you@example.com")
        new_password = st.text_input("New Password", type="password", placeholder="At least 6 characters")
        confirm_password = st.text_input("Confirm New Password", type="password")
        submitted = st.form_submit_button("Reset Password", use_container_width=True)

    if submitted:
        if new_password != confirm_password:
            st.error("Passwords do not match.")
        else:
            success, message = reset_password(email, new_password)
            if success:
                st.success(message)
                st.session_state["auth_view"] = "login"
                st.rerun()
            else:
                st.error(message)

    if st.button("Back to login", use_container_width=True):
        st.session_state["auth_view"] = "login"
        st.rerun()
