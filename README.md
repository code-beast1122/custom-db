# BitEngine (`bitengine-db`)

[![PyPI version](https://img.shields.io/pypi/v/bitengine-db.svg?color=orange&v=0.1.6)](https://pypi.org/project/bitengine-db/)
[![Python Version](https://img.shields.io/pypi/pyversions/bitengine-db.svg)](https://pypi.org/project/bitengine-db/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A lightweight, high-performance embedded & network key-value database engine written in pure Python. Built on the **Bitcask** log-structured storage model with CRC32 checksums, OS-level file locking, thread-safe operations, and multi-database TCP server support.

---

## 🚀 Installation

Install directly from PyPI via `pip`:

```bash
pip install bitengine-db
```

> **Zero External Dependencies:** BitEngine uses only the Python standard library.

---

## ⚡ Quick Start

### 1. Embedded Library Usage (Python API)

Use `BitEngine` directly in your Python applications without running any external database server process:

```python
from bitengine import BitEngine

# Open or create an embedded key-value database file
db = BitEngine("my_data.db", fsync_policy="everysec")

# Store key-value pairs
db.set("user:1001", "Alice")
db.set("user:1002", "Bob")

# Retrieve values
name = db.get("user:1001")
print(name)  # Output: "Alice"

# List all active keys in RAM index
print(db.list_keys())  # Output: ['user:1001', 'user:1002']

# Delete a key
db.delete("user:1002")

# Run log compaction to reclaim disk space from stale/deleted entries
db.compact()

# Close the database safely
db.close()
```

---

### 2. Interactive Terminal REPL

Installing `bitengine-db` provides terminal commands out of the box:

```bash
bitengine-cli
```

Output:
```text
===================================================
   Bitcask Custom Database Engine CLI (REPL Mode)
   Connected to: data.db | Active Keys: 0
   Type 'HELP' for available commands.
===================================================

custom_db> SET session_id "xyz_987"
OK (Set 'session_id')

custom_db> GET session_id
"xyz_987"

custom_db> KEYS
1) "session_id"

custom_db> COMPACT
Running log compaction...
OK (Database compacted successfully)
```

---

### 3. TCP Network Server & Client

Start a network-accessible database server supporting multiple client connections:

```bash
bitengine-server
```

Connect remotely using the client tool:

```bash
# Connect to local or remote server
bitengine-client 127.0.0.1
```

Client commands:
```text
bit-engine (127.0.0.1)> AUTH 123
OK (Authenticated)

bit-engine (127.0.0.1)> USE analytics
OK (Switched to database 'analytics')

bit-engine (127.0.0.1)> SET status "active"
OK

bit-engine (127.0.0.1)> GET status
VALUE: active
```

---

## ✨ Core Features

- 🪵 **Bitcask Log-Structured Storage:** Fast append-only write model for high write throughput.
- 🛡️ **CRC32 Data Integrity Verification:** Protects against data corruption on disk by validating checksums on every read.
- 🔒 **OS-Level & Thread-Safe Concurrency:** RLock concurrency control combined with cross-platform OS file locking (`msvcrt` on Windows, `fcntl` on Linux/macOS).
- 🧹 **Automatic Log Compaction:** Reclaims disk space by purging deleted tombstones and overwritten keys.
- ⚡ **Zero Third-Party Dependencies:** Pure Python standard library implementation (`struct`, `zlib`, `threading`, `asyncio`, `socket`).
- 🌐 **Multi-Database TCP Server:** Built-in async server supporting runtime database switching (`USE <dbname>`) and PBKDF2 password authentication.

---

## 📖 Python API Reference

### `BitEngine(db_filepath="data.db", fsync_policy="everysec")`
Initializes and opens the Bitcask database engine.

- **`set(key: str, value: str)`**: Store or overwrite a key-value pair.
- **`get(key: str) -> Optional[str]`**: Retrieve a value by key. Returns `None` if the key does not exist.
- **`delete(key: str) -> bool`**: Mark key as deleted via tombstone. Returns `True` if key was deleted, `False` if key wasn't found.
- **`list_keys() -> List[str]`**: Return a list of all active keys currently in RAM index.
- **`compact()`**: Merge and clean up the database file on disk to remove old/deleted records.
- **`clear()`**: Wipe all records in the database.
- **`close()`**: Flush buffers, force disk write, and safely close file handles.

---

## 📜 License

Distributed under the **MIT License**. See `LICENSE` for details.