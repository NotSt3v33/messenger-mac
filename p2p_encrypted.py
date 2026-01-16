import socket
import threading
import time
import os
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# --- CONFIG ---
MATCHMAKER_IP = "35.209.155.240"
MATCHMAKER_PORT = 10000
LOCAL_PORT = 50005


class SecureState:
    def __init__(self):
        self.peer_addr = None
        self.shared_key = None
        self.verified = False
        self.my_private_key = x25519.X25519PrivateKey.generate()
        self.my_public_bytes = self.my_private_key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )


state = SecureState()


def derive_aes_key(shared_secret):
    return HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b'p2p-chat-v1',
    ).derive(shared_secret)


def encrypt_msg(message_str):
    aesgcm = AESGCM(state.shared_key)
    nonce = os.urandom(12)  # GCM needs a unique 12-byte nonce per message
    ciphertext = aesgcm.encrypt(nonce, message_str.encode(), None)
    return nonce + ciphertext


def decrypt_msg(raw_data):
    aesgcm = AESGCM(state.shared_key)
    nonce = raw_data[:12]
    ciphertext = raw_data[12:]
    return aesgcm.decrypt(nonce, ciphertext, None).decode()


def listen_loop(sock):
    while True:
        try:
            data, addr = sock.recvfrom(4096)
            state.peer_addr = addr  # Update for NAT shifts

            if data.startswith(b"KEY:"):
                peer_pub_raw = data[4:]
                peer_public_key = x25519.X25519PublicKey.from_public_bytes(peer_pub_raw)
                shared_secret = state.my_private_key.exchange(peer_public_key)
                state.shared_key = derive_aes_key(shared_secret)
                continue

            if data.startswith(b"VFY:"):
                if state.shared_key:
                    try:
                        if decrypt_msg(data[4:]) == "OK":
                            state.verified = True
                    except:
                        pass
                continue

            if state.verified:
                try:
                    msg = decrypt_msg(data)
                    print(f"\r[Peer]: {msg}\nYou: ", end="", flush=True)
                except:
                    pass
        except:
            break


def start_p2p():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('0.0.0.0', LOCAL_PORT))

    choice = input("Enter Room ID or press Enter to generate NEW: ").strip()
    sock.sendto(b"NEW" if not choice else f"JOIN:{choice}".encode(), (MATCHMAKER_IP, MATCHMAKER_PORT))

    resp_data, _ = sock.recvfrom(1024)
    resp = resp_data.decode()
    if "ERROR" in resp: return print("Room not found.")

    room_id = resp.split(":")[1] if "CREATED" in resp else choice
    print(f"Room: {room_id}. Waiting for peer...")

    peer_raw, _ = sock.recvfrom(1024)
    ip, port = peer_raw.decode().split(":")
    state.peer_addr = (ip, int(port))

    threading.Thread(target=listen_loop, args=(sock,), daemon=True).start()

    # Handshake Loop
    print("Securing connection...")
    while not state.verified:
        # 1. Send Public Key
        sock.sendto(b"KEY:" + state.my_public_bytes, state.peer_addr)
        # 2. If we have a key, send an encrypted Verify
        if state.shared_key:
            try:
                vfy_pkt = b"VFY:" + encrypt_msg("OK")
                sock.sendto(vfy_pkt, state.peer_addr)
            except:
                pass
        time.sleep(0.5)

    print(f"--- SECURE CHANNEL READY ---")
    while True:
        msg = input("You: ")
        if msg.lower() == 'exit': break
        sock.sendto(encrypt_msg(msg), state.peer_addr)


if __name__ == "__main__":
    start_p2p()