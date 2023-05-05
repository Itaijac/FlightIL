import base64
import random
from Crypto.Cipher import AES

SIZE_HEADER_FORMAT = "000000000|"  # n digits for data size + one delimiter
SIZE_HEADER_LENGTH = len(SIZE_HEADER_FORMAT)
TCP_DEBUG = False
LEN_TO_PRINT = 100

BLOCK_SIZE = 16

def pad(data):
    """Add padding to the given bytes object."""
    padding = BLOCK_SIZE - (len(data) % BLOCK_SIZE)
    return data + bytes([padding] * padding)

def unpad(data):
    """Remove padding from the given bytes object."""
    padding_length = data[-1]
    return data[:-padding_length]

def recv_by_size(sock, key=None) -> bytes:
    """Receive data of variable length over a socket."""
    size_header = b""
    data_len = 0
    while len(size_header) < SIZE_HEADER_LENGTH:
        remaining = SIZE_HEADER_LENGTH - len(size_header)
        chunk = sock.recv(remaining)
        if chunk == b"":
            size_header = b""
            break
        size_header += chunk
    data = b""
    if size_header != b"":
        data_len = int(size_header[:SIZE_HEADER_LENGTH - 1])
        while len(data) < data_len:
            remaining = data_len - len(data)
            chunk = sock.recv(remaining)
            if chunk == b"":
                data = b""
                break
            data += chunk

    if TCP_DEBUG and size_header != b"":
        print(f"\nRecv({size_header})>>> {data[:min(len(data), LEN_TO_PRINT)]}")

    if data_len != len(data):
        data = b""  # Partial data is like no data!

    if key is not None and data != b"":
        # Decrypt data
        enc = base64.b64decode(data)
        iv = enc[:BLOCK_SIZE]
        cipher = AES.new(key, AES.MODE_CBC, iv)
        data = unpad(cipher.decrypt(enc[BLOCK_SIZE:]))

    return data

def send_with_size(sock, data, key=None):
    """Send data of variable length over a socket."""
    if key is not None:
        # Encrypt data
        raw_data = pad(data)
        iv = random.getrandbits(BLOCK_SIZE * 8).to_bytes(BLOCK_SIZE, "big")
        cipher = AES.new(key, AES.MODE_CBC, iv)
        data = base64.b64encode(iv + cipher.encrypt(raw_data))

    data_len = len(data)
    header_data = str(data_len).zfill(SIZE_HEADER_LENGTH - 1) + "|"

    header_bytes = header_data.encode("utf-8")
    message_bytes = header_bytes + data
    sock.send(message_bytes)

    if TCP_DEBUG and data_len > 0:
        print(f"\nSent({data_len})>>> {message_bytes[:min(len(message_bytes), LEN_TO_PRINT)]}")
