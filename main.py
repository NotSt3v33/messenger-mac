import socket
import threading
import sys

def receive_messages(sock):
    while True:
        try:
            data = sock.recv(1024)
            if not data:
                break
            print(f"\n[Friend]: {data.decode('utf-8')}")
            print("You: ", end="", flush=True)
        except:
            break

def start_chat():
    # 1. Setup Connection
    is_server = len(sys.argv) == 1
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    if is_server:
        # iPhone Mode: Wait for connection
        sock.bind(('0.0.0.0', 8080))
        sock.listen(1)
        print("Waiting for friend to connect...")
        conn, addr = sock.accept()
        print(f"Connected to {addr}")
    else:
        # Mac Mode: Connect to iPhone
        target_ip = sys.argv[1]
        sock.connect((target_ip, 8080))
        conn = sock

    # 2. Start Background Thread to Listen
    threading.Thread(target=receive_messages, args=(conn,), daemon=True).start()

    # 3. Main Loop to Send
    print("Type your message and hit Enter (Ctrl+C to quit)")
    while True:
        msg = input("You: ")
        conn.send(msg.encode('utf-8'))

if __name__ == "__main__":
    try:
        start_chat()
    except KeyboardInterrupt:
        print("\nChat ended.")