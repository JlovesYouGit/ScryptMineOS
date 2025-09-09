import sys
import os

# Add the current directory to the path
sys.path.insert(0, os.path.abspath('.'))

# Set the required environment variable for testing
os.environ['PAYOUT_ADDR'] = 'ltc1qpptg85asckrjy9ygygh2tfgxqwzn6672zmzq99'

try:
    from src.mining_os.__main__ import main
    print("Starting Mining OS server...")
    main()
except Exception as e:
    print(f"Error starting server: {e}")
    import traceback
    traceback.print_exc()