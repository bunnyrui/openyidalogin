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
admin / 你在 license-server/.env 中设置的 ADMIN_PASSWORD
```

## 快速启动客户端开发版

```bash
cd electron-client
npm install
# Windows PowerShell 示例：
$env:AUTH_SERVER="http://服务器IP:8000/api/v1"
npm start
```

## 客户端打包前必须配置

编辑 `electron-client/package.json`：

```json
"config": {
  "authServer": "https://你的授权域名/api/v1",
  "storageSecret": "替换为随机长字符串"
}
```

开发环境可以继续用 `AUTH_SERVER` 环境变量覆盖；正式打包时如果未配置，客户端会拒绝激活，避免误连用户本机 `127.0.0.1`。

## 三平台客户端打包

```bash
cd electron-client
npm install

# macOS: dmg + zip，分别输出 x64 / arm64
npm run build:mac

# Windows: portable x64
npm run build:win

# Linux: AppImage + deb x64
npm run build:linux
```

跨平台交叉打包会受本机环境限制；最稳妥的发布方式是在 Windows、macOS、Linux 各自系统或 CI runner 上分别执行对应命令。

仓库已提供 GitHub Actions 工作流：`.github/workflows/build-clients.yml`。在仓库 Secrets 中配置 `AUTH_SERVER` 和 `CLIENT_STORAGE_SECRET` 后，可手动触发或推送 `v*` tag 自动构建三平台产物。

## 生产前必须做

```bash
./scripts/generate_rs256_keys.sh
```

然后重新部署服务端、重新打包客户端。不要把 `license-server/keys/private.pem` 发给客户，也不要使用 `.env.example` 里的占位密码。
