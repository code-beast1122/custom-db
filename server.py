import asyncio
import os
import shlex
import socket
from engine import BitEngine

HOST = "0.0.0.0"       # Listen on all network interfaces
PORT = 6379            # Standard custom DB port
AUTH_PASSWORD = "123"  # Set to None or "" to disable auth requirements
DEFAULT_DB_NAME = "data"             # Default database name (resolves to data.db)

def print_help():
    return """
Available Commands:
  AUTH <password>      - Authenticate session with server password
  USE / SELECT <dbname>- Switch active database (creates <dbname>.db if missing)
  SET <key> <value>    - Store a key-value pair in active database
  GET <key>            - Retrieve a value by key from active database
  DELETE <key>         - Delete a key-value pair from active database
  KEYS                 - List all active keys in RAM for active database
  COMPACT              - Run log compaction on active database file
  CLEAR                - Completely wipe all data in active database
  PING                 - Test connection
  HELP                 - Show this menu
  EXIT / QUIT          - Close connection
"""

def get_local_ip() -> str:
    """Auto-detects the computer's active LAN/Wi-Fi IP address."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

class KVServer:
    def __init__(self, password: str | None = None):
        self.password = password
        # Cache active database instances: {"data": BitEngine("data.db"), ...}
        self.databases: dict[str, BitEngine] = {}

    def get_or_create_db(self, db_name: str) -> BitEngine:
        """Retrieves an existing BitEngine instance or opens a new one."""
        # Sanitize db_name to avoid path traversal issues
        clean_name = os.path.basename(db_name).replace(".db", "")
        if clean_name not in self.databases:
            filepath = f"{clean_name}.db"
            print(f"[Server] Initializing database engine for '{filepath}'")
            self.databases[clean_name] = BitEngine(filepath)
        return self.databases[clean_name]

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handles a single client TCP connection with per-client auth & database state."""
        peer_name = writer.get_extra_info('peername')
        print(f"[Server] Client connected from {peer_name}")
        
        # Track session state per client connection
        authenticated = self.password is None or len(self.password) == 0
        current_db_name = DEFAULT_DB_NAME
        current_db = self.get_or_create_db(current_db_name)

        try:
            while True:
                data = await reader.readline()
                if not data:
                    break  # Client disconnected
                
                command_line = data.decode('utf-8').strip()
                if not command_line:
                    continue
                
                try:
                    parts = shlex.split(command_line)
                except ValueError as e:
                    writer.write(f"ERR Syntax error: {e}\n".encode('utf-8'))
                    await writer.drain()
                    continue
                
                cmd = parts[0].upper()
                args = parts[1:]
                
                # 1. Process AUTH command
                if cmd == "AUTH":
                    if not self.password:
                        response = "ERR Client sent AUTH, but no password is set on server"
                    elif len(args) != 1:
                        response = "ERR Usage: AUTH <password>"
                    elif args[0] == self.password:
                        authenticated = True
                        response = "OK (Authenticated)"
                    else:
                        response = "ERR Invalid password"
                
                # 2. Block unauthenticated commands
                elif not authenticated and cmd not in ("PING", "HELP", "EXIT", "QUIT"):
                    response = "ERR Unauthenticated. Please run 'AUTH <password>' first."
                
                # 3. Process USE / SELECT database switching command
                elif cmd in ("USE", "SELECT"):
                    if len(args) != 1:
                        response = "ERR Usage: USE <dbname>"
                    else:
                        new_db_name = os.path.basename(args[0]).replace(".db", "")
                        current_db = self.get_or_create_db(new_db_name)
                        current_db_name = new_db_name
                        response = f"OK (Switched to database '{current_db_name}')"
                
                # 4. Route database commands to client's selected DB engine
                else:
                    response = self.execute_command(current_db, cmd, args)
                
                writer.write(f"{response}\n".encode('utf-8'))
                await writer.drain()
                
        except ConnectionResetError:
            pass
        finally:
            print(f"[Server] Client disconnected: {peer_name}")
            writer.close()
            await writer.wait_closed()

    def execute_command(self, db: BitEngine, cmd: str, args: list) -> str:
        """Executes database commands against the target BitEngine instance."""
        if cmd == "GET":
            if len(args) != 1:
                return "ERR Usage: GET <key>"
            val = db.get(args[0])
            return f"VALUE: {val}" if val is not None else "(nil)"

        elif cmd == "SET":
            if len(args) != 2:
                return "ERR Usage: SET <key> <value>"
            db.set(args[0], args[1])
            return "OK"

        elif cmd in ("DEL", "DELETE"):
            if len(args) != 1:
                return "ERR Usage: DEL <key>"
            success = db.delete(args[0])
            return f"OK! deleted {args[0]}" if success else "(nil)"

        elif cmd == "KEYS":
            keys = db.list_keys()
            if not keys:
                return "(empty list)"
            return " ".join(keys)

        elif cmd == "COMPACT":
            db.compact()
            return "OK (Compaction complete)"

        elif cmd == "CLEAR":
            db.clear()
            return "OK (Database cleared)"

        elif cmd == "PING":
            return "PONG"
        
        elif cmd == "HELP":
            return print_help()

        elif cmd in ("EXIT", "QUIT"):
            return "BYE"

        else:
            return f"ERR Unknown command '{cmd}'"
    def close_all(self):
        """Closes all open database engine file handles cleanly."""
        print("[Server] Closing all database file handles...")
        for name, db in self.databases.items():
            try:
                db.close()  # Flushes buffers & releases file locks
                print(f"[Server] Closed database '{name}.db'")
            except Exception as e:
                print(f"[Server] Error closing database '{name}.db': {e}")

async def main():
    server_instance = KVServer(password=AUTH_PASSWORD)
    server = await asyncio.start_server(
        server_instance.handle_client, HOST, PORT
    )
    
    local_ip = get_local_ip()
    
    print(f"==================================================")
    print(f" BitEngine TCP Server Running!\n Welcome to BitEngine")
    print(f" Local Access      : 127.0.0.1:{PORT}")
    print(f" Network Access    : {local_ip}:{PORT}")
    print(f" Default Database  : {DEFAULT_DB_NAME}.db")
    print(f" Authentication    : {'ENABLED' if AUTH_PASSWORD else 'DISABLED'}")
    print(f" Press Ctrl+C to stop the server")
    print(f"==================================================")
    
    try:
        async with server:
            await server.serve_forever()
    finally:
        # This ALWAYS executes when the server stops or crashes
        server_instance.close_all()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[Server] Shutdown signal received.")