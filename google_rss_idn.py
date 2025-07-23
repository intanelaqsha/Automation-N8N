import feedparser
from datetime import datetime, timedelta
import time
import re

# --- CONFIGURATION ---
RSS_BASE = "https://news.google.com/rss/search?q={query}&hl=id&gl=ID&ceid=ID:id"

# Top 5 perusahaan sawit Indonesia
TOP_COMPANIES = ["Wilmar", "Sime Darby", "Musim Mas", "Astra Agro Lestari"]
ISSUES = [ "deforestasi", "konflik", "korupsi", "sengketa", "kriminalisasi", "masyarakat adat", "kebakaran", "polusi" ]
NGO = ["Mongabay", "Reuters", "mighty earth", "greenpeace", "Rainforest Action Network"]

DAYS_LIMIT = 3 

# --- FUNCTIONS ---
def fetch_news(query):
    url = RSS_BASE.format(query=query.replace(" ", "+"))
    return feedparser.parse(url).entries

def is_recent(entry, days=DAYS_LIMIT):
    if hasattr(entry, 'published_parsed') and entry.published_parsed:
        pub_date = datetime.fromtimestamp(time.mktime(entry.published_parsed))
        return pub_date >= datetime.now() - timedelta(days=days)
    return False

def normalize_title(title):
    words = re.findall(r'\w+', title.lower())
    return set(words)

def is_similar(title1, title2, min_common=4):
    # True jika ada >= min_common kata yang sama
    words1 = normalize_title(title1)
    words2 = normalize_title(title2)
    common = words1 & words2
    return len(common) >= min_common

def deduplicate(results):
    unique = []
    for r in results:
        duplicate_found = False
        for u in unique:
            if is_similar(r["title"], u["title"], min_common=3):
                duplicate_found = True
                break
        if not duplicate_found:
            unique.append(r)
    return unique

def search_and_collect(queries, label):
    results = []
    for q in queries:
        print(f"\n🔍 Mencari {label}: {q}")
        entries = fetch_news(q)
        for e in entries:
            if is_recent(e):
                results.append({
                    "title": e.get("title", ""),
                    "url": e.get("link", ""),
                    "published": e.get("published", "Unknown"),
                    "query": q
                })
        time.sleep(1)  # hindari spam request
    return results

# --- MAIN WORKFLOW ---
def main():
    all_results = []

    # Pass 1: Palm oil + issue
    palm_queries = [f"sawit {issue}" for issue in ISSUES]
    all_results.extend(search_and_collect(palm_queries, "palm_issue"))

    # Pass 2: Company + issue
    company_queries = [f"{company} {issue}" for company in TOP_COMPANIES for issue in ISSUES]
    all_results.extend(search_and_collect(company_queries, "company_issue"))

    # Pass 3: Palm oil + issue + NGO
    ngo_queries = [f"sawit {issue} {ngo}" for issue in ISSUES for ngo in NGO]
    all_results.extend(search_and_collect(ngo_queries, "palm_ngo"))

    # Deduplicate by URL & similar title
    final_results = deduplicate(all_results)
    print(f"\n✅ Ditemukan {len(final_results)} artikel unik dalam {DAYS_LIMIT} hari terakhir.\n")

    # Print results
    for idx, r in enumerate(final_results, 1):
        print(f"[{idx}] {r['title']}")
        print(f"   Terbit: {r['published']}")
        print(f"   URL: {r['url']}")
        print(f"   Pencarian: {r['query']}\n")

if __name__ == "__main__":
    main()
