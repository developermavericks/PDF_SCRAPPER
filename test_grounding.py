import urllib.request
import urllib.parse
from bs4 import BeautifulSoup

def get_grounded_article_snippets(headline):
    # Remove special chars
    clean_title = headline.replace('"', '').replace("'", "").strip()
    query = f"{clean_title} Parimatch 1Xbet Economic Times"
    
    bing_url = 'https://www.bing.com/search?q=' + urllib.parse.quote(query)
    req = urllib.request.Request(bing_url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9'
    })
    
    snippets = []
    try:
        html = urllib.request.urlopen(req, timeout=6).read().decode('utf-8', errors='ignore')
        soup = BeautifulSoup(html, 'html.parser')
        
        for li in soup.find_all('li', class_='b_algo'):
            txt = li.get_text(separator=' ', strip=True)
            if txt and len(txt) > 40:
                snippets.append(txt)
    except Exception as e:
        print("Bing search error:", e)
        
    return snippets

if __name__ == '__main__':
    headline = 'Govt left with a losing hand as offshore RMG sites find a cheat code'
    results = get_grounded_article_snippets(headline)
    print("Bing Grounding Snippets Count:", len(results))
    for i, s in enumerate(results[:5]):
        print(f"\n[Snippet {i+1}]: {s}")
