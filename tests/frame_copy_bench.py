#!/usr/bin/env python3
"""Microbenchmark the old BytesIO WS serialization vs split zero-copy writes."""
import io, struct, time, tracemalloc
SIZE=4*1024*1024; LOOPS=128; payload=bytearray(b'x')*SIZE
def header(n):
    if n<126:return bytes((0x82,n))
    if n<65536:return struct.pack('!BBH',0x82,126,n)
    return struct.pack('!BBQ',0x82,127,n)
h=header(SIZE)
def stock():
    checksum=0
    for _ in range(LOOPS):
        b=io.BytesIO(); b.write(h); b.write(payload); frame=b.getvalue(); checksum^=len(frame)
    return checksum
class Sink:
    __slots__=('total',)
    def __init__(self):self.total=0
    def write(self,data):self.total+=len(data)
def direct():
    sink=Sink()
    for _ in range(LOOPS):sink.write(h);sink.write(payload)
    return sink.total
tracemalloc.start(); t=time.perf_counter(); stock(); old_t=time.perf_counter()-t; _,old_peak=tracemalloc.get_traced_memory(); tracemalloc.stop()
tracemalloc.start(); t=time.perf_counter(); total=direct(); new_t=time.perf_counter()-t; _,new_peak=tracemalloc.get_traced_memory(); tracemalloc.stop()
assert total==LOOPS*(SIZE+len(h))
print(f'frame-copy {LOOPS*SIZE/2**20:.0f}MiB: old={old_t:.4f}s peak={old_peak/2**20:.2f}MiB direct={new_t:.6f}s peak={new_peak/2**20:.3f}MiB payload-copy=0')
