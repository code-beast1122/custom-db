import os
import struct
import time
import zlib
import threading
from typing import Optional
from .file_lock import os_file_lock

HEADER_FORMAT = ">IdII"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)
TOMBSTONE = "__DB_TOMBSTONE__"

class BitEngine:
    def __init__(self, db_filepath: str = "data.db", fsync_policy: str = "everysec"):
        self.db_filepath = db_filepath
        self.fsync_policy = fsync_policy
        self.last_sync_time = time.time()
        self.keydir = {}
        self.lock = threading.RLock()
        with self.lock:
            if not os.path.exists(self.db_filepath):
                open(self.db_filepath, "wb").close()
            self.file = open(self.db_filepath, "a+b")
            with os_file_lock(self.file):
                self._build_index()

    def _sync_disk(self, force: bool = False):
        """Flushes Python internal buffer and forces OS write based on policy."""
        self.file.flush()
        
        if self.fsync_policy == "always" or force:
            os.fsync(self.file.fileno())
            self.last_sync_time = time.time()
            
        elif self.fsync_policy == "everysec":
            current_time = time.time()
            if current_time - self.last_sync_time >= 1.0:
                os.fsync(self.file.fileno())
                self.last_sync_time = current_time
    
    def _build_index(self):
        with self.lock:
            self.keydir.clear()
            self.file.seek(0, os.SEEK_SET)
            offset = 0
            while True:
                header_bytes = self.file.read(HEADER_SIZE)
                if not header_bytes or len(header_bytes) < HEADER_SIZE:
                    break
                crc32_stored, timestamp, key_len, val_len = struct.unpack(HEADER_FORMAT, header_bytes)
                key_bytes = self.file.read(key_len)
                val_bytes = self.file.read(val_len)

                payload = key_bytes + val_bytes
                crc32_calculated = zlib.crc32(payload) & 0xffffffff

                if crc32_stored != crc32_calculated:
                    print(f"[Warning] Corrupted record deteced at byte offset {offset}. Stopping index scan.")
                    break

                record_size = HEADER_SIZE + key_len + val_len
                key = key_bytes.decode('utf-8')
                val = val_bytes.decode('utf-8')

                if val == TOMBSTONE:
                    if key in self.keydir:
                        del self.keydir[key]
                else:
                    self.keydir[key] = (offset, record_size)
                offset += record_size

            print(f"[Engine] Index built. Loaded {len(self.keydir)} key(s) into memory.")

    def list_keys(self) -> list[str]:
        with self.lock:
            return list(self.keydir.keys())

    def delete(self, key: str) -> bool:
        with self.lock:
            with os_file_lock(self.file):
                if key not in self.keydir:
                    return False
                key_bytes = key.encode('utf-8')
                val_bytes = TOMBSTONE.encode('utf-8')
                timestamp = time.time()
                key_len, val_len = len(key_bytes), len(val_bytes)
                
                payload = key_bytes + val_bytes
                crc32_val = zlib.crc32(payload) & 0xffffffff
                header = struct.pack(HEADER_FORMAT, crc32_val, timestamp, key_len, val_len)
                record = header + payload
                
                # Write tombstone record to disk
                self.file.seek(0, os.SEEK_END)
                self.file.write(record)

                self._sync_disk()
                
                # Remove key from RAM index
                del self.keydir[key]
                return True
    
    def set(self, key: str, value: str):
        key_bytes = key.encode('utf-8')
        val_bytes = value.encode('utf-8')
        timestamp = time.time()
        key_len = len(key_bytes)
        val_len = len(val_bytes)

        payload = key_bytes + val_bytes
        crc32_val = zlib.crc32(payload) & 0xffffffff

        header = struct.pack(HEADER_FORMAT, crc32_val, timestamp, key_len, val_len)
        record = header + payload
        record_size = len(record)
        with self.lock:
            with os_file_lock(self.file):
                self.file.seek(0, os.SEEK_END)
                offset = self.file.tell()
                self.file.write(record)
                self._sync_disk()
                self.keydir[key] = (offset, record_size)

    def get(self, key: str) -> Optional[str]:
        with self.lock:
            with os_file_lock(self.file):
                if key not in self.keydir:
                    return None
                offset, record_size = self.keydir[key]
                self.file.seek(offset, os.SEEK_SET)
                header_bytes = self.file.read(HEADER_SIZE)
                crc32_stored, timestamp, key_len, val_len = struct.unpack(HEADER_FORMAT, header_bytes)

                self.file.seek(offset + HEADER_SIZE, os.SEEK_SET)
                payload = self.file.read(key_len + val_len)

                crc32_calculated = zlib.crc32(payload) & 0xffffffff
                if crc32_stored != crc32_calculated:
                    raise IOError(f"Data corruption detected on key '{key}' at disk offset {offset}!")
                
                val_bytes = payload[key_len:]
                return val_bytes.decode('utf-8')

    def compact(self):
        compact_filepath = self.db_filepath + ".compact"
        new_keydir = {}
        
        with self.lock:
            # 1. Read live records and write to compact file under OS Lock
            with os_file_lock(self.file):
                with open(compact_filepath, "wb") as compact_file:
                    new_offset = 0
                    for key, (old_offset, record_size) in list(self.keydir.items()):
                        self.file.seek(old_offset, os.SEEK_SET)
                        record_data = self.file.read(record_size)
                        
                        compact_file.write(record_data)
                        compact_file.flush()
                        
                        new_keydir[key] = (new_offset, record_size)
                        new_offset += record_size

            self.file.close()
            os.replace(compact_filepath, self.db_filepath)
            self.file = open(self.db_filepath, "a+b")
            self.keydir = new_keydir
            
            print(f"[Engine] Compaction completed. Database file cleaned.")

    def clear(self):
        with self.lock:
            with os_file_lock(self.file):
                # Safely wipe contents on disk without closing file stream
                self.file.seek(0, os.SEEK_SET)
                self.file.truncate(0)
                self._sync_disk(force=True)
                self.keydir.clear()
                
                print(f"[Engine] Database '{self.db_filepath}' completely cleared.")

    def close(self):
        with self.lock:
            if not self.file.closed:
                self._sync_disk(force=True)
                self.file.close()
