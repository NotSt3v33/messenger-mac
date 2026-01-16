import socket
import threading
import time

# --- CONFIG ---
M_IP, M_PORT, L_PORT = "35.209.155.240", 10000, 50005

state = {"ip": None, "port": None, "found": False}


def listen(sock):
    while True:
        try:
            data, addr = sock.recvfrom(4096)
            if not state["found"]:
                print(f"\n[!] HOLE PUNCHED! Peer is actually at {addr}")
                state["ip"], state["port"] = addr
                state["found"] = True
            print(f"\r[RECV] from {addr}: {data.decode(errors='ignore')[:20]}")
        except:
            continue


def start():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', L_PORT))

    room = input("Room ID: ").strip()
    sock.sendto(f"JOIN:{room}".encode() if room else b"NEW", (M_IP, M_PORT))

    while state["ip"] is None:
        data, _ = sock.recvfrom(1024)
        msg = data.decode()
        if "INFO:" in msg: print(f"Room: {msg[5:]}")
        if "PEER:" in msg:
            p = msg[5:].split(":")
            state["ip"], state["port"] = p[0], int(p[1])

    threading.Thread(target=listen, args=(sock,), daemon=True).start()

    print(f"Starting Prediction Blast against {state['ip']}...")

    # We blast a range around the port the server saw
    # Most routers increment by 1 or stay the same.
    port_range = range(state["port"] - 5, state["port"] + 20)

    count = 0
    while True:
        if not state["found"]:
            # If we haven't found the peer yet, blast the whole range
            for p_guess in port_range:
                sock.sendto(f"PROBE_{count}".encode(), (state["ip"], p_guess))
        else:
            # Once found, lock on to that port
            sock.sendto(f"PING_{count}".encode(), (state["ip"], state["port"]))

        count += 1
        time.sleep(0.5)


if __name__ == "__main__":
    start()