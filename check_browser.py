import subprocess
import sys

# Check for browsers
for cmd in ['chromium', 'chromium-browser', 'google-chrome', 'firefox']:
    result = subprocess.run(['which', cmd], capture_output=True)
    if result.returncode == 0:
        print(f"Found: {cmd} -> {result.stdout.decode().strip()}")

# Check playwright
try:
    import playwright
    print("playwright available")
except ImportError:
    print("playwright not installed")

# Check selenium
try:
    import selenium
    print("selenium available")
except ImportError:
    print("selenium not installed")