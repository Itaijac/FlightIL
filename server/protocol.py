import base64
from Crypto.Cipher import AES
from Crypto import Random


SIZE_HEADER_FORMAT = "000000000|" # n digits for data size + one delimiter
size_header_size = len(SIZE_HEADER_FORMAT)
TCP_DEBUG = False
LEN_TO_PRINT = 100

BS = 16
def pad(s): return s + (BS - len(s) % BS) * chr(BS - len(s) % BS)
def unpad(s): return s[:-ord(s[len(s)-1:])]

def recv_by_size(sock, key=None):
    size_header = b''
    data_len = 0
    while len(size_header) < size_header_size:
        _s = sock.recv(size_header_size - len(size_header))
        if _s == b'':
            size_header = b''
            break
        size_header += _s
    data  = b''
    if size_header != b'':
        data_len = int(size_header[:size_header_size - 1])
        while len(data) < data_len:
            _d = sock.recv(data_len - len(data))
            if _d == b'':
                data  = b''
                break
            data += _d

    if  TCP_DEBUG and size_header != b'':
        print ("\nRecv(%s)>>>" % (size_header,), end='')
        print ("%s"%(data[:min(len(data),LEN_TO_PRINT)],))
    if data_len != len(data):
        data=b'' # Partial data is like no data !

    # if key is not None and data != b'':
    #     # Decrypt 
    #     enc = base64.b64decode(data)
    #     iv = enc[:16]
    #     cipher = AES.new(key, AES.MODE_CBC, iv)
    #     data = unpad(cipher.decrypt(enc[16:])).decode()

    return data


def send_with_size(sock, bdata, key=None):
    # if key is not None:
    #     raw = pad(bdata)
    #     iv = Random.new().read(AES.block_size)
    #     cipher = AES.new(key, AES.MODE_CBC, iv)
    #     bdata = base64.b64encode(iv + cipher.encrypt(raw.encode()))

    len_data = len(bdata)
    header_data = str(len(bdata)).zfill(size_header_size - 1) + "|"

    bytea = bytearray(header_data,encoding='utf8') + bdata

    sock.send(bytea)
    if TCP_DEBUG and  len_data > 0:
        print ("\nSent(%s)>>>" % (len_data,), end='')
        print ("%s"%(bytea[:min(len(bytea),LEN_TO_PRINT)],))
