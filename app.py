# app.py
import os
import sys
import streamlit as st

# Add the project's root directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the chat app
from src.utils.chat import run_chat_app


if __name__ == "__main__":
    run_chat_app()