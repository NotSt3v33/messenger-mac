import socket, threading, time, os
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# --- CONFIG ---
M_IP, M_PORT, L_PORT = "35.209.155.240", 10000, 50005


# --- CRYPTO HELPERS ---
def get_cipher(shared_secret):
    key = HKDF(hashes.SHA256(), 32, None, b'p2p').derive(shared_secret)
    return AESGCM(key)


def encrypt(cipher, msg):
    nonce = os.urandom(12)
    return nonce + cipher.encrypt(nonce, msg.encode(), None)


def decrypt(cipher, data):
    return cipher.decrypt(data[:12], data[12:], None).decode()


# --- GLOBAL STATE ---
state = {"peer": None, "cipher": None, "verified": False}
my_priv = x25519.X25519PrivateKey.generate()
my_pub = my_priv.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)


def listen_loop(sock):
    while True:
        try:
            data, addr = sock.recvfrom(4096)
            state["peer"] = addr  # Keep port alive

            if data.startswith(b"K:"):
                peer_pub = x25519.X25519PublicKey.from_public_bytes(data[2:])
                shared = my_priv.exchange(peer_pub)
                state["cipher"] = get_cipher(shared)
            elif data.startswith(b"V:"):
                if state["cipher"] and decrypt(state["cipher"], data[2:]) == "OK":
                    state["verified"] = True
            elif state["verified"]:
                print(f"\r[Peer]: {decrypt(state['cipher'], data)}\nYou: ", end="", flush=True)
        except:
            continue


def start():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', L_PORT))

    room = input("Room ID (Enter for NEW): ").strip()
    sock.sendto(b"NEW" if not room else f"JOIN:{room}".encode(), (M_IP, M_PORT))

    # 1. Server Handshake
    while state["peer"] is None:
        data, _ = sock.recvfrom(1024)
        msg = data.decode(errors='ignore')
        if "INFO:" in msg: print(f"Room: {msg[5:]}")
        if "PEER:" in msg:
            p = msg[5:].split(":")
            state["peer"] = (p[0], int(p[1]))

    threading.Thread(target=listen_loop, args=(sock,), daemon=True).start()

    # 2. Secure Handshake (The "Sticky Port" Loop)
    print(f"Connecting to {state['peer']}...")
    while not state["verified"]:
        # We send to the exact peer port found by the server
        sock.sendto(b"K:" + my_pub, state["peer"])
        if state["cipher"]:
            try:
                sock.sendto(b"V:" + encrypt(state["cipher"], "OK"), state["peer"])
            except:
                pass
        time.sleep(1)  # Slow & steady to keep the NAT mapping stable

    print("--- SECURE ---")
    while True:
        msg = input("You: ")
        sock.sendto(encrypt(state["cipher"], msg), state["peer"])


if __name__ == "__main__":
    start()