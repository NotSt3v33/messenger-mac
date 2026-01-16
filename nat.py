import socket, threading, time

# Use your Matchmaker IP
M_IP, M_PORT, L_PORT = "35.209.155.240", 10000, 50005
peer_addr = None

def listen(s):
    global peer_addr
    while True:
        data, addr = s.recvfrom(4096)
        peer_addr = addr
        print(f"\n[RECV] {len(data)} bytes from {addr}: {data[:20]}...")

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind(('0.0.0.0', L_PORT))

room = input("Room ID: ")
s.sendto(f"JOIN:{room}".encode(), (M_IP, M_PORT))

# Get Peer IP from server
while peer_addr is None:
    data, _ = s.recvfrom(1024)
    if b"PEER:" in data:
        p = data.decode()[5:].split(":")
        peer_addr = (p[0], int(p[1]))

threading.Thread(target=listen, args=(s,), daemon=True).start()

print(f"Testing connection to {peer_addr}...")
while True:
    # Test 1: Small packet (like your old code)
    s.sendto(b"SMALL_TEST", peer_addr)
    # Test 2: Large packet (size of an encryption key)
    s.sendto(b"LARGE_TEST_" + b"X" * 500, peer_addr)
    time.sleep(2)