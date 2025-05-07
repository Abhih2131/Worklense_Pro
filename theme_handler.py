# theme_handler.py
import streamlit as st
import plotly.io as pio

# Centralized Theme Settings
THEME_OPTIONS = ["plotly_white", "simple_white", "presentation", "seaborn", "ggplot2"]

def selected_theme():
    theme = st.sidebar.selectbox("🎨 Select Chart Theme", THEME_OPTIONS)
    pio.templates.default = theme
    return theme