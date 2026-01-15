import socket
import sys
import threading
import time

# --- CONFIGURATION ---
MATCHMAKER_IP = "35.209.155.240"
MATCHMAKER_PORT = 10000
LOCAL_PORT = 50005  # We bind to a specific port to help the NAT stay stable


def listen_loop(sock):
    """Background thread to receive messages."""
    while True:
        try:
            data, addr = sock.recvfrom(2048)
            msg = data.decode('utf-8')
            if msg == "__ping__":  # Ignore internal keep-alives
                continue
            print(f"\n[Peer {addr[0]}]: {msg}")
            print("You: ", end="", flush=True)
        except:
            break


def start_p2p():
    # 1. Setup UDP Socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('0.0.0.0', LOCAL_PORT))

    # 2. Register with Matchmaker
    print(f"Connecting to Matchmaker at {MATCHMAKER_IP}...")
    sock.sendto(b"HELLO", (MATCHMAKER_IP, MATCHMAKER_PORT))

    # 3. Wait for Peer Info
    print("Waiting for a peer to join...")
    data, _ = sock.recvfrom(1024)
    peer_ip, peer_port = data.decode('utf-8').split(":")
    peer_addr = (peer_ip, int(peer_port))
    print(f"Match found! Peer is at {peer_addr}")

    # 4. The "Hole Punch" Phase (Retry until connected)
    print("Punching hole... (this may take a few seconds)")
    connected = False

    # Start listening in background
    threading.Thread(target=listen_loop, args=(sock,), daemon=True).start()

    # Send a stream of pings to open the NAT door
    for _ in range(10):
        sock.sendto(b"__ping__", peer_addr)
        time.sleep(0.5)

    # 5. Main Chat Loop
    print("\n--- CHAT START (Type 'exit' to quit) ---")
    while True:
        msg = input("You: ")
        if msg.lower() == 'exit':
            break
        sock.sendto(msg.encode('utf-8'), peer_addr)


if __name__ == "__main__":
    try:
        start_p2p()
    except KeyboardInterrupt:
        print("\nExiting...")