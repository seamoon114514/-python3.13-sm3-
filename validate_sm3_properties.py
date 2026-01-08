import argparse
import os
import random
import statistics
import sys
from sm3 import SM3


def _rand_msg(max_len):
    n = random.randint(0, max_len)
    return os.urandom(n)


def _flip_one_bit(b):
    if not b:
        return None
    pos = random.randint(0, len(b) * 8 - 1)
    byte_i = pos // 8
    bit_i = pos % 8
    mask = 1 << (7 - bit_i)
    nb = bytearray(b)
    nb[byte_i] ^= mask
    return bytes(nb)


def _hamming_bits(x, y):
    return (int.from_bytes(x, "big") ^ int.from_bytes(y, "big")).bit_count()

def _hex_preview(b, width=20):
    hx = b.hex()
    if len(hx) <= width:
        return hx
    return hx[:width] + "..."


def collision_test(n, max_len, seed, preview_count=8):
    if seed is not None:
        random.seed(seed)
    seen = {}
    dups = 0
    same_inputs = 0
    preview = []
    for _ in range(n):
        m = _rand_msg(max_len)
        h = SM3.hash(m)
        hx = h.hex()
        if hx in seen:
            if seen[hx] != m:
                dups += 1
            else:
                same_inputs += 1
        else:
            seen[hx] = m
        if len(preview) < preview_count:
            preview.append((m, h))
    return {
        "samples": n,
        "collisions": dups,
        "same_inputs": same_inputs,
        "collision_rate": (dups / n if n else 0.0),
        "preview": preview,
    }


def avalanche_test(n, max_len, seed, preview_count=8):
    if seed is not None:
        random.seed(seed)
    diffs = []
    skipped = 0
    preview = []
    for _ in range(n):
        m = _rand_msg(max_len)
        if not m:
            skipped += 1
            continue
        m2 = _flip_one_bit(m)
        h1 = SM3.hash(m)
        h2 = SM3.hash(m2)
        bits = _hamming_bits(h1, h2)
        diffs.append(bits)
        if len(preview) < preview_count:
            preview.append((m, bits, h1))
    if diffs:
        avg = statistics.mean(diffs)
        stdev = statistics.pstdev(diffs)
        rate = [d / 256 for d in diffs]
        avg_rate = statistics.mean(rate)
        min_bits = min(diffs)
        max_bits = max(diffs)
    else:
        avg = 0.0
        stdev = 0.0
        avg_rate = 0.0
        min_bits = 0
        max_bits = 0
    return {
        "samples": n,
        "used": n - skipped,
        "skipped_empty": skipped,
        "avg_bits_changed": avg,
        "stdev_bits_changed": stdev,
        "avg_rate": avg_rate,
        "min_bits_changed": min_bits,
        "max_bits_changed": max_bits,
        "preview": preview,
    }


def main():
    p = argparse.ArgumentParser(description="SM3 collision and avalanche verification")
    p.add_argument("--n-collision", type=int, default=2000)
    p.add_argument("--n-avalanche", type=int, default=1000)
    p.add_argument("--max-len", type=int, default=256)
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--show", type=int, default=8)
    args = p.parse_args()
    c = collision_test(args.n_collision, args.max_len, args.seed, args.show)
    a = avalanche_test(args.n_avalanche, args.max_len, args.seed, args.show)
    print("SM3 算法安全性测试报告")
    print("================================")
    print("--- 开始抗碰撞性测试 ---")
    print(f"正在生成 {c['samples']} 组随机样本并计算哈希...")
    print(f"测试完成。处理样本数：{c['samples']}")
    print("")
    print("部分测试样本：")
    print("输入(Hex)                 | 长度 | 哈希值")
    print("------------------------------------------------------------")
    for m, h in c["preview"]:
        ih = _hex_preview(m, 22)
        print(f"{ih:<24} | {len(m):>4} | {h.hex()}")
    print("")
    if c["collisions"] == 0:
        print(f"结论：基于 {c['samples']} 组样本，未检测到碰撞，符合抗碰撞性基本要求。")
    else:
        print(
            f"结论：检测到 {c['collisions']} 次不同输入碰撞，碰撞率 {c['collision_rate']:.8f}。"
            "建议增加样本或检查实现。"
        )
    print("")
    print("--- 开始雪崩效应测试 ---")
    print("随机翻转每条消息的 1 位比特并统计输出变化。")
    print(f"测试完成。有效样本：{a['used']} / 总样本：{a['samples']}")
    print("")
    print("部分测试样本：")
    print("输入(Hex)                 | 长度 | 位变更 | 比例    | 哈希值")
    print("-------------------------------------------------------------------")
    for m, bits, h in a["preview"]:
        ih = _hex_preview(m, 22)
        rate = bits / 256
        print(f"{ih:<24} | {len(m):>4} | {bits:>6} | {rate:>6.2%} | {h.hex()}")
    print("")
    print(
        f"整体统计：位变更均值 {a['avg_bits_changed']:.2f}/256 ({a['avg_rate']*100:.2f}%)，"
        f"标准差 {a['stdev_bits_changed']:.2f}，最小/最大 {a['min_bits_changed']} / {a['max_bits_changed']}。"
    )
    if 0.45 <= a["avg_rate"] <= 0.55:
        print("结论：平均位变更接近 50%，雪崩效应表现良好。")
    else:
        print("结论：平均位变更偏离 50%，建议复核实现或扩大样本。")


if __name__ == "__main__":
    main()
