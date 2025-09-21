# Cloudflare Tunnel 設置指南

## 步驟 1: 下載 cloudflared

1. 前往 Cloudflare 官方下載頁面：
   https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/

2. 下載 Windows 版本 (64-bit)：
   直接下載連結: https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe

## 步驟 2: 安裝設置

```powershell
# 1. 創建目錄
mkdir C:\cloudflared

# 2. 將下載的檔案移動到該目錄並重命名
move cloudflared-windows-amd64.exe C:\cloudflared\cloudflared.exe

# 3. 添加到系統 PATH (以管理員身份運行)
setx PATH "%PATH%;C:\cloudflared" /M
```

## 步驟 3: 登入 Cloudflare

```bash
# 登入您的 Cloudflare 帳戶
cloudflared tunnel login
```

## 步驟 4: 創建 Tunnel

```bash
# 創建一個新的 tunnel (替換 YOUR_TUNNEL_NAME)
cloudflared tunnel create erp-tunnel

# 列出所有 tunnels
cloudflared tunnel list
```

## 步驟 5: 配置 Tunnel

創建配置文件 `C:\cloudflared\config.yml`:

```yaml
tunnel: <YOUR_TUNNEL_ID>
credentials-file: C:\Users\%USERNAME%\.cloudflared\<YOUR_TUNNEL_ID>.json

ingress:
  # 映射前端 (port 5174)
  - hostname: erp.yourdomain.com
    service: http://localhost:5174
  # 映射後端 API (port 5000)
  - hostname: api.erp.yourdomain.com
    service: http://localhost:5000
  # 必須的 catch-all 規則
  - service: http_status:404
```

## 步驟 6: 配置 DNS

在 Cloudflare Dashboard 中添加 CNAME 記錄：

```
Name: erp
Content: <YOUR_TUNNEL_ID>.cfargotunnel.com
Proxy: 已代理 (橙色雲朵)

Name: api.erp
Content: <YOUR_TUNNEL_ID>.cfargotunnel.com
Proxy: 已代理 (橙色雲朵)
```

## 步驟 7: 運行 Tunnel

```bash
# 測試運行
cloudflared tunnel run erp-tunnel

# 作為 Windows 服務安裝 (以管理員身份運行)
cloudflared service install
cloudflared service start
```

## 步驟 8: 驗證

訪問您的網域確認是否成功：
- https://erp.yourdomain.com (前端)
- https://api.erp.yourdomain.com/api/v1 (後端 API)

## 注意事項

1. 確保您的域名已經在 Cloudflare 管理
2. 防火牆不需要開放任何入站端口
3. 所有流量都通過 Cloudflare 的安全隧道
4. 自動獲得 SSL 證書

## 常用命令

```bash
# 查看 tunnel 狀態
cloudflared tunnel info erp-tunnel

# 查看日誌
cloudflared tunnel run erp-tunnel --loglevel debug

# 停止服務
cloudflared service stop

# 卸載服務
cloudflared service uninstall
```