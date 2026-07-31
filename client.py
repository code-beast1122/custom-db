import socket
import sys

def get_local_ip() -> str:
    """Gets local LAN IP so client can display or test network IP."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

def run_client(host=None, port=6379):
    # Default to local LAN IP or loopback
    if host is None:
        host = "127.0.0.1"

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        print(f"Connected to BitEngine DB Server at {host}:{port}")
        print("Type commands (e.g., AUTH <password>, SET k v, GET k, KEYS, DEL k). Type 'exit' to quit.\n")
        
        while True:
            cmd = input(f"{host}:{port}> ").strip()
            if not cmd:
                continue
                
            # Send command over TCP socket
            s.sendall(f"{cmd}\n".encode('utf-8'))
            
            # Receive response from server
            response = s.recv(4096).decode('utf-8').strip()
            print(response)

            # Clean exit if server sends BYE or client typed exit
            if cmd.lower() in ("exit", "quit") or response == "BYE":
                break
            
    except ConnectionRefusedError:
        print(f"[Error] Could not connect to server at {host}:{port}. Is server.py running?")
    except Exception as e:
        print(f"[Error] Network error: {e}")
    finally:
        s.close()

if __name__ == "__main__":
    # If an IP address was passed in CLI (e.g., py client.py 192.168.9.36)
    if len(sys.argv) > 1:
        target_host = sys.argv[1]
    else:
        # Default to loopback if no argument is provided
        user_input = input("Enter Server IP Address (Press Enter for 127.0.0.1): ").strip()
        target_host = "127.0.0.1"
        
    run_client(target_host)