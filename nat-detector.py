import socket
import struct
import random


def get_stun_binding_request():
    # STUN Message Type: 0x0001 (Binding Request)
    # Message Length: 0x0000
    # Magic Cookie: 0x2112A442
    # Transaction ID: 12 random bytes
    transaction_id = bytes(random.getrandbits(8) for _ in range(12))
    return struct.pack("!HHI12s", 0x0001, 0x0000, 0x2112A442, transaction_id)


def parse_stun_response(data):
    # This is a simplified parser for the XOR-MAPPED-ADDRESS (Type 0x0020)
    # In a production environment, you'd iterate through all attributes.
    try:
        # Skip header (20 bytes)
        pos = 20
        while pos < len(data):
            attr_type, attr_len = struct.unpack("!HH", data[pos:pos + 4])
            if attr_type == 0x0020:  # XOR-MAPPED-ADDRESS
                # Skip 1 byte (reserved) and 1 byte (protocol family)
                _, family, x_port = struct.unpack("!BBH", data[pos + 4:pos + 8])
                x_ip = struct.unpack("!I", data[pos + 8:pos + 12])[0]

                # XOR-masking logic to get real Port and IP
                port = x_port ^ 0x2112
                ip = socket.inet_ntoa(struct.pack("!I", x_ip ^ 0x2112A442))
                return f"{ip}:{port}"
            pos += 4 + attr_len
    except Exception:
        return None
    return None
def determine_nat_type(results):
    # Filter out None values from timeouts
    valid_results = [r for r in results if r is not None]

    if len(valid_results) < 2:
        return "ERROR: Not enough data (UDP might be restricted)"

    # Extract just the ports for comparison
    # pub_addr format is "IP:PORT"
    ports = [addr.split(":")[1] for addr in valid_results]

    # Check if all ports are the same
    if len(set(ports)) == 1:
        # To distinguish between Full Cone and Restricted,
        # you'd need the "Change Request" attribute (RFC 3489).
        # But for most P2P apps, knowing it's "CONE" is the big win.
        return "CONE NAT (P2P Friendly)"
    else:
        return "SYMMETRIC NAT (P2P Difficult - requires TURN relay)"

def test_nat():
    stun_servers = [
        ("stun.l.google.com", 19302),  # Primary Google STUN
        ("stun1.l.google.com", 19302),  # Backup Google STUN
        ("stun.sipgate.net", 3478),  # High-reliability alternative
        ("stun.voipawesome.com", 3478)  # Community-run alternative
    ]

    results = []
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(2.0)
    sock.bind(("0.0.0.0", 0))

    for host, port in stun_servers:
        try:
            # Pre-resolving to ensure the hostname is valid before sending
            remote_addr = (socket.gethostbyname(host), port)

            request = get_stun_binding_request()
            sock.sendto(request, remote_addr)

            data, _ = sock.recvfrom(1024)
            pub_addr = parse_stun_response(data)
            results.append(pub_addr)
            print(f"Response from {host}: {pub_addr}")
        except socket.gaierror:
            print(f"DNS Error: Could not resolve {host}. Check your internet connection.")
            results.append(None)
        except socket.timeout:
            print(f"Timeout: No response from {host}")
            results.append(None)
    print(f"\nFinal Assessment: {determine_nat_type(results)}")


    # Add this to your test_nat() function:
    # print(f"\nFinal Assessment: {determine_nat_type(results)}")
    # ... (rest of your NAT logic)


if __name__ == "__main__":
    test_nat()