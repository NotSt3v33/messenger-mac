import socket
import threading
import sys

# Change this to any port you like
PORT = 8080


def listen_for_messages(conn):
    """Handles receiving data from a connected peer."""
    while True:
        try:
            data = conn.recv(1024)
            if not data:
                print("\n[System] Peer disconnected.")
                break
            print(f"\n[Peer]: {data.decode('utf-8')}")
            print("You: ", end="", flush=True)
        except ConnectionResetError:
            break
    conn.close()


def start_server():
    """Background thread that waits for someone to call us."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Allow restarting the script immediately without 'Address already in use' error
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', PORT))
    server.listen(1)

    conn, addr = server.accept()
    print(f"\n[System] Connected by {addr}")
    listen_for_messages(conn)


def start_client(peer_ip):
    """Connects to a specific friend's IP."""
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect((peer_ip, PORT))
        print(f"[System] Connected to {peer_ip}")

        # Start a thread to listen to what the friend says back
        threading.Thread(target=listen_for_messages, args=(client,), daemon=True).start()

        # Main loop for sending
        while True:
            msg = input("You: ")
            if msg.lower() == 'exit': break
            client.send(msg.encode('utf-8'))
    except Exception as e:
        print(f"[Error] Could not connect: {e}")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print(f"Starting in Wait-Mode (Listening on port {PORT})...")
        start_server()
    else:
        # If you provide an IP, you are the one "calling"
        target_ip = sys.argv[1]
        start_client(target_ip)