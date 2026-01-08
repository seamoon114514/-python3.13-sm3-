# SM3（纯 Python 3.13 实现）

一个不依赖第三方密码学库的 SM3 哈希算法实现，位于 `sm3.py`。支持命令行和作为模块调用。

## 环境要求
- Python `3.13`（兼容更高版本），Windows/macOS/Linux 皆可

## 快速开始（命令行）
- 默认对空字符串取哈希（打印十六进制）：
  - `python sm3.py`
- 对 UTF-8 字符串：
  - `python sm3.py -s "abc"`
- 对十六进制字节：
  - `python sm3.py -x 616263`
- 对文件内容：
  - `python sm3.py -f sm3.py`
- 输出原始字节（非十六进制）：
  - 在上述任一命令末尾添加 `--raw`

### 命令行帮助
- `python sm3.py -h`
- 选项说明：
  - `-s/--string <TEXT>` 对 UTF-8 字符串取哈希
  - `-x/--hex <HEX>` 对十六进制字节取哈希
  - `-f/--file <PATH>` 对文件内容取哈希
  - `--raw` 输出原始字节到标准输出

## 作为模块使用
```python
from sm3 import SM3

# 一次性
print(SM3.hexhash(b"abc"))

# 流式（分块）
h = SM3()
h.update(b"part1")
h.update(b"part2")
print(h.hexdigest())
```

## 已知测试向量
- `abc` → `66c7f0f462eeedd9d1f2d46bdc10e4e24167c4875cf2f7a2297da02b8f4ba8e0`
- `abcdefghijklmnopqrstuvwxyz` → `b80fe97a4da24afc277564f66a359ef440462ad28dcc6d63adb24d5c20a61595`
- 空字符串 → `1ab21d8355cfa17f8e61194831e81a8f22bec8c728fefb747ed035eb5082aa2b`

## 运行内置测试
- `python test_sm3.py`
- 通过则输出 `ok`

## 安全性验证（碰撞性与雪崩效应）
- 验证脚本：`validate_sm3_properties.py`
- 基本运行：`python validate_sm3_properties.py`
- 参数：
  - `--n-collision <N>` 碰撞性样本数，默认 `2000`
  - `--n-avalanche <N>` 雪崩效应样本数，默认 `1000`
  - `--max-len <L>` 随机消息最大长度（字节），默认 `256`
  - `--seed <S>` 随机种子，默认不设
  - `--show <K>` 报告中每块展示的样本条数，默认 `8`
- 报告说明：
  - 样本表格展示完整哈希值（不截断）
  - 抗碰撞性部分：样本数、部分样本、是否检测到碰撞与碰撞率
  - 雪崩效应部分：随机翻转 1 位，展示部分样本的位变更与比例，统计均值/标准差/最小/最大及总体结论

## 说明
- 实现遵循 SM3 标准流程：填充、消息扩展（`W/W'`）、压缩函数（`FF/GG`、`SS1/SS2`、`TT1/TT2`）
- 仅用于学习与集成验证，如用于生产安全场景请配合完备的密钥与安全策略
