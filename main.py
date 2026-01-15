import socket
import threading
import sys

PORT = 8080

def receive_loop(conn):
    """This runs in the background to catch incoming text."""
    while True:
        try:
            data = conn.recv(1024)
            if not data:
                print("\n[System] Peer disconnected.")
                break
            # \r clears the line so the incoming message doesn't
            # get mixed up with your 'You: ' prompt
            print(f"\r[Peer]: {data.decode('utf-8').strip()}")
            print("You: ", end="", flush=True)
        except:
            break
    print("\n[System] Connection closed. Press Enter to exit.")

def chat_session(conn):
    """Once connected, this handles the two-way flow."""
    # Start the receiver in the background
    threading.Thread(target=receive_loop, args=(conn,), daemon=True).start()

    # Main thread stays here for sending
    print("Chat active! Type and hit Enter. (Type 'exit' to quit)")
    while True:
        msg = input("You: ")
        if msg.lower() == 'exit':
            break
        try:
            conn.send((msg + "\n").encode('utf-8'))
        except:
            print("[System] Send failed. Peer might be offline.")
            break
    conn.close()

def main():
    if len(sys.argv) == 1:
        # iPhone / Wait-Mode
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('0.0.0.0', PORT))
        server.listen(1)
        print(f"Waiting for connection on port {PORT}...")
        conn, addr = server.accept()
        print(f"Connected to {addr}")
        chat_session(conn)
    else:
        # Mac / Call-Mode
        target_ip = sys.argv[1]
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            client.connect((target_ip, PORT))
            print(f"Connected to {target_ip}")
            chat_session(client)
        except Exception as e:
            print(f"Connection error: {e}")

if __name__ == "__main__":
    main()