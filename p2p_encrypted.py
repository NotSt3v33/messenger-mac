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

    print("Generating secure keys (512-bit)...")
    parameters = dh.generate_parameters(generator=2, key_size=512)
    private_key = parameters.generate_private_key()
    public_key = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    print("Keys generated.")

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('0.0.0.0', LOCAL_PORT))

    sock.sendto(f"HELLO:{room_id}".encode(), (MATCHMAKER_IP, MATCHMAKER_PORT))
    data, _ = sock.recvfrom(1024)
    ip, port = data.decode('utf-8').split(":")
    peer_info["addr"] = (ip, int(port))

    threading.Thread(target=listen_loop, args=(sock,), daemon=True).start()

    print("Performing secure handshake (waiting for peer)...")
    peer_public_key_raw = None
    sock.settimeout(1.0)  # Check for peer key every 1 second

    # LOOP UNTIL SUCCESS: This keeps the Mac waiting for the slow iPhone
    while not peer_public_key_raw:
        for offset in range(-2, 6):
            target = (ip, int(port) + offset)
            # Send our key to the peer
            sock.sendto(b"PUB:" + public_key, target)
            sock.sendto(b"__portscan__", target)

        try:
            # Try to catch the peer's key
            response, _ = sock.recvfrom(4096)
            if response.startswith(b"PUB:"):
                peer_public_key_raw = response[4:]
                # Send a confirmation so the other side knows we're done
                sock.sendto(b"PUB:" + public_key, peer_info["addr"])
                break
        except socket.timeout:
            print("Still waiting for peer...")
            continue
        except Exception as e:
            print(f"Handshake error: {e}")
            break

    # Finalize Encryption
    peer_public_key = serialization.load_pem_public_key(peer_public_key_raw)
    shared_secret = private_key.exchange(peer_public_key)
    peer_info["cipher"] = Fernet(derive_key(shared_secret))

    sock.settimeout(None)
    print(f"--- SECURE CHANNEL ESTABLISHED (Room:{room_id}) ---")

    while True:
        msg = input("You: ")
        if msg.lower() == 'exit': break
        encrypted = peer_info["cipher"].encrypt(msg.encode())
        sock.sendto(encrypted, peer_info["addr"])

if __name__ == "__main__":
    start_p2p()