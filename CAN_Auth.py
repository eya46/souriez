"""
File: CAN_Auth.py(校园网登录)
Author: eya46
Date: 2023/10/10 10:10
cron: 12 2/1 * * * ?
new Env('校园网登录');
Description:
自动检测并登录校园网，每一分钟执行一次。
变量：CAN_ACCOUNT,CAN_PASSWORD,CAN_ENCRYPT(账号,密码,是否为加密的密码true/false)
"""
from json import load, loads
from os import getenv
from typing import Tuple
from urllib.parse import quote, urlparse, urlencode
from urllib.request import urlopen, Request

from notify import send

userIndex = None
query = None


def get_login_info() -> dict:
    global userIndex
    return load(urlopen(Request(
        "http://10.2.10.19/eportal/InterFace.do?method=getOnlineUserInfo",
        method="POST"
    ),
        data=(userIndex or urlparse(urlopen("http://10.2.10.19").url).query).encode("utf-8")
    ))


def get_login_info_txt() -> str:
    info = get_login_info()
    return (
        f"用户信息:\n"
        f"--{info['userName']}[{info['userId']}]\n"
        f"--IP:{info['userIp']}\n"
        f"--MAC:{info['userMac']}\n"
        f"--Service:{info['service']}"
    )


def check_network() -> bool:
    try:
        urlopen("https://www.baidu.com", timeout=2)
        return True
    except:
        return False


def login(account: str, password: str, encrypt: str = "false") -> Tuple[bool, str]:
    global userIndex, query
    if not query:
        query = urlparse(
            urlopen("http://10.2.10.19").read().decode("gbk").strip()
            .replace("'</script>", "")
            .replace("<script>top.self.location.href='", "")
        ).query
    data: dict = load(urlopen(
        Request(
            "http://10.2.10.19/eportal/InterFace.do?method=login",
            headers={
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)" +
                              " Chrome/117.0.0.0 Safari/537.36"
            },
            method="POST",
            data=urlencode({
                "userId": account,
                "password": password,
                "service": "联通网服务",
                "queryString": quote(query),
                "operatorPwd": "",
                "operatorUserId": "",
                "validcode": "",
                "passwordEncrypt": encrypt  # 为true时需要RSA加密，网页登录抓包可以看到加密的密码
            }).encode("utf-8")
        )
    ))
    if not userIndex:
        userIndex = "userIndex=" + data.get("userIndex", "")
    return (
        data.get("result", "false") != "false",
        data.get("message", "无message返回") or "登录成功"
    )


def main():
    global userIndex, query
    if not (account := getenv("CAN_ACCOUNT")):
        return print("未设置账号:CAN_ACCOUNT")
    if not (password := getenv("CAN_PASSWORD")):
        return print("未设置密码:CAN_PASSWORD")
    # 是否为加密的密码
    encrypt = "true" if getenv("CAN_ENCRYPT") == "true" else "false"

    if check_network():
        return print("网络正常")

    print("网络异常，正在检查是否登录...")

    resp = urlopen("http://10.2.10.19")
    if "success.jsp" in resp.url:
        return True, "已经认证"
    print("未登录，进行登录...")
    if "web.njpji.cn" in resp.url:
        query = urlparse(
            resp.read().decode("gbk").strip()
            .replace("'</script>", "")
            .replace("<script>top.self.location.href='", "")
        ).query

    res, msg = login(account, password, encrypt)
    txt = (
        f"认证结果:{res}\n消息:{msg}\n"
        f"{get_login_info_txt()}"
    )
    print(txt)
    print("-" * 20)
    print("发送通知...")
    send("校园网登录结果", txt)


main()
print("结束~")

if __name__ == '__main__':
    pass
