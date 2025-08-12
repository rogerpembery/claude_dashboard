import json
import os
from datetime import datetime

DEFAULT_DATA = {
    "projects": [],
    "snippets": [
        {"id": 1, "title": "Virtual Environment", "code": "python -m venv venv\nsource venv/bin/activate", "tags": ["venv"], "created": datetime.now().isoformat()},
        {"id": 2, "title": "Quick DataFrame", "code": "import pandas as pd\ndf.info()", "tags": ["pandas"], "created": datetime.now().isoformat()}
    ],
    "sessions": []
}

def load_data(data_file):
    if os.path.exists(data_file):
        try:
            with open(data_file, 'r') as f:
                data = json.load(f)
                for key in DEFAULT_DATA:
                    if key not in data:
                        data[key] = DEFAULT_DATA[key]
                return data
        except:
            pass
    return DEFAULT_DATA.copy()

def save_data(data, data_file):
    try:
        with open(data_file, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except:
        return False