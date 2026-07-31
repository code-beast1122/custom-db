# BitEngine - Custom Key-Value Database Engine

A lightweight, high-performance embedded key-value database engine written in Python with both CLI and TCP server/client support. Built on the **Bitcask** log-structured storage model with CRC32 checksums, thread-safe operations, and multi-database support.

## Features

- **Log-Structured Storage** - Append-only write model for high write throughput
- **CRC32 Checksums** - Data integrity verification on every read
- **Thread-Safe** - RLock-based concurrency control with OS-level file locking
- **Multi-Database Support** - Switch between databases at runtime
- **TCP Server/Client** - Network-accessible database with authentication
- **CLI Interface** - Interactive REPL for local database operations
- **Log Compaction** - Reclaim disk space by removing stale entries
- **Cross-Platform** - Works on Windows, Linux, and macOS

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        BitEngine                             │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   CLI       │  │   TCP       │  │   Python API        │  │
│  │   (cli.py)  │  │   Server    │  │   (engine.py)       │  │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘  │
│         │                │                     │             │
│         └────────────────┼─────────────────────┘             │
│                          ▼                                   │
│              ┌───────────────────────┐                       │
│              │    BitEngine Core     │                       │
│              │  (engine.BitEngine)   │                       │
│              └───────────┬───────────┘                       │
│                          │                                   │
│              ┌───────────▼───────────┐                       │
│              │   Storage Layer       │                       │
│              │  (file_lock + CRC32)  │                       │
│              └───────────────────────┘                       │
└─────────────────────────────────────────────────────────────┘
```

## Project Structure

```
custom_db/
├── engine.py          # Core database engine (BitEngine class)
├── cli.py             # Interactive command-line interface
├── server.py          # Async TCP server with multi-db support
├── client.py          # TCP client for remote connections
├── file_lock.py       # Cross-platform file locking (Windows/Linux)
├── test_db.py         # Multi-threaded stress test
├── BitEngineClient.spec  # PyInstaller spec for client executable
├── BitEngineServer.spec  # PyInstaller spec for server executable
└── build/             # PyInstaller build artifacts
```

## Quick Start

### 1. Local CLI Usage

```bash
python cli.py
```

This opens an interactive REPL connected to `data.db`:

```
===================================================
   Bitcask Custom Database Engine CLI (REPL Mode)
   Connected to: data.db | Active Keys: 0
   Type 'HELP' for available commands.
===================================================

custom_db> SET username "john_doe"
OK (Set 'username')

custom_db> GET username
"john_doe"

custom_db> KEYS
1) "username"

custom_db> HELP
```

### 2. TCP Server/Client Mode

**Start the server:**
```bash
python server.py
```

Output:
```
==================================================
 BitEngine TCP Server Running!
 Welcome to BitEngine
 Local Access      : 127.0.0.1:6379
 Network Access    : 192.xxx.x.xxx:6379
 Default Database  : data.db
 Authentication    : ENABLED
 Press Ctrl+C to stop the server
==================================================
```

**Connect with client:**
```bash
# Local connection
python client.py

# Remote connection (specify server IP)
python client.py 192.xxx.x.xxx
```

**Client session:**
```
Connected to BitEngine DB Server at 127.0.0.1:6379
Type commands (e.g., AUTH <password>, SET k v, GET k, KEYS, DEL k). Type 'exit' to quit.

127.0.0.1:6379> AUTH 123
OK (Authenticated)

127.0.0.1:6379> SET user:1001 "Alice"
OK

127.0.0.1:6379> GET user:1001
VALUE: Alice

127.0.0.1:6379> KEYS
user:1001

127.0.0.1:6379> USE sessions
OK (Switched to database 'sessions')

127.0.0.1:6379> SET session:abc "active"
OK
```

### 3. Python API Usage

```python
from engine import BitEngine

# Create/open database
db = BitEngine("my_database.db")

