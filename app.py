#!/usr/bin/env python3
"""
Hugging Face Space entrypoint for AuditGym-v1.
Runs the demo and prints output.
"""

import subprocess
import sys

if __name__ == "__main__":
    print("AuditGym-v1 Hugging Face Space Demo")
    print("Running demo.py...")
    result = subprocess.run([sys.executable, "demo.py"], capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("Errors:", result.stderr)