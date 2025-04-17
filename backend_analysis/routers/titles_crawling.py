import newspaper
import csv
import time
from urllib.parse import urldefrag, urlparse

# Danh sách 8 website báo chính thống
NEWS_SITES = [
    "https://vnexpress.net",
    "https://tuoitre.vn",
    "https://thanhnien.vn",
    "https://vietnamnet.vn",
    "https://dantri.com.vn",
    "https://zingnews.vn",
    "https://plo.vn",  # Pháp Luật Online
    "https://laodong.vn",
    "https://nhandan.vn",
    "https://vtv.vn",
    "https://baochinhphu.vn",
    "https://vov.vn",
    "https://cand.com.vn",
    "https://qdnd.vn",
    "https://baophapluat.vn",
    "https://baogiaothong.vn",
    "https://nongnghiep.vn",
    "https://baoxaydung.com.vn",
    "https://suckhoedoisong.vn",
    "https://congthuong.vn",
    "https://daibieunhandan.vn",
    "https://baodautu.vn",
    "https://baotintuc.vn",
    "https://tienphong.vn",
    "https://kienthuc.net.vn",
    "https://infonet.vn",
    "https://vtcnews.vn",
    "https://nguoiduatin.vn"
]

MAX_ARTICLES_PER_SITE = 288
OUTPUT_CSV = "all_titles.csv"
MIN_WORD_COUNT = 50  # ngưỡng từ tối thiểu để coi là bài báo


def is_article(article, min_word_count=MIN_WORD_COUNT):
    og = article.meta_data.get('og', {})
    if og.get('type') == 'article':
        return True
    parsed = urlparse(article.url)
    # if parsed.path.endswith('.html'):
    #     return True
    text = article.text or ""
    if len(text.split()) >= min_word_count:
        return True
    return False


def crawl_titles(url, language='vi', max_articles=288):
    news_site = newspaper.build(url, language=language, memoize_articles=False)
    # Dùng set để track URLs đã xử lý (không tính fragment)
    seen = set()

    # Chỉ lấy 288 link đầu
    candidates = news_site.articles[:max_articles]
    titles = []
    print(f"[{url}] Tổng liên kết tìm được: {len(news_site.articles)} – sẽ thử crawl {len(candidates)} bài")

    for idx, article in enumerate(candidates, start=1):
        # 1. Loại bỏ fragment (#...) để normalize URL
        norm_url, _ = urldefrag(article.url)
        if norm_url in seen:
            # đã crawl url này rồi
            print(f"  ↳ Bỏ qua (duplicate): {article.url}")
            continue
        seen.add(norm_url)
        # gán lại article.url để các bước tiếp theo dùng URL chuẩn
        article.url = norm_url

        # 2. Download & parse
        try:
            article.download()
            article.parse()
            # 3. Chỉ lưu nếu đúng là bài báo
            if article.title and is_article(article):
                titles.append(article.title.strip())
            else:
                print(f"  ↳ Bỏ qua (không phải bài báo): {article.url}")
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
