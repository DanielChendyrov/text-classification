import schedule
import time
import json
from config_handler import load_config
import requests
import psycopg2
import pandas as pd
import smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta

config = load_config()

db_conn = psycopg2.connect(
    dbname='crawl4ai_db',
    user='user',
    password='pass',
    host='postgres_db'
)


def crawl_and_analyze():
    with open('config.json') as cfg_file:
        cfg = json.load(cfg_file)

    cursor = db_conn.cursor()

    for site in cfg['websites']:
        urls_response = requests.post(
            'http://crawl4ai_service:8000/crawl',
            json={"url": site}
        ).json()

        for url in urls_response.get('urls', []):
            article_response = requests.post(
                'http://crawl4ai_service:8000/extract',
                json={"url": url}
            ).json()

            contents = article_response['content']
            if not any(keyword in contents for keyword in cfg['keywords']):
                continue

            summary_response = requests.post(
                'http://crawl4ai_service:8000/summarize',
                json={"content": contents, "language": "vi"}
            ).json()

            analysis_response = requests.post(
                'http://crawl4ai_service:8000/analyze',
                json={"content": contents, "language": "vi"}
            ).json()

            cursor.execute("""
                INSERT INTO articles (url, contents, analysis, is_analyzed, analyzed_at)
                VALUES (%s, %s, %s, TRUE, NOW())
                ON CONFLICT (url) DO NOTHING;
            """, (url, summary_response['summary'], analysis_response['analysis']))
            db_conn.commit()


schedule.every(config['crawl_interval_seconds']).seconds.do(crawl_and_analyze)


def send_email_report(period="daily"):
    now = datetime.now()
    start_time = now - timedelta(days=1) if period == "daily" else now - timedelta(days=7)

    df = pd.read_sql("""
        SELECT * FROM articles WHERE is_analyzed = TRUE AND analyzed_at >= %s;
    """, db_conn, params=(start_time,))

    positive_urls = df[df['analysis'].str.contains("tích cực")]['url']
    negative_urls = df[df['analysis'].str.contains("tiêu cực")]['url']

    msg = EmailMessage()
    msg['Subject'] = f"{period.capitalize()} Article Analysis Report"
    msg['From'] = config['smtp']['user']
    msg['To'] = ', '.join(config['email_recipients'])
    msg.set_content(f"""
        Total Analyzed: {len(df)}
        Positive Articles: {len(positive_urls)}
        Negative Articles: {len(negative_urls)}
    """)

    # Attach CSV files
    pos_csv = positive_urls.to_csv(index=False).encode()
    neg_csv = negative_urls.to_csv(index=False).encode()

    msg.add_attachment(pos_csv, maintype='text', subtype='csv', filename='positive_articles.csv')
    msg.add_attachment(neg_csv, maintype='text', subtype='csv', filename='negative_articles.csv')

    with smtplib.SMTP(config['smtp']['host'], config['smtp']['port']) as smtp:
        smtp.starttls()
        smtp.login(config['smtp']['user'], config['smtp']['password'])
        smtp.send_message(msg)


schedule.every().day.at(config['email_report_time_daily']).do(send_email_report, "daily")
schedule.every().sunday.at(config['email_report_time_daily']).do(send_email_report, "weekly")

# Main loop
while True:
    schedule.run_pending()
    time.sleep(1)
