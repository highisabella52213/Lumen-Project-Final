#!/usr/bin/env python3
import hashlib,os,sys
from datetime import datetime,timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import proxy_repository as r
sample='''http://1.2.3.4:8080#Finland - 75%\nsocks5://u:p@1.2.3.4:8181#DE|Germany - 32%\nhttps://proxy.example:443#US - 91%\ninvalid\n'''
rows=r.parse_text(sample);assert [x.type for x in rows]==['http','socks5','https'];assert rows[0].code=='FI' and rows[0].flag=='🇫🇮' and rows[0].health==75;assert rows[1].country=='Germany' and rows[1].code=='DE'
pub=r.public(rows[1]);assert 'endpoint' not in pub and 'password' not in str(pub) and pub['safe'] is True
assert r.validate_url('socks5://u:p@host:1080')=='socks5://u:p@host:1080'
for bad in ('ftp://host:21','http://host','http://host:80/path'):
 try:r.validate_url(bad);raise AssertionError(bad)
 except ValueError:pass
assert r.REFRESH_SECONDS==7200
secret='ENV123-a-long-random-secret';digest=hashlib.sha256(secret.encode()).hexdigest();old_hash=r.MANUAL_REFRESH_TOKEN_SHA256;old={n:os.environ.get(n) for n in r.MANUAL_REFRESH_ENV_ALIASES};r.MANUAL_REFRESH_TOKEN_SHA256=digest
for n in r.MANUAL_REFRESH_ENV_ALIASES:os.environ.pop(n,None)
os.environ[r.MANUAL_REFRESH_ENV_NAME]=' “'+secret+'” ';assert r.manual_refresh_enabled() and r.manual_refresh_state()['enabled']
os.environ[r.MANUAL_REFRESH_ENV_NAME]='wrong';os.environ[r.MANUAL_REFRESH_ENV_ALIASES[1]]=digest.upper();assert r.manual_refresh_enabled()
os.environ[r.MANUAL_REFRESH_ENV_ALIASES[1]]='wrong';assert not r.manual_refresh_enabled()
old_id,old_secret=r.S3_ACCESS_KEY_ID,r.S3_SECRET_ACCESS_KEY;r.S3_ACCESS_KEY_ID='TESTKEY';r.S3_SECRET_ACCESS_KEY='TESTSECRET';req=r._signed_request(datetime(2026,9,2,8,0,0,tzinfo=timezone.utc));assert req.full_url=='https://s3.us-west-2.idrivee2.com/bt2/www-32k-ort-org-021/proxy.txt';auth=req.headers['Authorization'];assert 'Credential=TESTKEY/20260902/us-west-2/s3/aws4_request' in auth and 'TESTSECRET' not in auth
r.S3_ACCESS_KEY_ID,r.S3_SECRET_ACCESS_KEY=old_id,old_secret;r.MANUAL_REFRESH_TOKEN_SHA256=old_hash
for n,v in old.items():
 if v is None:os.environ.pop(n,None)
 else:os.environ[n]=v
print('private repository: parse=OK redaction=OK interval=2h manual-aliases=OK quotes=OK sigv4=OK')
