"""生成 ACCESS_PASSWORD 哈希的辅助工具。

平时不用：设置页的"修改密码"会自动把明文哈希后存到 server/.settings.json。
仅当需要手动 seed 一个哈希（例如灾难恢复、首次部署的脚本）时再用。

用法:
    python -m server.hash_password <密码>           # 单参数，密码作为 argv
    python -m server.hash_password                  # 无参数，交互式读入（不回显）

输出形如：
    scrypt$32768$8$1$<salt_b64>$<hash_b64>
直接粘到 server/.settings.json 的 "access_password" 字段即可。
"""

import getpass
import sys

from server.auth import hash_password


def main() -> int:
    if len(sys.argv) > 2:
        print("用法: python -m server.hash_password [密码]", file=sys.stderr)
        return 2

    if len(sys.argv) == 2:
        password = sys.argv[1]
    else:
        password = getpass.getpass("输入密码: ")
        confirm = getpass.getpass("再输一次: ")
        if password != confirm:
            print("两次输入不一致。", file=sys.stderr)
            return 1

    if not password:
        print("密码不能为空。", file=sys.stderr)
        return 1

    print(hash_password(password))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
