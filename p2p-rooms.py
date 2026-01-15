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
            data, addr = sock.recvfrom(2048)
            if peer_info["addr"] != addr:
                peer_info["addr"] = addr

            msg = data.decode('utf-8', errors='ignore')
            if "__portscan__" in msg: continue
            print(f"\r[Peer]: {msg}\nYou: ", end="", flush=True)
        except:
            break


def start_p2p():
    room_id = input("enter room id").strip()
    if not room_id:
        print("specify room ID")
        return

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('0.0.0.0', LOCAL_PORT))

    print(f"Connecting to Matchmaker for Room: {room_id}...")
    reg_msg = f"HELLO:{room_id}"
    sock.sendto(reg_msg.encode(), (MATCHMAKER_IP, MATCHMAKER_PORT))

    data, _ = sock.recvfrom(1024)
    ip, port = data.decode('utf-8').split(":")
    base_port = int(port)
    peer_info["addr"] = (ip, base_port)

    threading.Thread(target=listen_loop, args=(sock,), daemon=True).start()

    print(f"Connected to room. Starting Port Shotgun on {ip}:{base_port}...")
    for i in range(10):
        for offset in range(-2, 6):
            sock.sendto(b"__portscan__", (ip, base_port + offset))
        time.sleep(0.3)

    print(f"--- READY (Room: {room_id}) ---")
    while True:
        msg = input("You: ")
        if msg.lower() == 'exit': break
        sock.sendto(msg.encode('utf-8'), peer_info["addr"])

if __name__ == "__main__":
    start_p2p()