#!/usr/bin/env python3
import hashlib,sys
if len(sys.argv)!=2 or len(sys.argv[1])<16:
    raise SystemExit("usage: python tools/hash_manual_refresh_key.py 'a-long-random-secret-at-least-16-chars'")
print(hashlib.sha256(sys.argv[1].encode()).hexdigest())