# Basic operations
db.set("key", "value")
value = db.get("key")        # Returns "value" or None
db.delete("key")             # Returns True/False

# List all keys
keys = db.list_keys()

# Maintenance
db.compact()                 # Reclaim disk space
db.clear()                   # Wipe all data

# Cleanup
db.close()
```

## Command Reference

### CLI Commands (`cli.py`)

| Command | Description |
|---------|-------------|
| `SET <key> <value>` | Store a key-value pair (use quotes for multi-word values) |
| `GET <key>` | Retrieve a value by key |
| `DELETE <key>` | Delete a key-value pair |
| `KEYS` | List all active keys in RAM |
| `COMPACT` | Run log compaction to reclaim disk space |
| `CLEAR` | Completely wipe all data in the database |
| `HELP` | Show available commands |
| `EXIT` / `QUIT` | Close the CLI |

### Server Commands (`server.py`)

| Command | Description |
|---------|-------------|
| `AUTH <password>` | Authenticate session (default password: `123`) |
| `USE` / `SELECT <dbname>` | Switch active database (creates `<dbname>.db` if missing) |
| `SET <key> <value>` | Store a key-value pair in active database |
| `GET <key>` | Retrieve a value by key from active database |
| `DELETE` / `DEL <key>` | Delete a key-value pair from active database |
| `KEYS` | List all active keys in RAM for active database |
| `COMPACT` | Run log compaction on active database file |
| `CLEAR` | Completely wipe all data in active database |
| `PING` | Test connection (returns `PONG`) |
| `HELP` | Show this menu |
| `EXIT` / `QUIT` | Close connection |

## Configuration

### Server Configuration (`server.py`)

```python
HOST = "0.0.0.0"       # Listen on all network interfaces
PORT = 6379            # Standard custom DB port
AUTH_PASSWORD = "123"  # Set to None or "" to disable auth
DEFAULT_DB_NAME = "data"  # Default database name
```

### Building Executables

The project includes PyInstaller spec files for creating standalone executables:

```bash
# Build client executable
pyinstaller BitEngineClient.spec

# Build server executable
pyinstaller BitEngineServer.spec
```

Executables will be in `dist/BitEngineClient.exe` and `dist/BitEngineServer.exe`.

## Storage Format

Each record in the database file follows this binary format:

```
┌──────────────┬────────────┬──────────┬──────────┬──────────┬──────────┐
│ CRC32 (4B)   │ Timestamp  │ Key Len  │ Val Len  │ Key      │ Value    │
│ (uint32)     │ (double)   │ (uint32) │ (uint32) │ (bytes)  │ (bytes)  │
└──────────────┴────────────┴──────────┴──────────┴──────────┴──────────┘
     4 bytes       8 bytes      4 bytes    4 bytes    N bytes    M bytes
```

- **CRC32**: Checksum of `key + value` for corruption detection
- **Timestamp**: Unix epoch time (float) for record ordering
- **Key/Val Len**: Length prefixes for variable-length strings
- **TOMBSTONE**: Special value `__DB_TOMBSTONE__` marks deleted keys

## Concurrency & Safety

- **Thread Safety**: `threading.RLock` protects all in-memory operations
- **File Locking**: OS-level locks (`msvcrt` on Windows, `fcntl` on Unix) prevent concurrent file corruption
- **Atomic Writes**: Records written in single `write()` + `flush()` operation
- **Crash Recovery**: Index rebuilt from log on startup with CRC32 validation

## Testing

Run the multi-threaded stress test:

```bash
python test_db.py
```

Expected output:
```
--- Starting Multi-Threaded Stress Test ---
[SUCCESS] 10 threads completed 1,000 concurrent operations in 0.45s!
Total active keys in index: 1000
```

## Requirements

- Python 3.8+
- Standard library only (no external dependencies)


## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `python test_db.py`
5. Submit a pull request

---

**BitEngine** - Simple, fast, reliable key-value storage.