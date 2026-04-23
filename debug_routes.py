import sys
import os
sys.path.append(os.getcwd())

from server import app

for route in app.routes:
    print(f"{route.path} {route.name}")
