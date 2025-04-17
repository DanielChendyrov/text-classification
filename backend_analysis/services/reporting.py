import os
import json
import logging
from datetime import datetime, timedelta, date
import pandas as pd
import smtplib
from email.message import EmailMessage
from db.models import CrawledData
from db.database import SessionLocal

# Emotion categories (Vietnamese)
EMOTION_CATEGORIES = [
    "Tích cực", "Tiêu cực", "Trung lập", "Hài hước", "Phẫn nộ", "Bất ngờ", "Buồn bã"
]

logger = logging.getLogger("reporting")

CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config", "report.json"))

def load_report_config():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"[Config] Error loading report config: {e}")
        return {}

def extract_emotion(analysis_text):
    # Scan for known emotions in the analysis text
    for emotion in EMOTION_CATEGORIES:
        if emotion.lower() in (analysis_text or '').lower():
            return emotion
    return "Không xác định"

def get_report_data(period="day"):
    db = SessionLocal()
    try:
        now = datetime.now()
        if period == "day":
            start = datetime(now.year, now.month, now.day)
        elif period == "week":
            start = now - timedelta(days=now.weekday())
            start = datetime(start.year, start.month, start.day)
        else:
            raise ValueError("period must be 'day' or 'week'")
        records = db.query(CrawledData).filter(
            CrawledData.is_analyzed == True,
            CrawledData.analyze_success == True,
            CrawledData.analyzed_at >= start,
            CrawledData.analyzed_at <= now
        ).all()
        data = []
        for rec in records:
            emotion = extract_emotion(rec.analysis or "")
            data.append({
                "id": rec.id,
                "url": rec.url,
                "crawled_at": rec.crawled_at,
                "analyzed_at": rec.analyzed_at,
                "emotion": emotion,
                "analysis": rec.analysis
            })
        return data
    finally:
        db.close()

def emotion_statistics(data):
    stats = {cat: 0 for cat in EMOTION_CATEGORIES}
    for row in data:
        emo = row["emotion"]
        if emo in stats:
            stats[emo] += 1
        else:
            stats["Không xác định"] = stats.get("Không xác định", 0) + 1
    return stats

def make_excel(data, filename):
    df = pd.DataFrame(data)
    df.to_excel(filename, index=False)

def send_report_email(period="day"):
    config = load_report_config()
    emails = config.get("admin_emails", [])
    smtp_cfg = config.get("smtp", {})
    if not emails or not smtp_cfg:
        logger.error("[Report] Missing email or SMTP config.")
        return
    data = get_report_data(period)
    stats = emotion_statistics(data)
    now = datetime.now()
    if period == "day":
        subject = f"[Báo cáo phân tích tin tức] Tổng kết ngày {now.strftime('%d/%m/%Y')}."
        filename = f"bao_cao_phan_tich_{now.strftime('%Y%m%d')}.xlsx"
    else:
        subject = f"[Báo cáo phân tích tin tức] Tổng kết tuần {now.strftime('%d/%m/%Y')}."
        filename = f"bao_cao_phan_tich_tuan_{now.strftime('%Y%m%d')}.xlsx"
    make_excel(data, filename)
    # Compose email in Vietnamese
    body = f"""
Kính gửi Quản trị viên,

Dưới đây là thống kê cảm xúc các bài báo đã phân tích {'trong ngày' if period=='day' else 'trong tuần'}:
"""
    for emo in EMOTION_CATEGORIES:
        body += f"- {emo}: {stats.get(emo, 0)}\n"
    if "Không xác định" in stats:
        body += f"- Không xác định: {stats['Không xác định']}\n"
    body += f"\nTổng số bài báo đã phân tích thành công: {len(data)}\n"
    body += "\nFile đính kèm chứa chi tiết từng bài báo.\n\nTrân trọng."
    # Send email
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = smtp_cfg.get("user")
    msg["To"] = ", ".join(emails)
    msg.set_content(body)
    with open(filename, "rb") as f:
        msg.add_attachment(f.read(), maintype="application", subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename=filename)
    try:
        with smtplib.SMTP(smtp_cfg["host"], smtp_cfg["port"]) as server:
            if smtp_cfg.get("use_tls", True):
                server.starttls()
            server.login(smtp_cfg["user"], smtp_cfg["password"])
            server.send_message(msg)
        logger.info(f"[Report] Đã gửi email báo cáo {period} thành công.")
    except Exception as e:
        logger.error(f"[Report] Lỗi khi gửi email: {e}")
    finally:
        if os.path.exists(filename):
            os.remove(filename)
