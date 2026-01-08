from sm3 import SM3
import tempfile
import os


def _assert_eq(a, b):
    if a != b:
        raise AssertionError(f"{a} != {b}")


def test_vectors():
    _assert_eq(
        SM3.hexhash(b"abc"),
        "66c7f0f462eeedd9d1f2d46bdc10e4e24167c4875cf2f7a2297da02b8f4ba8e0",
    )
    _assert_eq(
        SM3.hexhash(b"abcdefghijklmnopqrstuvwxyz"),
        "b80fe97a4da24afc277564f66a359ef440462ad28dcc6d63adb24d5c20a61595",
    )
    _assert_eq(SM3.hexhash(b""), "1ab21d8355cfa17f8e61194831e81a8f22bec8c728fefb747ed035eb5082aa2b")
    _assert_eq(SM3.hexhash(b"a"), "623476ac18f65a2909e43c7fec61b49c7e764a91a18ccb82f1917a29c86c5e88")
    blk = ("abcd" * 16).encode("ascii")
    _assert_eq(SM3.hexhash(blk), "debe9ff92275b8a138604889c18e5a4d6fdb70e5387e5765293dcba39c0c5732")


def test_streaming_equivalence():
    data = b"a" * 1_000_000
    ref = SM3.hexhash(data)
    for step in (1, 7, 64, 4096, 65536):
        h = SM3()
        for i in range(0, len(data), step):
            h.update(data[i : i + step])
        _assert_eq(h.hexdigest(), ref)


def test_chinese_utf8():
    s = "中文字符串测试"
    b = s.encode("utf-8")
    ref = SM3.hexhash(b)
    h = SM3()
    h.update(b[:5])
    h.update(b[5:])
    _assert_eq(h.hexdigest(), ref)


def test_empty_file_vs_empty_string():
    with tempfile.NamedTemporaryFile(delete=True) as tmp:
        tmp.flush()
        tmp.seek(0)
        b = tmp.read()
        _assert_eq(SM3.hexhash(b), SM3.hexhash(b""))


def test_file_content_equals_string_digest():
    s = "文件的字符串"
    b = s.encode("utf-8")
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b)
        name = tmp.name
    try:
        with open(name, "rb") as fh:
            fb = fh.read()
        _assert_eq(SM3.hexhash(fb), SM3.hexhash(b))
    finally:
        try:
            os.remove(name)
        except OSError:
            pass


if __name__ == "__main__":
    test_vectors()
    test_streaming_equivalence()
    test_chinese_utf8()
    test_empty_file_vs_empty_string()
    test_file_content_equals_string_digest()
    print("ok")
