import os
from dotenv import load_dotenv

load_dotenv()
print(f"IBKR_CLIENT_ID from env: {os.getenv('IBKR_CLIENT_ID')}")
print(f"IBKR_CLIENT_ID int: {int(os.getenv('IBKR_CLIENT_ID', 1))}")
