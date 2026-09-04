# Hướng dẫn Setup Chi tiết

## Bước 1: Tạo Discord Webhook

### 1.1. Vào Discord Server
- Mở Discord desktop/web app
- Chọn server bạn muốn nhận thông báo

### 1.2. Tạo Webhook
1. Click chuột phải vào kênh text muốn nhận thông báo
2. Chọn **Edit Channel** (⚙️)
3. Vào tab **Integrations** ở sidebar bên trái
4. Click **Webhooks** → **New Webhook**
5. Đặt tên cho webhook (ví dụ: "Portal Notifications")
6. (Tùy chọn) Đổi avatar cho webhook
7. Click **Copy Webhook URL**
8. Lưu URL này lại (dạng: `https://discord.com/api/webhooks/123456789/abcdefg...`)

## Bước 2: Setup GitHub Repository

### 2.1. Fork hoặc Clone repo này
```bash
git clone https://github.com/your-username/School_Notification.git
cd School_Notification
```

### 2.2. Thêm GitHub Secret

1. Vào repository trên GitHub
2. Click tab **Settings** (phải có quyền admin)
3. Sidebar bên trái: **Secrets and variables** → **Actions**
4. Click **New repository secret**
5. Điền:
   - **Name**: `DISCORD_WEBHOOK_URL`
   - **Secret**: Paste webhook URL vừa copy
6. Click **Add secret**

### 2.3. Enable GitHub Actions

1. Vào tab **Actions**
2. Nếu Actions bị disable, click **I understand my workflows, go ahead and enable them**
3. Chọn workflow **Daily Portal Notification Crawl**
4. Click **Enable workflow** (nếu có)

## Bước 3: Test Thử

### 3.1. Chạy workflow thủ công
1. Vào tab **Actions**
2. Chọn workflow **Daily Portal Notification Crawl** ở sidebar trái
3. Click nút **Run workflow** (bên phải)
4. Chọn branch `main`
5. Click **Run workflow** (màu xanh)

### 3.2. Xem kết quả
- Workflow sẽ chạy trong ~30-60 giây
- Click vào run mới nhất để xem logs
- Nếu thành công, bạn sẽ thấy thông báo trong Discord channel

## Bước 4: Test Local (Tùy chọn)

### 4.1. Cài đặt Python dependencies
```bash
pip install -r requirements.txt
```

### 4.2. Chạy script
**Linux/Mac:**
```bash
export DISCORD_WEBHOOK_URL="your_webhook_url_here"
python crawl_notifications.py
```

**Windows (PowerShell):**
```powershell
$env:DISCORD_WEBHOOK_URL="your_webhook_url_here"
python crawl_notifications.py
```

**Windows (CMD):**
```cmd
set DISCORD_WEBHOOK_URL=your_webhook_url_here
python crawl_notifications.py
```

## Kết quả mong đợi

Khi chạy thành công, bạn sẽ thấy:

### Output trong console:
```
Fetching notifications from page 1...
Found 12 notifications
Found 12 new notifications
Sent to Discord!
Notifications saved!
```

### Discord message:
Mỗi thông báo mới sẽ xuất hiện dạng embed card với:
- ✅ Tiêu đề (clickable link)
- ✅ Ngày đăng
- ✅ Danh mục
- ✅ Badge "Nổi bật" (nếu có)
- ✅ Màu vàng cho bài nổi bật, xanh cho bài thường

## Xử lý lỗi

### Lỗi: "Missing required environment variable"
- **Nguyên nhân**: Chưa set DISCORD_WEBHOOK_URL
- **Giải pháp**: Kiểm tra lại bước 2.2

### Lỗi: "404 Not Found" khi gửi Discord
- **Nguyên nhân**: Webhook URL không đúng hoặc đã bị xóa
- **Giải pháp**: Tạo lại webhook và cập nhật secret

### Lỗi: "No notifications found"
- **Nguyên nhân**: Website thay đổi cấu trúc HTML
- **Giải pháp**: Cần cập nhật CSS selectors trong code

### Workflow chạy nhưng không có thông báo mới
- **Bình thường**: Có thể không có bài mới trong ngày
- **Lần đầu chạy**: Sẽ gửi 10 bài mới nhất
- **Lần sau**: Chỉ gửi bài chưa có trong `notifications.json`

## Tùy chỉnh nâng cao

### Thay đổi giờ chạy
Edit [.github/workflows/daily-crawl.yml](.github/workflows/daily-crawl.yml):

```yaml
schedule:
  # Chạy 2 lần mỗi ngày: 8h sáng và 5h chiều (GMT+7)
  - cron: '0 1 * * *'   # 8:00 GMT+7
  - cron: '0 10 * * *'  # 17:00 GMT+7
```

### Crawl nhiều trang
Edit [crawl_notifications.py](crawl_notifications.py), trong hàm `main()`:

```python
# Crawl 3 trang đầu tiên
all_notifications = []
for page in range(1, 4):
    print(f"Fetching page {page}...")
    notifs = crawler.get_notifications(page=page)
    all_notifications.extend(notifs)

current_notifications = all_notifications
```

### Thay đổi màu Discord embed
Edit [crawl_notifications.py](crawl_notifications.py), dòng ~120:

```python
"color": 13132095 if notif.get('featured') else 3447003,
#         ^^^^^^^^ vàng cho featured       ^^^^^^^^ xanh cho thường
```

[Color picker tool](https://www.spycolor.com/) để chọn màu khác.

## Hỗ trợ

Nếu gặp vấn đề:
1. Kiểm tra logs trong GitHub Actions
2. Test local để debug
3. Kiểm tra website có thay đổi cấu trúc không
4. Tạo issue trên GitHub với logs đầy đủ
