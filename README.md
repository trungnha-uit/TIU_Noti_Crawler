# Portal Notification Crawler

Tự động crawl thông báo từ nhiều nguồn công khai, lưu vào Supabase và gửi thông báo mới lên Discord mỗi ngày.

## Tính năng

- ✅ Crawl từ nhiều nguồn:
  - **portal.url/bai-viet** - Cổng thông tin chính
  - **ctsv.url/thong-bao** - Phòng Công tác Sinh viên
  - **khtc.url/thongbao** - Phòng Kế hoạch Tài chính
- ✅ Lọc loại bỏ các danh mục không liên quan:
  - Liên thông CQ
  - Thông báo Nghỉ - Bù
- ✅ Lưu trữ vào Supabase (PostgreSQL)
- ✅ Phát hiện thông báo mới
- ✅ Gửi thông báo lên Discord webhook với định dạng đẹp
- ✅ Chạy tự động hàng ngày lúc 8h sáng (GMT+7)
- ✅ Tự động ẩn thông tin cá nhân (ID, email, số điện thoại)
- ✅ Hỗ trợ cấu hình URL crawl linh hoạt qua ENV

## Cài đặt

### 1. Fork/Clone repository này

```bash
git clone <repository-url>
cd School_Notification
```

### 2. Cài đặt dependencies (để test local)

```bash
pip install -r requirements.txt
```

### 3. Tạo Discord Webhook

1. Vào Discord server của bạn
2. Chọn kênh muốn nhận thông báo → Settings → Integrations → Webhooks
3. Tạo New Webhook
4. Copy Webhook URL

### 4. Tạo Supabase Database

