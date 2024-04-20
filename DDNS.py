#!/usr/bin/python3
from http.client import HTTPSConnection
from json import loads, dumps
from pathlib import Path
from re import compile
from subprocess import Popen, PIPE
from traceback import print_stack
from typing import Any, Dict, List
from urllib.parse import urlencode

env = Path(__file__).parent / "data.json"

if not env.exists():
    print("data.json不存在")
    exit(-1)

with open(env) as f:
    data: dict = loads(f.read())

domains = data["domains"]
email = data["email"]
token = data["token"]

IPV4_REG = data["IPV4_REG"]
API = data["API"]


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
    zoneid = get_zone_id(domain)
    if not zoneid:
        raise Exception("invalid domain: [ %s ] " % domain)

    records = get_records(zoneid, name=domain, type=record_type)
    if records:  # update
        # https://api.cloudflare.com/#dns-records-for-a-zone-update-dns-record
        for record in records:
            if record['content'] != value:
                print(f"IP:{value} => 域名[{record_type}]:{domain}")
                request(
                    'PUT', '/' + zoneid + '/dns_records/' + record['id'],
                    type=record_type, content=value, name=domain, proxied=record['proxied']
                )
            else:
                print(f"IP:{value} == 域名[{record_type}]:{domain}")
    else:  # create
        # https://api.cloudflare.com/#dns-records-for-a-zone-create-dns-record
        print(f"IP:{value} >> 域名[{record_type}]:{domain}")
        request(
            'POST', '/' + zoneid + '/dns_records',
            type=record_type, name=domain, content=value, proxied=False
        )


def get_ipv4():
    return compile(IPV4_REG).search(
        Popen(["ifconfig"], stdout=PIPE).stdout.read().decode()
    ).group()


def main():
    ip = get_ipv4()
    for domain in domains:
        print(f"Domain: <{domain}> :")
        try:
            update_record(domain, ip)
        except:
            print_stack()
            print(f"{domain} 更新失败! ↑")


main()
