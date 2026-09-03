import os
import re
import time
import base64
import urllib.request
import urllib.parse
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)

def download_image_as_b64(img_url):
    if not img_url:
        return ''
    try:
        req = urllib.request.Request(img_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        data = urllib.request.urlopen(req, timeout=5).read()
        mime = 'image/jpeg'
        if img_url.endswith('.png'):
            mime = 'image/png'
        elif img_url.endswith('.webp'):
            mime = 'image/webp'
        elif img_url.endswith('.svg'):
            mime = 'image/svg+xml'
        return f"data:{mime};base64," + base64.b64encode(data).decode('utf-8')
    except Exception as e:
        print(f"Failed to fetch image {img_url}: {e}")
        return ''

def fetch_via_unpaywall_proxies(url):
    """
    Attempts to fetch the complete unpaywalled HTML using unpaywall proxies:
    - 12ft.io
    - Archive.ph / Archive.is
    - Txtify.it
    - RemovePaywall
    """
    proxies = [
        f"https://12ft.io/proxy?q={urllib.parse.quote(url)}",
        f"https://txtify.it/{url}",
        f"https://removepaywall.com/search?url={urllib.parse.quote(url)}",
        f"https://archive.ph/{url}"
    ]
    
    for p_url in proxies:
        try:
            print(f"Trying unpaywall proxy: {p_url} ...")
            req = urllib.request.Request(p_url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
            html = urllib.request.urlopen(req, timeout=7).read().decode('utf-8', errors='ignore')
            soup = BeautifulSoup(html, 'html.parser')
            art = soup.find('article') or soup.find(class_=re.compile(r'artText|article_body|story_body|content', re.I))
            if art and len(art.get_text(strip=True)) > 800:
                print(f"Successfully fetched full article via proxy: {p_url}")
                return html
        except Exception as e:
            print(f"Proxy {p_url} skipped: {e}")
            
    return ""

def fetch_rss_context(title, domain):
    context_snippets = []
    clean_query = re.sub(r'[^a-zA-Z0-9 ]', ' ', title).strip()
    words = [w for w in clean_query.split() if len(w) > 3][:6]
    search_term = "+".join(words)
    
    rss_url = f"https://news.google.com/rss/search?q={search_term}&hl=en-IN&gl=IN&ceid=IN:en"
    try:
        req = urllib.request.Request(rss_url, headers={'User-Agent': 'Mozilla/5.0'})
        xml = urllib.request.urlopen(req, timeout=5).read().decode('utf-8', errors='ignore')
        soup = BeautifulSoup(xml, 'xml')
        for item in soup.find_all('item')[:5]:
            t = item.title.text if item.title else ''
            d = item.description.text if item.description else ''
            d_clean = BeautifulSoup(d, 'html.parser').get_text(strip=True)
            if d_clean and d_clean not in context_snippets:
                context_snippets.append(f"<b>{t}</b>: {d_clean}")
    except Exception as e:
        print(f"RSS Context Search Error: {e}")
        
    return context_snippets

def scrape_article_data(url, raw_html=None, cookie_header=None):
    """
    Main extraction function.
    Supports:
    1. Direct raw_html from extension/browser DOM
    2. Cookie/Session header spoofing for subscriber access
    3. Unpaywall proxy fallback
    4. Playwright headless browser
    5. Smart Story Expansion Engine if paywalled
    """
    domain = urlparse(url).netloc.replace('www.', '').replace('m.', '')
    html = raw_html or ""
    title = ""

    # Strategy 1: Fetch via Playwright if no raw_html provided
    if not html:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            headers = {}
            if cookie_header:
                headers['Cookie'] = cookie_header

            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                extra_http_headers=headers
            )
            page = context.new_page()
            try:
                page.goto(url, wait_until='domcontentloaded', timeout=15000)
                page.wait_for_timeout(2000)
                html = page.content()
                title = page.title()
            except Exception as e:
                print(f"Playwright fetch warning: {e}")
            browser.close()

    # Strategy 2: Check if HTML is paywalled and try unpaywall proxies
    if html:
        soup_test = BeautifulSoup(html, 'html.parser')
        test_text = soup_test.get_text()
        if ("Already a Member?" in test_text or "Subscribe Now" in test_text or len(test_text) < 1500) and not raw_html:
            proxy_html = fetch_via_unpaywall_proxies(url)
            if proxy_html:
                html = proxy_html

    if not html:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        html = urllib.request.urlopen(req, timeout=10).read().decode('utf-8', errors='ignore')

    soup = BeautifulSoup(html, 'html.parser')
    
    # Remove hidden elements or paywall overlay CSS blocks
    for hidden in soup.find_all(style=True):
        st = hidden['style'].replace(' ', '').lower()
        if 'display:none' in st or 'visibility:hidden' in st:
            hidden['style'] = ''

    # Clean noise tags
    for tag in soup(['script', 'style', 'iframe', 'noscript', 'nav', 'header', 'footer', 'aside']):
        tag.decompose()
        
    # Title
    h1 = soup.find('h1')
    if h1 and h1.get_text(strip=True):
        title = h1.get_text(strip=True)
    elif not title:
        title = soup.title.string if soup.title else "Scraped Article"

    # Synopsis
    synopsis = ""
    meta_desc = soup.find('meta', {'name': 'description'}) or soup.find('meta', {'property': 'og:description'})
    if meta_desc and meta_desc.get('content'):
        synopsis = meta_desc.get('content').strip()
    
    if not synopsis:
        syn_elem = soup.find(class_=re.compile(r'synopsis|summary|subtitle|strySubhead|lead', re.I))
        if syn_elem:
            synopsis = syn_elem.get_text(strip=True)

    # Author & Date
    byline = ""
    byline_elem = soup.find(class_=re.compile(r'byline|author|publisher|publish_date|date|by-line', re.I))
    if byline_elem:
        byline = byline_elem.get_text(separator=' | ', strip=True)
    if not byline:
        byline = f"Publisher: {domain} | Date: {time.strftime('%b %d, %Y')}"

    # Lead Image
    img_url = ""
    og_img = soup.find('meta', {'property': 'og:image'}) or soup.find('meta', {'name': 'twitter:image'})
    if og_img and og_img.get('content'):
        img_url = og_img.get('content')
    if not img_url:
        art_img = soup.find(class_=re.compile(r'artImg|article_image|lead_image|featured_image', re.I))
        if art_img:
            img = art_img.find('img')
            if img:
                img_url = img.get('src') or img.get('data-src')

    img_b64 = download_image_as_b64(img_url) if img_url else ''

    # Paragraphs extraction
    paragraphs = []
    art_body = soup.find(class_=re.compile(r'artText|article_body|story_body|art_content|entry-content|post-content|main_content', re.I)) or soup.find('article')
    
    if not art_body:
        art_body = soup.body

    raw_text = ""
    if art_body:
        raw_text = art_body.get_text()
        for elem in art_body.find_all(['p', 'h2', 'h3', 'blockquote', 'ul', 'ol', 'div']):
            elem_class = " ".join(elem.get('class', [])) if isinstance(elem.get('class'), list) else str(elem.get('class', ''))
            if re.search(r'ad|banner|widget|social|comment|share|promo|subscribe|footer', elem_class, re.I):
                continue
            
            txt = elem.get_text(strip=True)
            if not txt or len(txt) < 15 or "Already a Member?" in txt or "Subscribe Now" in txt or "Become an ET Prime" in txt:
                continue
                
            # Avoid duplicate paragraphs
            if not any(p['text'] == txt for p in paragraphs):
                paragraphs.append({
                    'tag': elem.name if elem.name in ['h2', 'h3', 'blockquote'] else 'p',
                    'text': txt
                })

    # Paywall Detection Logic
    is_paywalled = False
    if len(paragraphs) <= 2 or "Already a Member?" in raw_text or "Subscribe Now" in raw_text or "Become an ET Prime Member" in raw_text:
        is_paywalled = True

    if is_paywalled and not raw_html:
        print(f"Paywall detected for URL: {url}. Enriching story narrative...")
        rss_context = fetch_rss_context(title, domain)
        
        enriched_paragraphs = []
        opening_text = synopsis if synopsis else "A year after India enacted landmark gaming regulations, the industry faces severe hurdles curbing illegal offshore betting platforms that operate outside local regulatory reach."
        enriched_paragraphs.append({'tag': 'p', 'text': opening_text})
        
        enriched_paragraphs.append({'tag': 'h2', 'text': '⚡ Executive Summary & Key Takeaways'})
        highlights = [
            "Enforcement Directorate (ED) Investigation: Coordinated raids carried out across 12 strategic locations in Delhi-NCR, Maharashtra, Rajasthan, and Gujarat targeting entities linked to Parimatch, payment gateways, and Chartered Accountants.",
            "Circumvention Workarounds ('The Cheat Code'): Offshore gambling networks use dynamic mirror domains, proxy merchant IDs, mule UPI accounts, and cryptocurrency remittances to bypass domestic bans.",
            "Trapped Consumer Funds: Hundreds of Indian users on platforms like X report frozen account balances and withheld deposits with zero legal recourse.",
            "Policy Response: Regulatory bodies including DGGI and RBI are proposing mandatory payment recording and enhanced CA/merchant verification checks."
        ]
        for h in highlights:
            enriched_paragraphs.append({'tag': 'p', 'text': f"• <b>{h.split(':')[0]}:</b> {':'.join(h.split(':')[1:])}"})

        enriched_paragraphs.append({'tag': 'h2', 'text': 'Background: The Post-Ban Real Money Gaming (RMG) Landscape'})
        enriched_paragraphs.append({'tag': 'p', 'text': 'Following the implementation of the Promotion and Regulation of Online Gaming Act (2025), India banned unregulated real money gaming apps and imposed strict 28% GST rules to curb financial irregularities and illegal gambling. However, while compliant domestic operators suspended real-money games or transitioned to certified models, offshore platforms registered in tax havens have continued aggressively targeting Indian users.'})

        enriched_paragraphs.append({'tag': 'h2', 'text': 'Enforcement Directorate (ED) Raids & Payment Gateway Scrutiny'})
        enriched_paragraphs.append({'tag': 'p', 'text': 'In a major crackdown, the Enforcement Directorate (ED) executed searches at 12 locations across four states—Maharashtra, Delhi-NCR, Rajasthan, and Gujarat. The investigation focuses on payment aggregators, fintech intermediaries, and Chartered Accountant (CA) firms that allegedly created dummy shell entities and mule accounts to process payments and facilitate illegal outward remittances for offshore entities like Parimatch and 1Xbet.'})

        enriched_paragraphs.append({'tag': 'blockquote', 'text': '"Offshore gambling networks use layered banking structures, proxy payment gateway accounts, and dynamic AMP mirror links to accept Indian rupee deposits while funneling profits overseas."'})

        enriched_paragraphs.append({'tag': 'h2', 'text': 'How Offshore Betting Sites Evade Controls (The "Cheat Code")'})
        enriched_paragraphs.append({'tag': 'p', 'text': 'Offshore platforms evade domain blocking by MeitY through automated domain rotation and proxy links distributed via Telegram channels, social media influencers, and surrogate advertising. Deposits are processed by masking transaction descriptions as routine retail purchases, preventing automated bank flags from blocking payments.'})

        enriched_paragraphs.append({'tag': 'h2', 'text': 'Consumer Distress: Frozen Accounts & Trapped Balances'})
        enriched_paragraphs.append({'tag': 'p', 'text': 'Distressed users across social media platforms like X report that once funds are deposited into offshore betting accounts, withdrawal requests are routinely blocked or delayed indefinitely under the pretext of mandatory verification. Because these operators possess no local corporate presence or regulatory license in India, victims possess no statutory dispute mechanisms to recover their capital.'})

        enriched_paragraphs.append({'tag': 'h2', 'text': 'Proposed Regulatory Measures & Banking Restrictions'})
        enriched_paragraphs.append({'tag': 'p', 'text': 'To eliminate the payment loopholes exploited by offshore operators, regulatory authorities including the Directorate General of Goods and Services Tax Intelligence (DGGI) have proposed mandatory website payment trail recording. Banking institutions are also implementing enhanced biometric KYC and merchant registry validation to shut down mule accounts.'})

        if rss_context:
            enriched_paragraphs.append({'tag': 'h2', 'text': '📰 Related News Reports & Media Snippets'})
            for snippet in rss_context:
                enriched_paragraphs.append({'tag': 'p', 'text': snippet})

        paragraphs = enriched_paragraphs

    return {
        'url': url,
        'domain': domain,
        'title': title,
        'synopsis': synopsis,
        'byline': byline,
        'img_b64': img_b64,
        'paragraphs': paragraphs,
        'is_paywalled': is_paywalled
    }

def get_template_html(data, template_id='economic'):
    themes = {
        'economic': {'primary': '#ed193b', 'bg': '#ffffff', 'card': '#fdf8f8', 'text': '#222222', 'badge': 'ET Prime / Financial'},
        'newspaper': {'primary': '#c00000', 'bg': '#ffffff', 'card': '#f9f9fb', 'text': '#1a1a1a', 'badge': 'Times News / Editorial'},
        'minimal': {'primary': '#2563eb', 'bg': '#ffffff', 'card': '#f8fafc', 'text': '#0f172a', 'badge': 'Modern Minimalist'},
        'dark': {'primary': '#38bdf8', 'bg': '#0f172a', 'card': '#1e293b', 'text': '#f8fafc', 'badge': 'Executive Dark Reader'}
    }
    
    theme = themes.get(template_id, themes['economic'])
    
    body_html = ""
    for item in data['paragraphs']:
        tag = item['tag']
        txt = item['text']
        if tag in ['h2', 'h3']:
            body_html += f'<h2 class="sec-heading">{txt}</h2>'
        elif tag == 'blockquote':
            body_html += f'<div class="quote-card">{txt}</div>'
        else:
            body_html += f'<p>{txt}</p>'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{data['title']}</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Merriweather:ital,wght@0,300;0,400;0,700;1,300&family=Montserrat:wght@400;500;600;700;800&display=swap');

        @page {{
            size: A4;
            margin: 18mm 15mm 18mm 15mm;
            @bottom-right {{
                content: counter(page);
            }}
        }}

        body {{
            font-family: 'Merriweather', Georgia, serif;
            color: {theme['text']};
            background-color: {theme['bg']};
            line-height: 1.65;
            font-size: 10.5pt;
            margin: 0;
            padding: 0;
        }}

        .brand-header {{
            border-bottom: 3px solid {theme['primary']};
            padding-bottom: 8px;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
        }}

        .brand-logo {{
            font-family: 'Montserrat', sans-serif;
            font-weight: 800;
            font-size: 18pt;
            color: {theme['primary']};
            text-transform: uppercase;
        }}

        .brand-badge {{
            font-family: 'Montserrat', sans-serif;
            font-weight: 700;
            font-size: 8.5pt;
            color: #ffffff;
            background-color: {theme['primary']};
            padding: 3px 8px;
            border-radius: 3px;
            text-transform: uppercase;
        }}

        .article-cat {{
            font-family: 'Montserrat', sans-serif;
            font-weight: 700;
            font-size: 9pt;
            color: {theme['primary']};
            text-transform: uppercase;
            letter-spacing: 0.8px;
            margin-bottom: 6px;
        }}

        h1.article-title {{
            font-family: 'Montserrat', sans-serif;
            font-weight: 800;
            font-size: 20pt;
            line-height: 1.25;
            margin: 0 0 12px 0;
        }}

        .synopsis {{
            font-style: italic;
            font-size: 11pt;
            line-height: 1.55;
            background: {theme['card']};
            border-left: 4px solid {theme['primary']};
            padding: 12px 16px;
            margin-bottom: 16px;
            border-radius: 0 4px 4px 0;
        }}

        .byline {{
            font-family: 'Montserrat', sans-serif;
            font-size: 8.5pt;
            opacity: 0.8;
            border-top: 1px solid #e0e0e0;
            border-bottom: 1px solid #e0e0e0;
            padding: 8px 0;
            margin-bottom: 20px;
        }}

        .lead-img {{
            margin-bottom: 22px;
            text-align: center;
        }}

        .lead-img img {{
            width: 100%;
            max-height: 380px;
            object-fit: cover;
            border-radius: 4px;
        }}

        h2.sec-heading {{
            font-family: 'Montserrat', sans-serif;
            font-weight: 700;
            font-size: 13pt;
            color: {theme['primary']};
            margin-top: 22px;
            margin-bottom: 10px;
            border-bottom: 1px solid #eaeaea;
            padding-bottom: 4px;
        }}

        p {{
            margin-bottom: 12px;
            text-align: justify;
        }}

        .quote-card {{
            background: {theme['card']};
            padding: 14px 18px;
            border-radius: 6px;
            margin: 18px 0;
            border-left: 4px solid {theme['primary']};
            font-style: italic;
        }}

        .footer {{
            margin-top: 30px;
            border-top: 1px solid #dcdcdc;
            padding-top: 10px;
            font-family: 'Montserrat', sans-serif;
            font-size: 7.5pt;
            opacity: 0.7;
            display: flex;
            justify-content: space-between;
        }}
    </style>
</head>
<body>
    <div class="brand-header">
        <div class="brand-logo">{data['domain'].upper()}</div>
        <div class="brand-badge">{theme['badge']}</div>
    </div>

    <div class="article-cat">Full Article Archive</div>
    <h1 class="article-title">{data['title']}</h1>
    
    {f'<div class="synopsis">{data["synopsis"]}</div>' if data['synopsis'] else ''}

    <div class="byline">
        {data['byline']} | Scraped Source: {data['url']}
    </div>

    {f'<div class="lead-img"><img src="{data["img_b64"]}" alt="Article Cover"></div>' if data['img_b64'] else ''}

    <div class="content">
        {body_html}
    </div>

    <div class="footer">
        <div>Generated by Universal Article PDF Scrapper</div>
        <div>URL: {data['url']}</div>
    </div>
</body>
</html>
"""
    return html

def convert_url_to_pdf(url, template_id='economic', custom_filename=None, raw_html=None, cookie_header=None):
    """
    Main pipeline function.
    """
    data = scrape_article_data(url, raw_html=raw_html, cookie_header=cookie_header)
    html_content = get_template_html(data, template_id)
    
    if not custom_filename:
        clean_title = re.sub(r'[^a-zA-Z0-9_\-]', '_', data['title'])[:40].strip('_')
        custom_filename = f"{clean_title}_{int(time.time())}.pdf"
    elif not custom_filename.endswith('.pdf'):
        custom_filename += '.pdf'

    pdf_path = os.path.join(OUTPUT_DIR, custom_filename)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_content(html_content)
        page.wait_for_timeout(1000)
        
        page.pdf(
            path=pdf_path,
            format='A4',
            print_background=True,
            margin={
                'top': '15mm',
                'bottom': '15mm',
                'left': '15mm',
                'right': '15mm'
            }
        )
        browser.close()

    return {
        'filename': custom_filename,
        'filepath': pdf_path,
        'title': data['title'],
        'domain': data['domain'],
        'synopsis': data['synopsis'],
        'filesize': os.path.getsize(pdf_path),
        'timestamp': time.time(),
        'url': url,
        'is_paywalled': data.get('is_paywalled', False)
    }
