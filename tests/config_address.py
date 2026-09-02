#!/usr/bin/env python3
from pathlib import Path
import sys
from urllib.parse import parse_qs, urlsplit
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config_address import *

assert normalize_address(' Example.COM. ') == 'example.com'
assert normalize_address('[2606:4700::1]') == '2606:4700::1'
assert normalize_address('1.2.3.4') == '1.2.3.4'
assert address_kind('1.2.3.4') == 'ipv4'
assert address_kind('2606:4700::1') == 'ipv6'
assert address_kind('edge.example.com') == 'domain'
assert parse_address_list('a.com, 1.1.1.1\n[2606:4700::1];a.com') == ['a.com','1.1.1.1','2606:4700::1']
for bad in ('https://a.com','a.com:443','a.com/path','999.1.1.1','', 'a..com'):
    try: normalize_address(bad)
    except ValueError: pass
    else: raise AssertionError(('accepted bad address',bad))
for bad in ('1.1.1.1','[2606:4700::1]','https://sni.test'):
    try: normalize_sni(bad)
    except ValueError: pass
    else: raise AssertionError(('accepted bad sni',bad))
assert link_hosts('104.16.1.1','', 'app.example.com') == ('104.16.1.1','app.example.com')
assert link_hosts('edge.example.net','', 'app.example.com') == ('edge.example.net','edge.example.net')
assert link_hosts('104.16.1.1','front.example.org','app.example.com') == ('104.16.1.1','front.example.org')
assert authority_host('2606:4700::1') == '[2606:4700::1]'
print('config address + TLS SNI: ALL OK')
