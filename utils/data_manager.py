"""
Data management utilities for loading and saving dashboard data.
"""
import json
import os
from datetime import datetime

from utils.time_utils import debug_log


# Sample data structure
DEFAULT_DATA = {
    "projects": [],
    "snippets": [
        {
            "id": 1,
            "title": "Virtual Environment Setup",
            "code": "# Create and activate venv\npython -m venv venv\nsource venv/bin/activate  # macOS/Linux\n# pip install -r requirements.txt",
            "tags": ["venv", "setup"],
            "created": datetime.now().isoformat()
        },
        {
            "id": 2,
            "title": "Quick DataFrame Info",
            "code": "import pandas as pd\n\n# Quick data overview\ndf.info()\nprint(f\"Shape: {df.shape}\")\nprint(f\"Nulls: {df.isnull().sum().sum()}\")",
            "tags": ["pandas", "data-analysis"],
            "created": datetime.now().isoformat()
        }
    ],
    "sessions": []
}


def load_data(data_file):
    """
    Load dashboard data from file.
    
    Args:
        data_file (str): Path to the data file
        
    Returns:
        dict: Loaded data or default data structure
    """
    debug_log("Loading data from file...")
    if os.path.exists(data_file):
        try:
            with open(data_file, 'r') as f:
                data = json.load(f)
                # Ensure all required keys exist
                for key in DEFAULT_DATA:
                    if key not in data:
                        data[key] = DEFAULT_DATA[key]
                debug_log(f"✓ Data loaded from {data_file}")
                return data
        except Exception as e:
            debug_log(f"Error loading data file: {e}")
            return DEFAULT_DATA.copy()
    debug_log("No data file found, using defaults")
    return DEFAULT_DATA.copy()


def save_data(data, data_file):
    """
    Save dashboard data to file.
    
    Args:
        data (dict): Data to save
        data_file (str): Path to the data file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with open(data_file, 'w') as f:
            json.dump(data, f, indent=2)
        debug_log(f"✓ Data saved to {data_file}")
        return True
    except Exception as e:
        debug_log(f"Error saving data: {e}")
        return False