import boto3
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
from weasyprint import HTML
from io import BytesIO

def extract_content_from_url(url):
    session = requests.Session()
    
    # Rotate through different user agents
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    ]
    
    for attempt in range(3):
        try:
            headers = {
                'User-Agent': user_agents[attempt % len(user_agents)],
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none'
            }
            
            if attempt > 0:
                interval = 3 + attempt * 2
                # nosemgrep: arbitrary-sleep
                time.sleep(interval)
            
            response = session.get(url, headers=headers, timeout=30, allow_redirects=True)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title = soup.find('title')
            title_text = title.get_text().strip() if title else "Amazon Help Page"
            title_text = title_text.replace(' - Amazon Customer Service', '').replace(' | Amazon.com', '')
            
            # Find main content with multiple selectors
            content = (soup.select_one('#help-content') or 
                      soup.select_one('.help-content') or 
                      soup.select_one('main') or 
                      soup.select_one('.a-container') or
                      soup.find('body'))
            
            if content:
                # Remove unwanted elements
                for tag in content(["script", "style", "nav", "footer", "header"]):
                    tag.decompose()

            return str(content)             
        except Exception as e:
            pass
    return None


def process_urls(urls):
    for url in urls:
        title, content = url[1], extract_content_from_url(url[0])
        if not title or not content:
            continue
        HTML(string=content).write_pdf(f"./kb_docs/{title}.pdf")
