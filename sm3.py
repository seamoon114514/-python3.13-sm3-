def _rotl32(x, n):
    n &= 31
    return ((x << n) | (x >> (32 - n))) & 0xFFFFFFFF


def _p0(x):
    return x ^ _rotl32(x, 9) ^ _rotl32(x, 17)


def _p1(x):
    return x ^ _rotl32(x, 15) ^ _rotl32(x, 23)


_IV = [
    0x7380166F,
    0x4914B2B9,
    0x172442D7,
    0xDA8A0600,
    0xA96F30BC,
    0x163138AA,
    0xE38DEE4D,
    0xB0FB0E4E,
]

_T0 = 0x79CC4519
_T1 = 0x7A879D8A


def _ff(j, a, b, c):
    if j <= 15:
        return a ^ b ^ c
    return (a & b) | (a & c) | (b & c)


def _gg(j, e, f, g):
    if j <= 15:
        return e ^ f ^ g
    return (e & f) | ((~e) & g)


def _expand(block):
    w = [0] * 68
    for i in range(16):
        w[i] = int.from_bytes(block[4 * i : 4 * i + 4], "big")
    for i in range(16, 68):
        t = w[i - 16] ^ w[i - 9] ^ _rotl32(w[i - 3], 15)
        w[i] = (_p1(t) ^ _rotl32(w[i - 13], 7) ^ w[i - 6]) & 0xFFFFFFFF
    wp = [0] * 64
    for i in range(64):
        wp[i] = (w[i] ^ w[i + 4]) & 0xFFFFFFFF
    return w, wp


def _compress(v, block):
    w, wp = _expand(block)
    a, b, c, d, e, f, g, h = v
    for j in range(64):
        tj = _T0 if j <= 15 else _T1
        ss1 = _rotl32(((_rotl32(a, 12) + e + _rotl32(tj, j)) & 0xFFFFFFFF), 7)
        ss2 = ss1 ^ _rotl32(a, 12)
        tt1 = (_ff(j, a, b, c) + d + ss2 + wp[j]) & 0xFFFFFFFF
        tt2 = (_gg(j, e, f, g) + h + ss1 + w[j]) & 0xFFFFFFFF
        d = c
        c = _rotl32(b, 9)
        b = a
        a = tt1
        h = g
        g = _rotl32(f, 19)
        f = e
        e = _p0(tt2)
    return [
        v[0] ^ a,
        v[1] ^ b,
        v[2] ^ c,
        v[3] ^ d,
        v[4] ^ e,
        v[5] ^ f,
        v[6] ^ g,
        v[7] ^ h,
    ]


def _pad(data_len):
    bit_len = data_len * 8
    pad = b"\x80"
    rem = (data_len + 1) % 64
    pad_len = (56 - rem) % 64
    pad += b"\x00" * pad_len
    pad += bit_len.to_bytes(8, "big")
    return pad


class SM3:
    def __init__(self):
        self._v = list(_IV)
        self._buf = bytearray()
        self._len = 0

    def update(self, data):
        if not data:
            return
        self._buf.extend(data)
        self._len += len(data)
        while len(self._buf) >= 64:
            blk = bytes(self._buf[:64])
            self._v = _compress(self._v, blk)
            del self._buf[:64]

    def _finalize(self):
        tmp_v = list(self._v)
        tmp_buf = bytes(self._buf) + _pad(self._len)
        for i in range(0, len(tmp_buf), 64):
            tmp_v = _compress(tmp_v, tmp_buf[i : i + 64])
        out = b"".join(x.to_bytes(4, "big") for x in tmp_v)
        return out

    def digest(self):
        return self._finalize()

    def hexdigest(self):
        return self._finalize().hex()

    @staticmethod
    def hash(data: bytes):
        h = SM3()
        h.update(data)
        return h.digest()

    @staticmethod
    def hexhash(data: bytes):
        h = SM3()
        h.update(data)
        return h.hexdigest()

if __name__ == "__main__":
    import argparse
    import sys
    parser = argparse.ArgumentParser(prog="sm3", description="SM3 hash (pure Python)")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-s", "--string", help="hash a UTF-8 string")
    group.add_argument("-x", "--hex", help="hash hex-encoded bytes")
    group.add_argument("-f", "--file", help="hash file contents")
    parser.add_argument("--raw", action="store_true", help="output raw bytes to stdout")
    args = parser.parse_args()
    if args.string is not None:
        data = args.string.encode("utf-8")
    elif args.hex is not None:
        try:
            data = bytes.fromhex(args.hex)
        except ValueError:
            print("invalid hex input", file=sys.stderr)
            sys.exit(2)
    elif args.file is not None:
        try:
            with open(args.file, "rb") as fh:
                data = fh.read()
        except OSError as e:
            print(str(e), file=sys.stderr)
            sys.exit(2)
    else:
        data = b""
    if args.raw:
        sys.stdout.buffer.write(SM3.hash(data))
    else:
        print(SM3.hexhash(data))
