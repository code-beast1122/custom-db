import socket
import sys

def run_client(host=None, port=6379):
    if host is None or not host.strip():
        host = "127.0.0.1"

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        print(f"Connected to BitEngine DB Server at {host}:{port}")
        print("Type commands (e.g., AUTH <password>, SET k v, GET k, KEYS, DEL k). Type 'exit' to quit.\n")
        
        while True:
            cmd = input(f"bit-engine ({host})> ").strip()
            if not cmd:
                continue
                
            s.sendall(f"{cmd}\n".encode('utf-8'))
            
            response = s.recv(4096).decode('utf-8').strip()
            print(response)

            if cmd.lower() in ("exit", "quit") or response == "BYE":
                break
            
    except ConnectionRefusedError:
        print(f"[Error] Could not connect to server at {host}:{port}. Is server.py running?")
    except Exception as e:
        print(f"[Error] Network error: {e}")
    finally:
        s.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_host = sys.argv[1]
    else:
        user_input = input("Enter Server IP Address (Press Enter for 127.0.0.1): ").strip()
        target_host = user_input if user_input else "127.0.0.1"
        
    run_client(target_host)