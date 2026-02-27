"""
PMW Agents entry point.

Delegates to root main.py when run from agents/.
Run via: python main.py (from pmw-agents root)
"""
import sys
import os

# Ensure repo root is on path when run from agents/
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

if __name__ == "__main__":
    import main as root_main

    print("PMW Agents starting...")
    root_main.run_migrations()
    print("PMW Agents started successfully.")
    root_main.worker_loop()
