# Cloudflare

```
cloudflare/
├── README.md           ← this file
└── tunnel-config.yaml  ← tunnel ingress rules (reserved)
```

## Purpose

Cloudflare Tunnel 相关配置。

## Current Status

当前未启用。生产环境采用 Caddy + Let's Encrypt（直连 HTTPS，80/443 端口开放）。

## When to Use

- 无法开放 80/443 端口
- 家宽 / NAT 环境
- 希望隐藏 VPS IP

## How to Enable

1. 取消 `docker-compose.yml` 中 `cloudflared` 服务的注释
2. 配置 `CF_TUNNEL_TOKEN` 环境变量
3. 调整 `tunnel-config.yaml` 中的 ingress 规则
