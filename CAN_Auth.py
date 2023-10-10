"""
File: CAN_Auth.py(校园网登录)
Author: eya46
Date: 2023/10/10 10:10
cron: 0 0/2 * * * ?
new Env('校园网登录');
Description:
自动检测并登录校园网，每两分钟执行一次。
变量：CAN_ACCOUNT,CAN_PASSWORD,CAN_ENCRYPT(账号,密码,是否为加密的密码true/false)
"""
from os import getenv
from time import sleep
from json import dumps, load, loads
from random import randint
from typing import Tuple
from urllib.parse import quote, urlparse
from urllib.request import urlopen, Request

from notify import send


def get_login_info() -> dict:
    return load(urlopen(Request(
        "http://10.2.10.19/eportal/InterFace.do?method=getOnlineUserInfo",
        method="POST"
    ),
        data=urlparse(urlopen("http://10.2.10.19").url).query.encode("utf-8")
    ))


def get_login_info_txt() -> str:
    info = get_login_info()
    ball_info = loads(info["ballInfo"])
    device_num = "未知"
    for i in ball_info:
        if i["type"] == "deviceNum":
            device_num = i["value"]
    return (
        f"用户信息:\n"
        f"--{info['userName']}[{info['userId']}]\n"
        f"--IP:{info['userIp']}\n"
        f"--MAC:{info['userMac']}\n"
        f"--Service:{info['service']}\n"
        f"--在线设备:{device_num}"
    )


def check_auth() -> bool:
    resp = urlopen("http://10.2.10.19")
    # http://10.2.10.19/eportal/./success.jsp?userIndex=***
    return "success.jsp" in resp.url


def get_user_index() -> str:
    resp = urlopen("http://10.2.10.19")
    if "eportal/index.jsp" in resp.url:
        return urlparse(resp.url).query.split("&")[0].split("=")[1]


def login(account: str, password: str, encrypt: str = "false") -> Tuple[bool, str]:
    pre_resp = urlopen("http://10.2.10.19")
    if "web.njpji.cn" not in pre_resp.url:
        return True, "已经认证"
    query = urlparse(
        urlopen("http://10.2.10.19").read().decode("gbk").strip()
        .replace("'</script>", "")
        .replace("<script>top.self.location.href='", "")
    ).query

    auth_resp = urlopen(
        Request(
            "http://10.2.10.19/eportal/InterFace.do?method=login",
            headers={
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)" +
                              " Chrome/117.0.0.0 Safari/537.36"
            },
            method="POST"
        ),
        data=dumps({
            "userId": account,
            "password": password,
            "service": "联通网服务",
            "queryString": quote(query),
            "operatorPwd": "",
            "operatorUserId": "",
            "validcode": "",
            "passwordEncrypt": encrypt  # 为true时需要RSA加密，网页登录抓包可以看到加密的密码
        }, ensure_ascii=False).encode("utf-8")
    )
    data: dict = load(auth_resp)
    return data.get("result", "false") != "false", data.get("message", "无message返回")


def main():
    if not (account := getenv("CAN_ACCOUNT")):
        return print("未设置账号:CAN_ACCOUNT")
    if not (password := getenv("CAN_PASSWORD")):
        return print("未设置密码:CAN_PASSWORD")
    # 是否为加密的密码
    encrypt = "true" if getenv("CAN_ENCRYPT") == "true" else "false"
    # 当场睡0~15s (￣o￣) . z Z
    sleep(randint(0, 15))
    if check_auth():
        return print(
            "已经认证"
            f"{get_login_info_txt()}"
        )
    res, msg = login(account, password, encrypt)
    if status := check_auth():
        msg = (
            f"认证结果:{res}\n消息:{msg}\n网络状态:{status}\n"
            f"{get_login_info_txt()}"
        )
        print(msg)
        send("校园网登录结果", msg)
    else:
        print(
            f"认证结果:{res}\n消息:{msg}\n网络状态:{status}"
        )


main()

if __name__ == '__main__':
    pass
