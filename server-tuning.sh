#!/usr/bin/env bash
# Optional Linux host tuning for high-throughput WS. Run as root on a VPS.
# Containers such as Railway may reject sysctl; application fallback remains safe.
set -euo pipefail
sysctl -w net.core.default_qdisc=fq || true
sysctl -w net.ipv4.tcp_congestion_control=bbr || true
sysctl -w net.core.rmem_max=67108864 || true
sysctl -w net.core.wmem_max=67108864 || true
sysctl -w 'net.ipv4.tcp_rmem=4096 1048576 67108864' || true
sysctl -w 'net.ipv4.tcp_wmem=4096 1048576 67108864' || true
sysctl -w net.core.somaxconn=8192 || true
sysctl -w net.core.netdev_max_backlog=16384 || true
sysctl -w net.ipv4.tcp_fastopen=3 || true
sysctl -w net.ipv4.tcp_mtu_probing=1 || true
ulimit -n 1048576 2>/dev/null || true
printf 'CC: '; sysctl -n net.ipv4.tcp_congestion_control 2>/dev/null || true
printf 'Qdisc: '; sysctl -n net.core.default_qdisc 2>/dev/null || true
