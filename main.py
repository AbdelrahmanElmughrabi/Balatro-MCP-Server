import json
import time
from pathlib import Path
import os
import errno  # Import for specific error handling

# The file is at %AppData%/Balatro/mcp-bridge/ (NOT in Mods folder!)
APPDATA = os.getenv('APPDATA')
if not APPDATA:
    print("ERROR: APPDATA environment variable not found!")
    exit(1)

# Correct path - no "Mods" folder in the path
BASE_PATH = Path(APPDATA) / "Balatro" / "mcp-bridge"
JSON_PATH = BASE_PATH / "mcp_gamestate.json"

print("=" * 60)
print("MCP Bridge - Game State Watcher")
print("=" * 60)
print(f"Looking for file at:")
print(f"  {JSON_PATH}")
print(f"\nDirectory exists: {BASE_PATH.exists()}")
print(f"File exists: {JSON_PATH.exists()}")
print("=" * 60)

if JSON_PATH.exists():
    print("\n✓ File found! Starting watcher...\n")
else:
    # Clear the initial 'waiting' message print on the first check
    print("\n⏳ Waiting for first export (press F1 in game)...")

last_modified = 0

while True:
    try:
        if JSON_PATH.exists():
            # Check for directory creation if it doesn't exist, though the game should create it.
            # Added a stat() check inside the try block for better error handling.
            current_modified = JSON_PATH.stat().st_mtime

            if current_modified != last_modified:
                # To prevent potential issues with the game writing the file,
                # we wrap the read operation in a loop and handle transient errors.
                read_attempts = 0
                max_attempts = 5
                data = None

                while read_attempts < max_attempts:
                    try:
                        with open(JSON_PATH, 'r', encoding='utf-8') as f:
                            # Use f.read() and check for empty file before json.loads()
                            content = f.read()
                            if content:
                                data = json.loads(content)
                            else:
                                # File is empty, wait a bit for a full write
                                raise IOError("File is empty or still being written.")
                            break  # Success, break out of read loop
                    except (IOError, json.JSONDecodeError, OSError) as e:
                        # Handle errors like "Permission denied" (EPERM/EACCES)
                        # or incomplete writes (JSONDecodeError or IOError from empty check)
                        read_attempts += 1
                        print(
                            f"\n⚠️ Transient Read/JSON Error (Attempt {read_attempts}/{max_attempts}): {type(e).__name__} - {e}")
                        if read_attempts == max_attempts:
                            raise  # Re-raise if max attempts reached
                        time.sleep(0.1)  # Short wait before retry

                if data:
                    # Update last_modified ONLY after successful read and parse
                    last_modified = current_modified

                    print(f"\n{'=' * 60}")
                    print(f"📊 Updated at: {time.strftime('%H:%M:%S')}")
                    print('=' * 60)
                    print(json.dumps(data, indent=2))
                    print('=' * 60)

                    # Quick summary
                    if 'test_data' in data:
                        td = data['test_data']
                        print(
                            f"\n💰 Cash: ${td.get('cash', 'N/A')} | Round: {td.get('round', 'N/A')} | Ante: {td.get('ante', 'N/A')}")

                        if 'current_hand' in data and data['current_hand']:
                            # Added a check to ensure 'current_hand' is iterable/list
                            if isinstance(data['current_hand'], list):
                                # Minor efficiency: use a generator expression for list comprehension
                                cards = [f"{c['rank'][0]}{c['suit'][0]}" for c in data['current_hand']]
                                print(f"🃏 Hand ({len(cards)}): {' '.join(cards)}")
                            else:
                                print(f"🃏 Hand: Data format error - 'current_hand' is not a list.")

                    print()

        else:
            # Clear the previous line when printing the 'Waiting...' status
            print(f"⏳ Waiting... ({time.strftime('%H:%M:%S')})", end='\r', flush=True)

        time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n\n👋 Stopped watching.")
        break
    except json.JSONDecodeError as e:
        # This block now mostly catches persistent, non-transient JSON errors after retries
        print(f"\n❌ Persistent JSON Parse Error: {e}")
    except OSError as e:
        # Handle errors like file not found after an existence check, or other OS issues.
        # This is primarily for robust error reporting.
        print(f"\n❌ OS Error accessing file (Code {e.errno}): {e}")
    except Exception as e:
        # Catch any other unexpected errors
        print(f"\n❌ Unexpected Error: {e}")
        time.sleep(1)
        