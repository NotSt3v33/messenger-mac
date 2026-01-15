import socket
import threading
import time
import base64
from cryptography.hazmat.primitives.asymmetric import dh
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.fernet import Fernet

# Constants
MATCHMAKER_IP = "35.209.155.240"
MATCHMAKER_PORT = 10000
LOCAL_PORT = 50005

peer_info = {"addr": None, "cipher": None}


def derive_key(shared_secret):
    """Turns a raw DH shared secret into a 32-byte key for Fernet."""
    return base64.urlsafe_b64encode(HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b'handshake data',
    ).derive(shared_secret))


def listen_loop(sock):
    while True:
        try:
            data, addr = sock.recvfrom(4096)
            if peer_info["addr"] != addr:
                peer_info["addr"] = addr

            # If it's a handshake packet, ignore it here (handled in start_p2p)
            if data.startswith(b"PUB:"): continue
            if b"__portscan__" in data: continue

            # Decrypt message
            if peer_info["cipher"]:
                try:
                    decrypted = peer_info["cipher"].decrypt(data).decode()
                    print(f"\r[Peer]: {decrypted}\nYou: ", end="", flush=True)
                except:
                    pass
            else:
                print(f"\r[Peer (Unencrypted)]: {data.decode()}\nYou: ", end="", flush=True)
        except:
            break


def start_p2p():
    room_id = input("Enter Room ID: ").strip()

    # 1. Generate DH Parameters and Keys
    print("Generating secure keys...")
    parameters = dh.generate_parameters(generator=2, key_size=1024)  # 1024 for speed in iSH
    private_key = parameters.generate_private_key()
    public_key = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('0.0.0.0', LOCAL_PORT))

    # 2. Matchmaking
    sock.sendto(f"HELLO:{room_id}".encode(), (MATCHMAKER_IP, MATCHMAKER_PORT))
    data, _ = sock.recvfrom(1024)
    ip, port = data.decode('utf-8').split(":")
    peer_info["addr"] = (ip, int(port))

    # 3. Start Background Listener
    threading.Thread(target=listen_loop, args=(sock,), daemon=True).start()

    # 4. Handshake & Holepunching
    print("Performing secure handshake...")
    peer_public_key_raw = None

    # Shotgun blast the Public Key and Portscan
    for i in range(15):
        for offset in range(-2, 6):
            target = (ip, int(port) + offset)
            sock.sendto(b"PUB:" + public_key, target)
            sock.sendto(b"__portscan__", target)

        # Check if we've received the peer's key yet
        # We peek at the socket to find the PUB: prefix
        try:
            sock.settimeout(0.1)
            response, _ = sock.recvfrom(4096)
            if response.startswith(b"PUB:"):
                peer_public_key_raw = response[4:]
                break
        except:
            continue

    if not peer_public_key_raw:
        print("Failed to receive peer public key. Try again.")
        return

    # 5. Finalize Encryption
    peer_public_key = serialization.load_pem_public_key(peer_public_key_raw)
    shared_secret = private_key.exchange(peer_public_key)
    peer_info["cipher"] = Fernet(derive_key(shared_secret))

    sock.settimeout(None)  # Reset timeout
    print(f"--- SECURE CHANNEL ESTABLISHED (Room:{room_id}) ---")

    while True:
        msg = input("You: ")
        if msg.lower() == 'exit': break
        # Encrypt and send
        encrypted = peer_info["cipher"].encrypt(msg.encode())
        sock.sendto(encrypted, peer_info["addr"])


if __name__ == "__main__":
    start_p2p()