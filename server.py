import socket
import random
import string

def generate_room_id():
    # xxx-xxxx-xxx
    return "-".join([''.join(random.choices(string.ascii_lowercase, k=n)) for n in [3, 4, 3]])

def start_matchmaker():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', 10000))
    waiting_rooms = {}

    print("Matchmaker v2 (Explicit) online...")

    while True:
        data, addr = sock.recvfrom(1024)
        msg = data.decode().strip()

        if msg == "NEW":
            new_id = generate_room_id()
            waiting_rooms[new_id] = addr
            sock.sendto(f"INFO:{new_id}".encode(), addr)
            print(f"Room Created: {new_id}")

        elif msg.startswith("JOIN:"):
            room_id = msg.split(":")[1]
            if room_id in waiting_rooms:
                peer_addr = waiting_rooms.pop(room_id)
                # Explicitly tell BOTH users who their peer is
                sock.sendto(f"PEER:{peer_addr[0]}:{peer_addr[1]}".encode(), addr)
                sock.sendto(f"PEER:{addr[0]}:{addr[1]}".encode(), peer_addr)
                print(f"Matched Room: {room_id}")
            else:
                sock.sendto(b"ERROR:NOT_FOUND", addr)

if __name__ == "__main__":
    start_matchmaker()