import socket, threading, time, os
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

MATCHMAKER_IP = "35.209.155.240"
MATCHMAKER_PORT = 10000
LOCAL_PORT = 50005

# Global state
peer_info = {"addr": None, "key": None, "verified": False}
my_priv = x25519.X25519PrivateKey.generate()
my_pub = my_priv.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)


def encrypt(msg):
    aesgcm = AESGCM(peer_info["key"])
    nonce = os.urandom(12)
    return nonce + aesgcm.encrypt(nonce, msg.encode(), None)


def decrypt(data):
    aesgcm = AESGCM(peer_info["key"])
    return aesgcm.decrypt(data[:12], data[12:], None).decode()


def listen_loop(sock):
    while True:
        try:
            data, addr = sock.recvfrom(4096)
            if data == b"PUNCH":  # Ignore the hole-punching noise
                continue
            if data.startswith(b"KEY:"):
                raw_pub = data[4:]
                shared = my_priv.exchange(x25519.X25519PublicKey.from_public_bytes(raw_pub))
                peer_info["key"] = HKDF(hashes.SHA256(), 32, None, b'p2p').derive(shared)
            elif data.startswith(b"VFY:"):
                if peer_info["key"] and decrypt(data[4:]) == "OK":
                    peer_info["verified"] = True
            elif peer_info["verified"]:
                print(f"\r[Peer]: {decrypt(data)}\nYou: ", end="", flush=True)
        except:
            continue


def start_p2p():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Using 0 lets the OS pick a random free port if 50005 is busy,
    # but LOCAL_PORT is fine for consistency.
    sock.bind(('0.0.0.0', LOCAL_PORT))

    choice = input("Enter Room ID or press Enter for NEW: ").strip()
    sock.sendto(b"NEW" if not choice else f"JOIN:{choice}".encode(), (MATCHMAKER_IP, MATCHMAKER_PORT))

    # --- PHASE 1: Get Room Info & Peer ---
    while peer_info["addr"] is None:
        raw, _ = sock.recvfrom(1024)
        try:
            msg = raw.decode()
            print(f"DEBUG: Received message: {msg}")
            if msg.startswith("INFO:"):
                # Use [5:] to skip "INFO:"
                print(f"Room created! ID: {msg[5:]}\nWaiting for friend...")
            elif msg.startswith("PEER:"):
                # Skip "PEER:" by taking everything after the first 5 characters
                # Then split the remaining "91.200.10.124:50005"
                peer_data = msg[5:]
                parts = peer_data.split(":")
                peer_info["addr"] = (parts[0], int(parts[1]))
            elif "ERROR" in msg:
                print("Room not found.");
                return
        except UnicodeDecodeError:
            continue

    threading.Thread(target=listen_loop, args=(sock,), daemon=True).start()
    import pprint
    print("Punching hole in NAT...")
    for _ in range(10):  # Hammer it 10 times
        sock.sendto(b"PUNCH", peer_info["addr"])
        time.sleep(0.1)

    # Now start the listener
    threading.Thread(target=listen_loop, args=(sock,), daemon=True).start()
    # --- PHASE 2: Secure Handshake ---
    print(f"DEBUG: Starting handshake for {peer_info['addr']}")
    print(f"DEBUG: Initial peer_info state: {pprint.pformat(peer_info)}")

    while not peer_info["verified"]:
        print(f"\n--- Loop Tick: {time.time()} ---")

        # 1. Check sending the key
        print(f"DEBUG: Attempting to send KEY to {peer_info['addr']}...")
        try:
            sock.sendto(b"KEY:" + my_pub, peer_info["addr"])
            print("DEBUG: KEY packet sent successfully.")
        except Exception as e:
            print(f"DEBUG ERROR: Failed to send KEY: {e}")

        # 2. Check if we have the peer's key yet
        if peer_info["key"]:
            print(f"DEBUG: Peer key found. Attempting VFY message...")
            try:
                encrypted_msg = encrypt("OK")
                sock.sendto(b"VFY:" + encrypted_msg, peer_info["addr"])
                print("DEBUG: VFY packet sent.")
            except Exception as e:
                # This 'except' was hiding errors before!
                print(f"DEBUG ERROR: Encryption or VFY send failed: {e}")
        else:
            print("DEBUG: Still waiting to receive peer's key (peer_info['key'] is empty).")

        # 3. Check the verified status again
        print(f"DEBUG: Current verification status: {peer_info['verified']}")

        time.sleep(0.5)

    print("DEBUG: Loop exited! Connection is verified.")

    print("--- SECURE CHANNEL READY ---")
    while True:
        msg = input("You: ")
        if msg.lower() == 'exit': break
        # Important: Don't send empty messages as they can break some decoders
        if msg.strip():
            sock.sendto(encrypt(msg), peer_info["addr"])


if __name__ == "__main__":
    start_p2p()