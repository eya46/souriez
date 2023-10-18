## 版本
```
whyour/qinglong:2.16
```

## cron
```
11 11 1/11 * * ?
```

## 拉取
```bash
# 白名单 黑名单 依赖
# 用的代理为 https://ghproxy.com/
ql repo https://ghproxy.com/https://github.com/eya46/souriez.git "" "__|notify.py" "notify.py"
```

## 脚本

- [登录校园网](CAN_Auth.py)
- [自动注销校园网](CAN_Logout.py)
- [DDNS](CAN_DDNS.py)