# 宜搭自助登录工具 V2 最终版

本包按“服务端 / 客户端”分离：

- `license-server/`：FastAPI 授权服务端 + Web 管理后台
- `electron-client/`：Electron 宜搭自助登录客户端
- `docs/编译部署手册.md`：完整编译、部署、打包说明
- `scripts/generate_rs256_keys.sh`：重新生成 RS256 密钥

## V2 核心变化

- JWT 已升级为 **RS256 非对称签名**：服务端私钥签发，客户端只用公钥验签。
- 管理员密码加密已从 bcrypt 替换为 **pbkdf2_sha256**，规避 bcrypt 72 字节限制和 Python 3.12 兼容问题。
- 保留原始核心功能：宜搭内置登录、获取 Cookie、保存到桌面结果目录。
- 保留 Web 管理后台：创建卡密、启用/禁用、续期、解绑设备、日志查看。

## 快速启动服务端

```bash
cd license_product_source_final_v2
cp license-server/.env.example license-server/.env
sudo docker compose up -d --build
sudo docker logs -f license-server
```

访问：

```text
http://服务器IP:8000/admin
```

默认账号：

```text
admin / admin123456
```

## 快速启动客户端开发版

```bash
cd electron-client
npm install
# Windows PowerShell 示例：
$env:AUTH_SERVER="http://服务器IP:8000/api/v1"
npm start
```

## 生产前必须做

```bash
./scripts/generate_rs256_keys.sh
```

然后重新部署服务端、重新打包客户端。不要把 `license-server/keys/private.pem` 发给客户。
