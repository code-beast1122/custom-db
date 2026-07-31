import sys
import shlex
from engine import BitEngine

def print_help():
    print("""
Available Commands:
  SET <key> <value>  - Store a key-value pair (use quotes for multi-word values)
  GET <key>          - Retrieve a value by key
  DELETE <key>       - Delete a key-value pair
  KEYS               - List all active keys in RAM
  COMPACT            - Run log compaction to reclaim disk space
  CLEAR              - Completely wipe all data in the database
  HELP               - Show this menu
  EXIT / QUIT        - Close the CLI
""")

def run_cli():
    db = BitEngine("data.db")
    print("=" * 55)
    print("   Bitcask Custom Database Engine CLI (REPL Mode)")
    print(f"   Connected to: data.db | Active Keys: {len(db.keydir)}")
    print("   Type 'HELP' for available commands.")
    print("=" * 55)

    while True:
        try:
            user_input = input("\ncustom_db> ").strip()
            if not user_input:
                continue

            # Split command using shlex to respect quoted strings like: SET title "Hello World"
            tokens = shlex.split(user_input)
            cmd = tokens[0].upper()
            args = tokens[1:]

            if cmd in ("EXIT", "QUIT"):
                print("Closing database connection. Goodbye!")
                db.close()
                break

            elif cmd == "HELP":
                print_help()

            elif cmd == "KEYS":
                keys = db.list_keys()
                if not keys:
                    print("empty")
                else:
                    for idx, key in enumerate(keys, 1):
                        print(f"{idx}) \"{key}\"")
            elif cmd == "SET":
                if len(args) < 2:
                    print("[Error] Usage: SET <key> <value>")
                    continue
                key = args[0]
                # Join remaining args if not quoted
                value = " ".join(args[1:]) if len(args) > 2 else args[1]
                db.set(key, value)
                print(f"OK (Set '{key}')")

            elif cmd == "GET":
                if len(args) < 1:
                    print("[Error] Usage: GET <key>")
                    continue
                key = args[0]
                value = db.get(key)
                if value is None:
                    print("(nil) - Key not found")
                else:
                    print(f'"{value}"')

            elif cmd == "DELETE":
                if len(args) < 1:
                    print("[Error] Usage: DELETE <key>")
                    continue
                key = args[0]
                success = db.delete(key)
                if success:
                    print(f"OK (Deleted '{key}')")
                else:
                    print("(nil) - Key does not exist")

            elif cmd == "KEYS":
                keys = list(db.keydir.keys())
                if not keys:
                    print("(empty database)")
                else:
                    for idx, k in enumerate(keys, 1):
                        print(f"{idx}) \"{k}\"")

            elif cmd == "COMPACT":
                print("Running log compaction...")
                db.compact()
                print("OK (Database compacted successfully)")

            elif cmd == "CLEAR":
                confirm = input("Are you sure you want to CLEAR all data? (y/N): ").strip().lower()
                if confirm == 'y':
                    db.clear()
                    print("OK (Database cleared)")
                else:
                    print("Cancelled.")

            else:
                print(f"[Error] Unknown command '{cmd}'. Type 'HELP' for available commands.")

        except KeyboardInterrupt:
            print("\nClosing database connection. Goodbye!")
            db.close()
            sys.exit(0)
        except Exception as e:
            print(f"[Error] {e}")

if __name__ == "__main__":
    run_cli()