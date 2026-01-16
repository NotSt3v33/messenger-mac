import socket
import random
import string


def generate_room_id():
    part1 = ''.join(random.choices(string.ascii_lowercase, k=3))
    part2 = ''.join(random.choices(string.ascii_lowercase, k=4))
    part3 = ''.join(random.choices(string.ascii_lowercase, k=3))
    return f"{part1}-{part2}-{part3}"


def start_matchmaker():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', 10000))

    waiting_rooms = {}  # { "room-id": (ip, port) }

    print("Matchmaker with Auto-Generation online...")

    while True:
        data, addr = sock.recvfrom(1024)
        msg = data.decode().strip()

        # CASE 1: User wants a NEW room
        if msg == "NEW":
            new_id = generate_room_id()
            while new_id in waiting_rooms:
                new_id = generate_room_id()

            waiting_rooms[new_id] = addr
            sock.sendto(f"CREATED:{new_id}".encode(), addr)
            print(f"Room Created: {new_id} for {addr}")

        # CASE 2: User wants to JOIN a room
        elif msg.startswith("JOIN:"):
            room_id = msg.split(":")[1]

            if room_id in waiting_rooms:
                peer_addr = waiting_rooms.pop(room_id)
                # Exchange info
                sock.sendto(f"{peer_addr[0]}:{peer_addr[1]}".encode(), addr)
                sock.sendto(f"{addr[0]}:{addr[1]}".encode(), peer_addr)
                print(f"Matched Room: {room_id}")
            else:
                sock.sendto(b"ERROR:NOT_FOUND", addr)


if __name__ == "__main__":
    start_matchmaker()