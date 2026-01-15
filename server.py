import socket


def start_matchmaker():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', 10000))
    waiting_peers = {}

    print("Matchmaker online")

    while True:
        data, addr = sock.recvfrom(1024)
        msg = data.decode().strip()

        if msg.startswith("HELLO:"):
            room_id = msg.split(":")[1]

            if room_id in waiting_peers:
                peer_addr = waiting_peers.pop(room_id)
                sock.sendto(f"{peer_addr[0]}:{peer_addr[1]}".encode(), addr)
                sock.sendto(f"{addr[0]}:{addr[1]}".encode(), peer_addr)
                print(f"Matched room: {room_id}")
            else:
                waiting_peers[room_id] = addr
                print(f"User waiting in room: {room_id}")


if __name__ == "__main__":
    start_matchmaker()