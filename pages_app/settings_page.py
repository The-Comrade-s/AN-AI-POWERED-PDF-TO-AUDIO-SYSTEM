"""
Settings page: theme, default voice/speed, language, notifications,
account details, password change, and account deletion.
"""
import os
import shutil

import streamlit as st

from database.models import get_session, User
from auth.authentication import hash_password, verify_password, validate_password_strength
from audio.tts_engine import list_available_voices, SPEED_OPTIONS
from utils.helpers import logout


def render_settings_page():
    st.markdown("### Settings")

    user_id = st.session_state["user_id"]
    session = get_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            st.error("Could not load account details.")
            return

        tab1, tab2, tab3 = st.tabs(["Preferences", "Account", "Danger Zone"])

        with tab1:
            st.markdown("**Playback & Appearance**")
            voices = list_available_voices()
            voice_names = list(voices.keys())
            current_voice_label = next((k for k, v in voices.items() if v == user.default_voice), voice_names[0])

            theme = st.selectbox("Theme", ["dark", "light"], index=0 if user.theme == "dark" else 1)
            voice_label = st.selectbox("Default Voice", voice_names, index=voice_names.index(current_voice_label))

            speed_index = 2
            try:
                speed_index = SPEED_OPTIONS.index(float(user.default_speed))
            except (ValueError, TypeError):
                pass
            speed = st.selectbox("Default Playback Speed", SPEED_OPTIONS, index=speed_index)

            lang_choices = ["en", "es", "fr", "de"]
            lang_index = lang_choices.index(user.language) if user.language in lang_choices else 0
            language = st.selectbox("Language", lang_choices, index=lang_index)
            notifications = st.checkbox("Enable notifications", value=user.notifications_enabled)

            if st.button("Save Preferences", use_container_width=True):
                user.theme = theme
                user.default_voice = voices[voice_label]
                user.default_speed = speed
                user.language = language
                user.notifications_enabled = notifications
                session.commit()
                st.success("Preferences saved.")

        with tab2:
            st.markdown("**Account Details**")
            st.text_input("Full Name", value=user.full_name, key="settings_name", disabled=True)
            st.text_input("Email", value=user.email, key="settings_email", disabled=True)
            st.caption("Contact support to change your name or email.")

            st.markdown('<div class="soft-divider"></div>', unsafe_allow_html=True)
            st.markdown("**Change Password**")
            with st.form("change_password_form"):
                current_pw = st.text_input("Current Password", type="password")
                new_pw = st.text_input("New Password", type="password")
                confirm_pw = st.text_input("Confirm New Password", type="password")
                submitted = st.form_submit_button("Update Password", use_container_width=True)

            if submitted:
                if not verify_password(current_pw, user.password_hash):
                    st.error("Current password is incorrect.")
                elif new_pw != confirm_pw:
                    st.error("New passwords do not match.")
                else:
                    valid, msg = validate_password_strength(new_pw)
                    if not valid:
                        st.error(msg)
                    else:
                        user.password_hash = hash_password(new_pw)
                        session.commit()
                        st.success("Password updated successfully.")

        with tab3:
            st.markdown("**Delete Account**")
            st.warning("This will permanently delete your account, all uploaded PDFs, generated audio, notes, and history. This cannot be undone.")
            confirm_text = st.text_input("Type DELETE to confirm")
            if st.button("Delete My Account", use_container_width=True):
                if confirm_text.strip() == "DELETE":
                    _delete_account(session, user)
                    st.success("Account deleted.")
                    logout()
                    st.rerun()
                else:
                    st.error("Please type DELETE exactly to confirm.")
    finally:
        session.close()


def _delete_account(session, user):
    user_id = user.id
    upload_dir = os.path.join("uploads", str(user_id))
    audio_dir = os.path.join("generated_audio", str(user_id))
    thumb_dir = os.path.join("assets", "thumbnails", str(user_id))

    for d in [upload_dir, audio_dir, thumb_dir]:
        if os.path.exists(d):
            shutil.rmtree(d, ignore_errors=True)

    session.delete(user)
    session.commit()
