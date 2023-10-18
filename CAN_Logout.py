"""
File: CAN_Logout.py(自动注销校园网)
Author: eya46
Date: 2023/10/18 10:18
cron: 0 0 3 1/1 * ? 
new Env('自动注销校园网');
Description:
每天凌晨3点注销校园网。
"""

from json import load
from urllib.parse import urlparse
from urllib.request import urlopen, Request


def get_userindex() -> str:
    return urlparse(urlopen("http://10.2.10.19").url).query


def logout(userindex: str):
    return urlopen(
        Request(
            "http://10.2.10.19/eportal/InterFace.do?method=logout",
            method="POST",
            headers={
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)" +
                              " Chrome/117.0.0.0 Safari/537.36"
            },
            data=userindex.encode("utf-8")
        )
    )


print("校园网自动注销登录~")
res = logout(get_userindex())
data = load(res)
print(
    f"状态:{data.get('result', '无')}\n"
    f"消息:{data.get('message', '无')}\n"
)

if __name__ == "__main__":
    pass
