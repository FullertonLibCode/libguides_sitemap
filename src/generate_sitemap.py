import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from urllib.parse import urljoin
from xml.dom import minidom
import time

# Function to fetch a webpage
def fetch_page(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Failed to fetch {url}: {e}")
        return None

# Function to extract navigation links from a page
def extract_nav_links(page_content, base_url):
    if not page_content:
        return set()
    soup = BeautifulSoup(page_content, 'lxml')  # Use lxml for HTML parsing
    # Look for <ul> with 'nav' and 'split-button-nav' in class
    nav = soup.find('ul', class_=lambda x: x and 'nav' in x and 'split-button-nav' in x)
    if not nav:
        # Fallback: try <nav> tag
        nav = soup.find('nav')
        if not nav:
            print(f"No navigation found for {base_url}")
            return set()
        print(f"Using <nav> fallback for {base_url}")
    
    links = set()
    for a_tag in nav.find_all('a', href=True):
        href = a_tag['href']
        full_url = urljoin(base_url, href)
        if full_url.startswith('https://libraryguides.fullerton.edu'):
            links.add(full_url)
    return links

# Function to generate sitemap XML
def generate_sitemap(urls):
    urlset = ET.Element('urlset', xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    for url in sorted(urls):
        url_element = ET.SubElement(urlset, 'url')
        loc = ET.SubElement(url_element, 'loc')
        loc.text = url
    
    rough_string = ET.tostring(urlset, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="  ")
    return pretty_xml

# Main process
def main():
    sitemap_url = "https://libraryguides.fullerton.edu/sitemap.xml"
    
    # Fetch sitemap
    sitemap_content = fetch_page(sitemap_url)
    if not sitemap_content:
        print("Failed to fetch sitemap")
        return
    
    # Parse sitemap XML with lxml
    soup = BeautifulSoup(sitemap_content, 'lxml-xml')  # Explicitly use lxml for XML
    urls = [loc.text for loc in soup.find_all('loc')]
    
    # Collect all navigation links
    all_nav_links = set()
    failed_pages = []
    for url in urls:
        print(f"Processing {url}")
        page_content = fetch_page(url)
        if page_content:
            nav_links = extract_nav_links(page_content, url)
            all_nav_links.update(nav_links)
        else:
            failed_pages.append(url)
        time.sleep(1)  # Avoid rate-limiting
    
    # Log failed pages
    if failed_pages:
        print(f"Failed to process {len(failed_pages)} pages: {failed_pages}")
    
    # Generate new sitemap
    new_sitemap = generate_sitemap(all_nav_links)
    
    # Write to file
    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write(new_sitemap)
    
    print(f"Generated new sitemap with {len(all_nav_links)} URLs")

if __name__ == "__main__":
    main()