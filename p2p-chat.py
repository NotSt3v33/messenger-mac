import socket
import threading
import time

#constants
MATCHMAKER_IP = "35.209.155.240"
MATCHMAKER_PORT = 10000
LOCAL_PORT = 50005


peer_info = {"addr": None, "uid":None}


def listen_loop(sock):
    while True:
        try:
            data, addr = sock.recvfrom(2048)
            if peer_info["addr"] != addr:
                peer_info["addr"] = addr
                print(f"peer port: {addr[1]}")

            msg = data.decode('utf-8', errors='ignore')
            if "__portscan__" in msg: continue #port scan
            print(f"\r[Peer]: {msg}\nYou: ", end="", flush=True)
        except (ConnectionResetError, ConnectionAbortedError):#holepunching errors?
            continue
        except Exception as e:
            print(f"error:{e}")
            break


def start_p2p():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('0.0.0.0', LOCAL_PORT))

    print("connecting to server...")
    sock.sendto(b"HELLO", (MATCHMAKER_IP, MATCHMAKER_PORT))

    data, _ = sock.recvfrom(1024)
    ip, port = data.decode('utf-8').split(":")
    base_port = int(port)
    peer_info["addr"] = (ip, base_port)

    threading.Thread(target=listen_loop, args=(sock,), daemon=True).start()

    print(f"Server connection through {base_port}. Port scan:")

    for i in range(10):
        for offset in range(-2, 6):
            sock.sendto(b"__portscan__", (ip, base_port + offset))
        time.sleep(0.5)

    print("---READY---")
    while True:
        msg = input("You: ")
        if msg.lower() == 'exit': break
        sock.sendto(msg.encode('utf-8'), peer_info["addr"])


if __name__ == "__main__":
    start_p2p()