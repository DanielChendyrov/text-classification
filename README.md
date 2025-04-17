# text-classification

## Thiết lập gửi email báo cáo phân tích

Để hệ thống tự động gửi báo cáo phân tích qua email (hàng ngày, hàng tuần):

1. **Cấu hình SMTP và email nhận báo cáo**

```json
{
  "admin_emails": ["your_admin_email@gmail.com"],
  "smtp": {
    "host": "smtp.gmail.com",
    "port": 587,
    "user": "your_gmail_address@gmail.com",
    "password": "your_app_password",
    "use_tls": true
  },
  "daily_report_time": "08:00",
  "weekly_report_time": "Monday 08:00"
}
```

   - Mở file `config/report.json` và chỉnh sửa các trường sau:
     - **admin_emails**: Danh sách email nhận báo cáo.
     - **smtp**: Thông tin máy chủ gửi mail. Nếu dùng Gmail:
       - `host`: `smtp.gmail.com`
       - `port`: `587`
       - `user`: Địa chỉ Gmail của bạn
       - `password`: [App Password](https://myaccount.google.com/apppasswords) (không phải mật khẩu Gmail thông thường, xem hướng dẫn bên dưới)
       - `use_tls`: `true`
     - **daily_report_time**: Thời gian gửi báo cáo ngày (theo định dạng 24h, ví dụ: "08:00").
     - **weekly_report_time**: Thời gian gửi báo cáo tuần (ví dụ: "Monday 08:00").

2. **Cách lấy App Password cho Gmail**

   - Truy cập: <https://myaccount.google.com/security>
   - Bật xác minh 2 bước (2-Step Verification).
   - Vào mục "App Passwords" (<https://myaccount.google.com/apppasswords>).
   - Tạo mật khẩu ứng dụng mới cho "Mail".
   - Dùng mật khẩu này cho trường `password` trong config.

3. **Lưu ý bảo mật**

   - Không commit mật khẩu thật lên git.
   - Có thể dùng biến môi trường và nạp vào config nếu cần bảo mật hơn.

4. **Có thể chỉnh sửa file config/report.json bất cứ lúc nào, hệ thống sẽ tự động cập nhật cấu hình khi gửi báo cáo.**
