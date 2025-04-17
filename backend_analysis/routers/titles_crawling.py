import newspaper
import csv
import time
from urllib.parse import urlparse

# Danh sách 8 website báo chính thống
NEWS_SITES = [
    "https://vnexpress.net",
    "https://tuoitre.vn",
    "https://vtv.vn"
]

MAX_ARTICLES_PER_SITE = 288
OUTPUT_CSV = "all_titles.csv"
MIN_WORD_COUNT = 50  # ngưỡng từ tối thiểu để coi là bài báo


def is_article(article, min_word_count=MIN_WORD_COUNT):
    """
    Trả về True nếu article có vẻ là bài báo thật.
    """
    # 1. Kiểm tra og:type
    og = article.meta_data.get('og', {})
    if og.get('type') == 'article':
        return True

    # # 2. Kiểm tra URL kết thúc bằng .html
    # parsed = urlparse(article.url)
    # if parsed.path.endswith('.html'):
    #     return True

    # 3. Kiểm tra độ dài nội dung
    text = article.text or ""
    if len(text.split()) >= min_word_count:
        return True

    # Nếu cả 3 đều không đạt -> không phải bài báo
    return False


def crawl_titles(url, language='vi', max_articles=288):
    news_site = newspaper.build(url, language=language, memoize_articles=False)
    articles = news_site.articles[:max_articles]

    titles = []
    print(f"[{url}] Tổng liên kết tìm được: {len(news_site.articles)} – sẽ thử crawl {len(articles)} bài")

    for idx, article in enumerate(articles, start=1):
        try:
            article.download()
            article.parse()
            # chỉ lưu nếu là bài báo
            if article.title and is_article(article):
                titles.append(article.title.strip())
            else:
                print(f"  ↳ Bỏ qua (không phải bài báo) URL: {article.url}")
        except Exception as e:
            print(f"Lỗi tại bài {idx} ({url}): {e}")
        time.sleep(0.1)
    return titles


def save_all_titles(sites, output_csv, max_per_site):
    with open(output_csv, mode='w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Website", "STT", "Tiêu đề"])

        for site in sites:
            titles = crawl_titles(site, max_articles=max_per_site)
            for idx, title in enumerate(titles, start=1):
                writer.writerow([site, idx, title])
            print(f"Đã crawl xong {len(titles)} tiêu đề từ {site}\n")

    print(f"Hoàn tất! Đã lưu tiêu đề từ {len(sites)} trang vào {output_csv}")


if __name__ == "__main__":
    save_all_titles(NEWS_SITES, OUTPUT_CSV, MAX_ARTICLES_PER_SITE)
