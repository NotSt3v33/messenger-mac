import socket
import sys
import threading
import time

MATCHMAKER_IP = "35.209.155.240"
MATCHMAKER_PORT = 10000
LOCAL_PORT = 50005

# Shared state to track the peer's actual address
peer_info = {"addr": None}


def listen_loop(sock):
    while True:
        try:
            data, addr = sock.recvfrom(2048)
            # CRITICAL: If we get ANY packet, that is the real port. Update immediately!
            if peer_info["addr"] != addr:
                peer_info["addr"] = addr
                print(f"\n[System] Found real peer port: {addr[1]}")

            msg = data.decode('utf-8', errors='ignore')
            if "__punch__" in msg: continue
            print(f"\r[Peer]: {msg}\nYou: ", end="", flush=True)
        except:
            break


def start_p2p():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('0.0.0.0', LOCAL_PORT))

    print("Registering...")
    sock.sendto(b"HELLO", (MATCHMAKER_IP, MATCHMAKER_PORT))

    data, _ = sock.recvfrom(1024)
    ip, port = data.decode('utf-8').split(":")
    base_port = int(port)
    peer_info["addr"] = (ip, base_port)

    threading.Thread(target=listen_loop, args=(sock,), daemon=True).start()

    print(f"Matchmaker saw port {base_port}. Starting Port Shotgun...")

    # THE SHOTGUN: Send punches to the expected port AND the next 5 ports.
    # This bypasses 90% of Symmetric NAT port-shifting.
    for i in range(10):
        for offset in range(-2, 6):  # Try ports -2 to +5
            sock.sendto(b"__punch__", (ip, base_port + offset))
        time.sleep(0.5)

    print("--- READY ---")
    while True:
        msg = input("You: ")
        if msg.lower() == 'exit': break
        # We always send to the LATEST discovered address
        sock.sendto(msg.encode('utf-8'), peer_info["addr"])


if __name__ == "__main__":
    start_p2p()