import requests
from bs4 import BeautifulSoup
import browser_cookie3


def get_article_text(url: str, browser: str = "firefox") -> str:
    """
    Fetch article text from El País with browser cookies for paywall bypass.

    Args:
        url: URL of the El País article
        browser: Browser to extract cookies from ('chrome', 'firefox', 'edge', 'opera')

    Returns:
        Cleaned article text

    Raises:
        ValueError: If article text is too short (likely authentication failure)
        requests.RequestException: If network request fails
    """
    cookies = None

    try:
        if browser == "chrome":
            cookies = browser_cookie3.chrome(domain_name=".elpais.com")
        elif browser == "firefox":
            cookies = browser_cookie3.firefox(domain_name=".elpais.com")
        elif browser == "edge":
            cookies = browser_cookie3.edge(domain_name=".elpais.com")
        else:
            cookies = browser_cookie3.load(domain_name=".elpais.com")
    except Exception as e:
        print(f"Warning: Could not load {browser} cookies: {e}")
        print("Attempting to fetch article without authentication...")

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        response = requests.get(url, cookies=cookies, headers=headers, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Network error fetching article: {e}")
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
        except requests.RequestException as retry_e:
            raise requests.RequestException(f"Failed to fetch article after retry: {retry_e}")

    soup = BeautifulSoup(response.content, 'html.parser')

    article = soup.find('article')
    if not article:
        article = soup.find('div', class_='article-body')
    if not article:
        article = soup.find('div', {'id': 'article_body'})
    if not article:
        article = soup.find('main')

    if not article:
        raise ValueError("Could not find article content in HTML. The page structure may have changed.")

    for tag in article.find_all(['script', 'style', 'aside', 'nav', 'header', 'footer']):
        tag.decompose()

    text = article.get_text(separator=' ', strip=True)
    text = ' '.join(text.split())

    if len(text) < 500:
        print(f"Warning: Article text is only {len(text)} characters. Authentication may have failed.")
        print(f"Try a different browser with --browser option (chrome, firefox, edge)")

    return text
