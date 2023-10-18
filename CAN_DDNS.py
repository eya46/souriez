"""
File: CAN_DDNS.py(DDNS)
Author: eya46
Date: 2023/10/18 21:21
cron: 0 0 2 1/1 * ?
new Env('DDNS');
Description:
每天凌晨2点进行DDNS映射,把指定网卡的ip映射。
变量：CAN_NTCARD网卡名,CAN_DOMAIN域名
from:https://github.com/NewFuture/DDNS
"""

from os import getenv
from re import compile
from json import loads, dumps
from subprocess import Popen, PIPE
from http.client import HTTPSConnection
from typing import Any, Dict, List
from urllib.parse import urlencode
from traceback import print_stack

nt_card = getenv("DDNS_NTCARD")
domains = getenv("DDNS_DOMAIN", "").split(",")
email = getenv("DDNS_EMAIL")
token = getenv("DDNS_TOKEN")

IPV4_REG = r'((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])'
API = "api.cloudflare.com"


def request(method, action, param=None, **params):
    """
        发送请求数据
    """
    if param:
        params.update(param)

    params = dict((k, params[k]) for k in params if params[k] is not None)
    conn = HTTPSConnection(API)

    if method in ['PUT', 'POST', 'PATCH']:
        # 从public_v(4,6)获取的IP是bytes类型，在json.dumps时会报TypeError
        params['content'] = str(params.get('content'))
        params = dumps(params)
    else:  # (GET, DELETE) where DELETE doesn't require params in Cloudflare
        if params:
            action += '?' + urlencode(params)
        params = None
    headers = {
        "Content-type": "application/json",
        "X-Auth-Email": email,
        "X-Auth-Key": token
    }
    conn.request(method, '/client/v4/zones' + action, params, headers)
    response = conn.getresponse()
    res = response.read().decode('utf8')
    conn.close()
    if response.status < 200 or response.status >= 300:
        print('%s : error[%d]:%s' % (action, response.status, res))
        raise Exception(res)
    else:
        data = loads(res)
        if not data:
            raise Exception("Empty Response")
        elif data.get('success'):
            return data.get('result', [{}])
        else:
            raise Exception(data.get('errors', [{}]))


def get_zone_id(domain: str) -> str:
    """
        切割域名获取主域名ID(Zone_ID)
        https://api.cloudflare.com/#zone-list-zones
    """
    zoneid = None
    domain_slice = domain.split('.')
    index = 2
    # ddns.example.com => example.com; ddns.example.eu.org => example.eu.org
    while (not zoneid) and (index <= len(domain_slice)):
        zones = request('GET', '', name='.'.join(domain_slice[-index:]))
        zone = next((z for z in zones if domain.endswith(z.get('name'))), None)
        zoneid = zone and zone['id']
        index += 1
    return zoneid


def get_records(zoneid, **conditions) -> List[Dict[str, Any]]:
    """
           获取记录ID
           返回满足条件的所有记录[]
    """
    return request('GET', '/' + zoneid + '/dns_records', per_page=100, **conditions)


def update_record(domain, value, record_type="A"):
    """
    更新记录
    """
    print(f"IP:{value} => 域名[{record_type}]:{domain}")
    zoneid = get_zone_id(domain)
    if not zoneid:
        raise Exception("invalid domain: [ %s ] " % domain)

    records = get_records(zoneid, name=domain, type=record_type)
    if records:  # update
        # https://api.cloudflare.com/#dns-records-for-a-zone-update-dns-record
        for record in records:
            if record['content'] != value:
                request(
                    'PUT', '/' + zoneid + '/dns_records/' + record['id'],
                    type=record_type, content=value, name=domain, proxied=record['proxied']
                )
    else:  # create
        # https://api.cloudflare.com/#dns-records-for-a-zone-create-dns-record
        request(
            'POST', '/' + zoneid + '/dns_records',
            type=record_type, name=domain, content=value, proxied=False
        )


def get_ipv4():
    global nt_card

    return compile(IPV4_REG).search(
        Popen(["ifconfig", nt_card], stdout=PIPE).stdout.read().decode()
    ).group()


def main():
    ip = get_ipv4()
    for domain in domains:
        try:
            update_record(domain, ip)
        except:
            print_stack()
            print(f"{domain} 更新失败! ↑")


if nt_card and email and token and len(domains) > 0:
    main()
else:
    print("环境变量未正确配置或域名为空")
