# Checklist Hướng Dẫn & Các Bước Cần Thực Hiện (MUSTDO.md)

Tài liệu này tổng hợp toàn bộ các thao tác thủ công bạn cần thực hiện để hoàn tất và nộp bài Day 26 - MCP Tools Integration.

---

## 📌 1. Nộp Bài Lên Codelabs VLearn

1. Kiểm tra lại trạng thái git và push code lên GitHub:
   ```bash
   git status
   git add .
   git commit -m "Complete Track 3 Day 26 MCP Tools Integration (Easy, Medium, Hard & Bonus)"
   git push origin main
   ```
2. Copy đường link repository GitHub cá nhân:
   ```
   https://github.com/NamKhanh2128/Day26-MCP-Tools-Integration-2A202601103-NguyenDucNamKhanh
   ```
3. Truy cập vào Codelabs VLearn: [https://codelabs.vlearn.dev/profile](https://codelabs.vlearn.dev/profile)
4. Dán link GitHub vào ô nộp bài của **Track 3 - Day 26 - MCP Tools Integration** và nhấn **Nộp bài**.

---

## 🤖 2. Đăng Ký MCP Server Vào Claude Code CLI

Nếu bạn đang sử dụng **Claude Code** trong terminal/PowerShell:

```bash
# Đăng ký server chế độ stdio
claude mcp add devops-intelligence -- python c:/Users/KHANH/Documents/GitHub/Day26-MCP-Tools-Integration-2A202601103-NguyenDucNamKhanh/my-mcp-server/server.py --transport stdio
```

Kiểm tra danh sách tool đã đăng ký trong Claude Code:
```bash
claude mcp list
```

---

## 💻 3. Cấu Hình Cho Claude Desktop (Nếu Sử Dụng App Desktop)

Mở file cấu hình Claude Desktop:
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

Thêm cấu hình sau:
```json
{
  "mcpServers": {
    "devops-intelligence": {
      "command": "python",
      "args": [
        "c:/Users/KHANH/Documents/GitHub/Day26-MCP-Tools-Integration-2A202601103-NguyenDucNamKhanh/my-mcp-server/server.py",
        "--transport",
        "stdio"
      ],
      "env": {
        "PYTHONUTF8": "1",
        "MCP_AUTH_TOKEN": "dev-token-secret123"
      }
    }
  }
}
```
Khởi động lại Claude Desktop để nhận diện bộ tools.

---

## 💬 4. Các Câu Lệnh Tự Nhiên Để Test Với AI

Hãy thử chat với AI để kiểm tra khả năng tự động gọi tool:

1. **Test Phân Tích Log & Chẩn Đoán Lỗi**:
   > *"Tìm giúp tôi các sự cố liên quan đến database timeout hoặc thanh toán trong file log và gợi ý giải pháp xử lý."*
   - AI sẽ tự động chọn `search_logs_v2` hoặc `get_recent_errors`, phân tích stack trace và trả lời.

2. **Test Tra Cứu Đơn Hàng & Doanh Thu**:
   > *"Cho tôi xem chi tiết đơn hàng ORD-2026-001 bao gồm khách hàng, các sản phẩm đã mua và mã vận đơn."*
   > *"Kiểm tra tổng doanh thu và tỷ lệ các trạng thái đơn hàng trong database hiện tại."*
   - AI sẽ tự động chọn `get_order_v2` và `get_database_summary`.

3. **Test Giám Sát Hệ Thống**:
   > *"Kiểm tra tình trạng CPU, RAM và dung lượng ổ đĩa của máy chủ hiện tại."*
   - AI sẽ tự động gọi `check_system_health`.

---

## 🔒 5. Bảo Vệ Thông Tin Mật (Secrets & Credentials)

- Không bao giờ commit file `.env` hoặc access token thật lên GitHub (đã được cấu hình trong `.gitignore`).
- Khi chạy trên môi trường mới hoặc máy khác trong mạng LAN, hãy copy từ `.env.example`:
  ```bash
  cp my-mcp-server/.env.example my-mcp-server/.env
  ```
