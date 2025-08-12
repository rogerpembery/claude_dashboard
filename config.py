"""
Configuration module for the dashboard application.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration - CUSTOMIZE THESE FOR YOUR SETUP
PROJECTS_DIR = os.path.expanduser("/Volumes/BaseHDD/python/")
DATA_FILE = os.path.expanduser("~/.vibe_dashboard_data.json")

# Git/GitHub Configuration - LOADED FROM .env FILE
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME", "your_username_here")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "your_token_here")
GIT_EMAIL = os.getenv("GIT_EMAIL", "your_email@example.com")
GIT_NAME = os.getenv("GIT_NAME", "Your Name")