# speed_limit.py
# Token-bucket speed limiting + low-overhead batched usage accounting.

from __future__ import annotations

import asyncio
import time

from main import LINKS

_buckets: dict = {}

MIN_RATE = 1024
MIN_BURST = 64 * 1024
MAX_SLEEP = 0.25
MIN_SLEEP = 0.002


class _Bucket:
    __slots__ = ("rate", "capacity", "tokens", "last")

    def __init__(self, rate_bytes_per_sec: float):
        self.rate = float(max(rate_bytes_per_sec, MIN_RATE))
        self.capacity = max(self.rate, float(MIN_BURST))
        self.tokens = self.capacity
        self.last = time.monotonic()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self.last
        if elapsed > 0:
            self.last = now
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)

    async def _consume_slice(self, nbytes: float) -> None:
        while True:
            self._refill()
            if self.tokens >= nbytes:
                self.tokens -= nbytes
                return
            wait = (nbytes - self.tokens) / self.rate
            await asyncio.sleep(min(max(wait, MIN_SLEEP), MAX_SLEEP))

    async def consume(self, nbytes: int) -> None:
        remaining = float(nbytes)
        while remaining > 0:
            take = min(remaining, self.capacity)
            await self._consume_slice(take)
            remaining -= take


def _get_bucket(uuid: str, rate: int) -> _Bucket:
    target = max(float(rate), float(MIN_RATE))
    bucket = _buckets.get(uuid)
    if bucket is None or bucket.rate != target:
        bucket = _Bucket(rate)
        _buckets[uuid] = bucket
    return bucket


async def throttle(uuid: str, nbytes: int) -> None:
    if nbytes <= 0:
        return
    link = LINKS.get(uuid)
    if not link:
        return
    rate = int(link.get("speed_limit_bytes", 0) or 0)
    if rate > 0:
        await _get_bucket(uuid, rate).consume(nbytes)


def reset_bucket(uuid: str) -> None:
    _buckets.pop(uuid, None)


def prune_buckets() -> int:
    removed = 0
    for uid in list(_buckets):
        link = LINKS.get(uid)
        if not link or int(link.get("speed_limit_bytes", 0) or 0) <= 0:
            _buckets.pop(uid, None)
            removed += 1
    return removed


# ── QuotaGate ────────────────────────────────────────────────────────────────
# Unlimited-volume links can account in large batches. Metered links retain a
# smaller batch to bound temporary quota overshoot. Either profile still flushes
# on close, so final byte totals are exact.
QUOTA_MIN_BATCH = 64 * 1024
QUOTA_METERED_MAX_BATCH = 1024 * 1024
QUOTA_UNLIMITED_MAX_BATCH = 8 * 1024 * 1024
QUOTA_METERED_START = 64 * 1024
QUOTA_UNLIMITED_START = 512 * 1024
QUOTA_METERED_INTERVAL = 0.20
QUOTA_UNLIMITED_INTERVAL = 0.50
QUOTA_TIME_CHECK_EVERY = 32


class QuotaGate:
    """Batch usage checks while keeping a synchronous per-frame hot path.

    ``stage`` is intentionally non-async. WS calls it for every data frame and
    awaits ``commit`` only when a batch is actually ready. ``add`` preserves a convenient asynchronous compatibility API.
    """

    __slots__ = (
        "uuid",
        "pending",
        "last_check",
        "ok",
        "batch_bytes",
        "rate_ewma",
        "max_batch",
        "check_interval",
        "ticks",
        "_consume",
    )

    def __init__(self, uuid: str, consume):
        self.uuid = uuid
        self.pending = 0
        self.last_check = time.monotonic()
        self.ok = True
        self.rate_ewma = 0.0
        self.ticks = 0
        self._consume = consume

        link = LINKS.get(uuid) or {}
        metered = int(link.get("limit_bytes", 0) or 0) > 0
        if metered:
            self.batch_bytes = QUOTA_METERED_START
            self.max_batch = QUOTA_METERED_MAX_BATCH
            self.check_interval = QUOTA_METERED_INTERVAL
        else:
            self.batch_bytes = QUOTA_UNLIMITED_START
            self.max_batch = QUOTA_UNLIMITED_MAX_BATCH
            self.check_interval = QUOTA_UNLIMITED_INTERVAL

    def stage(self, nbytes: int) -> int:
        """Return 0 for the hot path, bytes to commit, or -1 when denied."""
        if not self.ok:
            return -1
        if nbytes <= 0:
            return 0

        self.pending += nbytes
        self.ticks += 1
        # Avoid even a monotonic clock call on most frames.
        if (
            self.pending < self.batch_bytes
            and self.ticks % QUOTA_TIME_CHECK_EVERY != 0
        ):
            return 0

        now = time.monotonic()
        elapsed = now - self.last_check
        if self.pending < self.batch_bytes and elapsed < self.check_interval:
            return 0

        amount, self.pending = self.pending, 0
        if elapsed > 0:
            instant_rate = amount / elapsed
            self.rate_ewma = (
                instant_rate
                if self.rate_ewma == 0
                else 0.75 * self.rate_ewma + 0.25 * instant_rate
            )
            target = int(self.rate_ewma * self.check_interval)
            self.batch_bytes = max(
                QUOTA_MIN_BATCH,
                min(self.max_batch, target or QUOTA_MIN_BATCH),
            )
        self.last_check = now
        return amount

    async def commit(self, amount: int) -> bool:
        if amount <= 0:
            return self.ok
        result = await self._consume(self.uuid, amount)
        self.ok = self.ok and result
        return self.ok

    async def add(self, nbytes: int) -> bool:
        amount = self.stage(nbytes)
        if amount < 0:
            return False
        if amount:
            return await self.commit(amount)
        return True

    async def flush(self) -> bool:
        if self.pending:
            amount, self.pending = self.pending, 0
            await self.commit(amount)
        return self.ok