1. Đăng ký tài khoản miễn phí tại [supabase.com](https://supabase.com)
2. Tạo project mới
3. Vào **SQL Editor** và chạy query:

```sql
CREATE TABLE public.Notification (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  title text,
  link text,
  date timestamp with time zone,
  categories text,
  featured boolean,
  source text,
  crawled_at timestamp with time zone,
  CONSTRAINT Notification_pkey PRIMARY KEY (id)
);
```

4. Lấy **Project URL** và **API Key** (anon/public) từ Settings > API

### 5. Cấu hình GitHub Secrets

Vào repository Settings → Secrets and variables → Actions → New repository secret

Thêm các secrets:

- **DISCORD_WEBHOOK_URL**: URL webhook Discord vừa tạo
- **SUPABASE_URL**: Project URL từ Supabase (dạng `https://xxx.supabase.co`)
- **SUPABASE_KEY**: API Key (anon/public) từ Supabase
- **PORTAL_BASE_URL**: Base URL nguồn 1
- **CTSV_BASE_URL**: Base URL nguồn 2
- **KHTC_BASE_URL**: Base URL nguồn 3

### 6. Kích hoạt GitHub Actions

1. Vào tab **Actions** trong repository
2. Chọn workflow "Daily Portal Notification Crawl"
3. Click **Enable workflow**

## Sử dụng

### Chạy tự động

GitHub Actions sẽ tự động chạy mỗi ngày lúc 8h sáng (GMT+7).

### Chạy thủ công

1. Vào tab **Actions**
2. Chọn workflow "Daily Portal Notification Crawl"
3. Click **Run workflow** → **Run workflow**

### Test trên máy local

Linux/Mac:

```bash
# Set environment variables
export DISCORD_WEBHOOK_URL="your_webhook_url"
export SUPABASE_URL="your_supabase_url"
export SUPABASE_KEY="your_supabase_key"
export PORTAL_BASE_URL="https://portal.url"
export CTSV_BASE_URL="https://ctsv.url"
export KHTC_BASE_URL="https://khtc.url"

# Run script
python crawl_notifications.py
```

Windows (PowerShell):

```powershell
$env:DISCORD_WEBHOOK_URL="your_webhook_url"
$env:SUPABASE_URL="your_supabase_url"
$env:SUPABASE_KEY="your_supabase_key"
$env:PORTAL_BASE_URL="https://portal.url"
$env:CTSV_BASE_URL="https://ctsv.url"
$env:KHTC_BASE_URL="https://khtc.url"

python crawl_notifications.py
```

## Cấu trúc project

```
.
├── .github/
│   └── workflows/
│       └── daily-crawl.yml      # GitHub Actions workflow
├── crawl_notifications.py       # Script crawl chính
├── requirements.txt             # Python dependencies
└── README.md
```

## Cách hoạt động

1. **Crawl từ nhiều nguồn**: Script tự động crawl từ 3 trang:
   - `portal.url/bai-viet` - Parse HTML từ trang Next.js
   - `ctsv.url/thong-bao` - Parse HTML từ trang Drupal
   - `khtc.url/thongbao` - Parse HTML từ trang Drupal
2. **Lọc danh mục**: Tự động loại bỏ "Liên thông CQ" và "Thông báo Nghỉ - Bù"
3. **So sánh với lịch sử**: Kiểm tra các bài viết mới chưa có trong Supabase
4. **Gửi Discord**: Chỉ gửi các thông báo mới lên Discord với format đẹp
5. **Lưu trữ**: Lưu thông báo mới vào Supabase database
6. **Ẩn thông tin**: Tự động ẩn các thông tin cá nhân như ID, email, số điện thoại

## Thông tin được crawl

- **Tiêu đề** bài viết
- **Link** đến bài viết chi tiết
- **Ngày đăng**
- **Danh mục** (Thông báo chung, CTSV, Học bổng, v.v.)
- **Trạng thái nổi bật** (featured badge)
- **Nguồn** (portal.url, ctsv.url, hoặc khtc.url)

## Lưu ý

- **Không cần đăng nhập**: Script crawl từ trang công khai nên không cần tài khoản
- **Bảo mật**: Script tự động ẩn các thông tin cá nhân trong nội dung
- **Tần suất crawl**: Mặc định chạy 1 lần/ngày. Có thể thay đổi cron schedule trong [daily-crawl.yml](.github/workflows/daily-crawl.yml)
- **Giới hạn Discord**: Mỗi lần chỉ gửi tối đa 10 thông báo mới để tránh spam
- **Lưu trữ**: Dữ liệu được lưu trong Supabase, KHÔNG có file JSON nào được commit lên GitHub

## Tùy chỉnh

### Thay đổi URL crawl

Thay đổi các URL bằng cách cập nhật GitHub Secrets:

- **PORTAL_BASE_URL**: Base URL nguồn 1
- **CTSV_BASE_URL**: Base URL nguồn 2
- **KHTC_BASE_URL**: Base URL nguồn 3

**Lưu ý**: Mỗi nguồn mới cần có hàm crawl riêng trong code để parse đúng cấu trúc HTML.

### Thay đổi danh mục loại bỏ

Edit [crawl_notifications.py](crawl_notifications.py), dòng ~20:

```python
self.excluded_categories = [
    "Liên thông CQ",
    "Thông báo Nghỉ - Bù",
    "Thông báo nghỉ - bù",
    # Thêm danh mục khác muốn bỏ qua
]
```

### Thay đổi giờ chạy

Edit file [.github/workflows/daily-crawl.yml](.github/workflows/daily-crawl.yml):

```yaml
schedule:
  # Chạy lúc 14:00 UTC (21:00 GMT+7)
  - cron: "0 14 * * *"
```

[Công cụ tạo cron expression](https://crontab.guru/)

### Thay đổi số lượng thông báo gửi Discord

Edit [crawl_notifications.py](crawl_notifications.py), dòng:

```python
for notif in notifications[:10]:  # Thay 10 thành số lượng mong muốn
```

### Crawl nhiều trang

Để crawl nhiều trang, sửa hàm `main()` trong [crawl_notifications.py](crawl_notifications.py):

```python
# Crawl trang 1 và 2
notifications_page1 = crawler.get_notifications(page=1)
notifications_page2 = crawler.get_notifications(page=2)
current_notifications = notifications_page1 + notifications_page2
```

## Xử lý lỗi thường gặp

### No notifications found

- Website có thể thay đổi HTML structure
- Cần inspect lại trang web và cập nhật CSS selectors trong code

### Discord webhook failed

- Kiểm tra DISCORD_WEBHOOK_URL có đúng không
- Webhook có thể bị xóa - tạo lại webhook mới

### Supabase connection error

- Kiểm tra SUPABASE_URL và SUPABASE_KEY có đúng không
- Đảm bảo table `Notification` đã được tạo theo đúng schema
- Kiểm tra Supabase project có đang active không

## License

MIT
