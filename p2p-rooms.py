import socket
import threading
import time

# Constants
MATCHMAKER_IP = "35.209.155.240"
MATCHMAKER_PORT = 10000
LOCAL_PORT = 50005

peer_info = {"addr": None}


def listen_loop(sock):
    while True:
        try:
            data, addr = sock.recvfrom(4096)
            # Ignore messages from the matchmaker once we are in P2P mode
            if addr == (MATCHMAKER_IP, MATCHMAKER_PORT):
                continue

            msg = data.decode('utf-8', errors='ignore')
            if msg == "__ping__":
                continue

            print(f"\r[Peer]: {msg}\nYou: ", end="", flush=True)
        except:
            break


def start_p2p():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Allow port reuse in case of quick restarts
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('0.0.0.0', LOCAL_PORT))

    choice = input("Enter Room ID or press Enter for NEW: ").strip()

    # Phase 1: Contact Matchmaker
    command = b"NEW" if not choice else f"JOIN:{choice}".encode()
    sock.sendto(command, (MATCHMAKER_IP, MATCHMAKER_PORT))

    # Phase 2: Wait for Peer Info
    print("Waiting for peer information from server...")
    while peer_info["addr"] is None:
        data, _ = sock.recvfrom(1024)
        msg = data.decode(errors='ignore')

        if msg.startswith("INFO:"):
            print(f"Room created! ID: {msg[5:]}\nWaiting for friend...")
        elif msg.startswith("PEER:"):
            # Format is PEER:IP:PORT
            peer_data = msg[5:]
            parts = peer_data.split(":")
            peer_info["addr"] = (parts[0], int(parts[1]))
            print(f"Peer found at {peer_info['addr']}")
        elif "ERROR" in msg:
            print("Room error: Not found or full.")
            return

    # Start listener thread
    threading.Thread(target=listen_loop, args=(sock,), daemon=True).start()

    # Phase 3: UDP Hole Punching (The "Handshake")
    # We send pings to open the NAT firewall
    print("Establishing P2P connection...")
    for _ in range(5):
        sock.sendto(b"__ping__", peer_info["addr"])
        time.sleep(0.2)

    print("--- SECURE CHANNEL READY (UNENCRYPTED) ---")
    while True:
        try:
            msg = input("You: ")
            if msg.lower() == 'exit':
                break
            if msg.strip():
                sock.sendto(msg.encode('utf-8'), peer_info["addr"])
        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    start_p2p()