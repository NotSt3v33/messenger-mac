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

            # If we receive a Public Key, store it in peer_info
            if data.startswith(b"PUB:"):
                peer_info["raw_pub_key"] = data[4:]
                # Update address just in case it's different
                peer_info["addr"] = addr
                continue

            if b"__portscan__" in data:
                continue

            if peer_info["cipher"]:
                try:
                    decrypted = peer_info["cipher"].decrypt(data).decode()
                    print(f"\r[Peer]: {decrypted}\nYou: ", end="", flush=True)
                except:
                    pass
        except:
            break


# Add "raw_pub_key" to your global dictionary at the top
peer_info = {"addr": None, "cipher": None, "raw_pub_key": None}


def start_p2p():
    room_id = input("Enter Room ID: ").strip()

    print("Generating secure keys (512-bit)...")
    parameters = dh.generate_parameters(generator=2, key_size=512)
    private_key = parameters.generate_private_key()
    public_key = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('0.0.0.0', LOCAL_PORT))

    sock.sendto(f"HELLO:{room_id}".encode(), (MATCHMAKER_IP, MATCHMAKER_PORT))
    data, _ = sock.recvfrom(1024)
    ip, port = data.decode('utf-8').split(":")
    peer_info["addr"] = (ip, int(port))

    # Start the listener BEFORE we start the handshake loop
    threading.Thread(target=listen_loop, args=(sock,), daemon=True).start()

    print("Performing secure handshake...")

    # LOOP UNTIL the listen_loop catches the key
    while peer_info["raw_pub_key"] is None:
        for offset in range(-2, 6):
            target = (ip, int(port) + offset)
            sock.sendto(b"PUB:" + public_key, target)
            sock.sendto(b"__portscan__", target)

        print("Waiting for peer key...")
        time.sleep(1)  # Wait 1 second before blasting the ports again

    # Finalize Encryption using the key the listener caught
    peer_public_key = serialization.load_pem_public_key(peer_info["raw_pub_key"])
    shared_secret = private_key.exchange(peer_public_key)
    peer_info["cipher"] = Fernet(derive_key(shared_secret))

    print(f"--- SECURE CHANNEL ESTABLISHED (Room:{room_id}) ---")

    while True:
        msg = input("You: ")
        if msg.lower() == 'exit': break
        if peer_info["cipher"]:
            encrypted = peer_info["cipher"].encrypt(msg.encode())
            sock.sendto(encrypted, peer_info["addr"])

if __name__ == "__main__":
    start_p2p()