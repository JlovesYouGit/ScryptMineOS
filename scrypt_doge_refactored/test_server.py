import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from mining_os.config import Settings
    settings = Settings()
    print("Settings loaded successfully")
    print(f"Host: {settings.host}")
    print(f"Port: {settings.port}")
except Exception as e:
    print(f"Error loading settings: {e}")
    import traceback
    traceback.print_exc()