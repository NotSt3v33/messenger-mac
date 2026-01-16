import socket
import threading
import time
import sys

# --- CONFIG ---
MATCHMAKER_IP = "35.209.155.240"
MATCHMAKER_PORT = 10000
LOCAL_PORT = 50005

# --- GLOBAL STATE ---
# We store the target as a list so threads can update it
target = {"ip": None, "port": None}
running = True


def listen_loop(sock):
    global target
    print("[Listener] Started...")

    while running:
        try:
            data, addr = sock.recvfrom(4096)
            msg = data.decode('utf-8', errors='ignore')

            # 1. Check if this is from our known peer IP
            if target["ip"] and addr[0] == target["ip"]:

                # 2. SYMMETRIC NAT DETECTION
                # If the port is different from what we thought, UPDATE IT!
                if addr[1] != target["port"]:
                    print(f"\n[!] NAT SHIFT DETECTED!")
                    print(f"    Old Target: {target['port']}")
                    print(f"    New Source: {addr[1]}")
                    print(f"    >> SWITCHING TARGET to {addr[1]} <<")
                    target["port"] = addr[1]

            print(f"\r[RECV] '{msg}' from {addr}\nYou: ", end="", flush=True)

        except Exception as e:
            print(f"Listener Error: {e}")
            break


def start_test():
    global target
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', LOCAL_PORT))

    room = input("Enter Room ID (or Enter for NEW): ").strip()
    msg = b"NEW" if not room else f"JOIN:{room}".encode()
    sock.sendto(msg, (MATCHMAKER_IP, MATCHMAKER_PORT))

    print("Waiting for server match...")
    while target["ip"] is None:
        data, _ = sock.recvfrom(1024)
        decoded = data.decode()

        if "INFO:" in decoded:
            print(f"Room Created: {decoded[5:]}")
        elif "PEER:" in decoded:
            parts = decoded[5:].split(":")
            target["ip"] = parts[0]
            target["port"] = int(parts[1])
            print(f"Match found! Server says peer is at: {target['ip']}:{target['port']}")

    # Start the smart listener
    threading.Thread(target=listen_loop, args=(sock,), daemon=True).start()

    print("--- STARTING SMART HOLE PUNCHING ---")
    print("If connection fails, this script will auto-detect the correct port.")

    counter = 0
    while running:
        if target["ip"] and target["port"]:
            msg = f"Ping #{counter}"
            # Send to the CURRENT best known port
            sock.sendto(msg.encode(), (target['ip'], target['port']))

            if counter % 5 == 0:
                print(f"\r[SEND] Pinging {target['ip']}:{target['port']}...", end="")

            counter += 1
        time.sleep(0.5)  # Send 2 packets per second


if __name__ == "__main__":
    try:
        start_test()
    except KeyboardInterrupt:
        running = False