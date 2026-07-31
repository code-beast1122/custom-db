import sys
import contextlib

if sys.platform == 'win32':
    import msvcrt

    @contextlib.contextmanager
    def os_file_lock(file_handle):
        pos = file_handle.tell()
        file_handle.seek(0)

        msvcrt.locking(file_handle.fileno(), msvcrt.LK_LOCK, 1)
        file_handle.seek(pos)
        try:
            yield
        finally:
            pos = file_handle.tell()
            file_handle.seek(0)
            msvcrt.locking(file_handle.fileno(), msvcrt.LK_UNLCK, 1)
            file_handle.seek(pos)
else:
    import fcntl

    @contextlib.contextmanager
    def os_file_lock(file_handle):
        
        fcntl.flock(file_handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(file_handle.fileno(), fcntl.LOCK_UN)