# 防火牆設定指南

## Windows 防火牆設定

### 方法一：使用 PowerShell (管理員權限)
```powershell
# 開啟前端端口
New-NetFirewallRule -DisplayName "ERP Frontend" -Direction Inbound -Protocol TCP -LocalPort 5174 -Action Allow

# 開啟後端端口
New-NetFirewallRule -DisplayName "ERP Backend API" -Direction Inbound -Protocol TCP -LocalPort 5000 -Action Allow
```

### 方法二：使用命令提示字元 (管理員權限)
```cmd
# 開啟前端端口
netsh advfirewall firewall add rule name="ERP Frontend" dir=in action=allow protocol=TCP localport=5174

# 開啟後端端口
netsh advfirewall firewall add rule name="ERP Backend API" dir=in action=allow protocol=TCP localport=5000
```

### 方法三：使用 Windows Defender 防火牆圖形介面
1. 開啟 Windows Defender 防火牆
2. 點擊「進階設定」
3. 選擇「輸入規則」
4. 點擊「新增規則」
5. 選擇「連接埠」→ 下一步
6. 選擇「TCP」和「特定本機連接埠」
7. 輸入端口號碼（5174 和 5000 分別建立）
8. 選擇「允許連線」
9. 套用到所有網路設定檔
10. 給規則命名

## 啟動服務時的注意事項

### 後端啟動設定
確保後端監聽所有網路介面，不只是 localhost：

```python
# 在 backend/app.py 中
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)  # host='0.0.0.0' 很重要！
```

### 前端啟動設定
確保前端也監聽所有網路介面：

```bash
# 啟動前端時使用
cd frontend
npm run dev -- --host 0.0.0.0 --port 5174
```

或修改 `frontend/vite.config.ts`：
```typescript
export default defineConfig({
  server: {
    host: '0.0.0.0',
    port: 5174
  }
})
```

## 前端 API 端點設定

確保前端使用正確的後端 API 位址。修改 `frontend/.env` 或相關設定檔：

```env
# 使用您的電腦 IP 位址，不要用 localhost
VITE_API_BASE_URL=http://YOUR_COMPUTER_IP:5000
```

例如：
```env
VITE_API_BASE_URL=http://192.168.1.100:5000
```

## 測試連線

從遠端電腦測試：
1. 前端：瀏覽器開啟 `http://YOUR_IP:5174`
2. 後端：瀏覽器開啟 `http://YOUR_IP:5000`（應該看到 API 回應）

## 安全性建議

1. **限制 IP 範圍**：如果只需要特定 IP 連線，可以在防火牆規則中限制來源 IP
2. **使用 VPN**：考慮使用 VPN 而不是直接開放端口
3. **HTTPS**：正式環境應該使用 HTTPS 加密連線
4. **認證**：確保 API 有適當的認證機制（目前已有 JWT）