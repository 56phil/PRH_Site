import sys, json, os, re
from html.parser import HTMLParser

class MLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

def strip_tags(html):
    if not html:
        return ''
    s = MLStripper()
    s.feed(html)
    return s.get_data()

def slugify(text):
    text = re.sub(r'[^\w\s-]', '', text).strip().lower()
    return re.sub(r'[-\s]+', '-', text)

def convert_html_to_md(html):
    if not html:
        return ''
    html = re.sub(r'<h1[^>]*>(.*?)</h1>', r'# \1\n\n', html, flags=re.IGNORECASE|re.DOTALL)
    html = re.sub(r'<h2[^>]*>(.*?)</h2>', r'## \1\n\n', html, flags=re.IGNORECASE|re.DOTALL)
    html = re.sub(r'<h3[^>]*>(.*?)</h3>', r'### \1\n\n', html, flags=re.IGNORECASE|re.DOTALL)
    html = re.sub(r'<h4[^>]*>(.*?)</h4>', r'#### \1\n\n', html, flags=re.IGNORECASE|re.DOTALL)
    html = re.sub(r'<strong[^>]*>(.*?)</strong>', r'**\1**', html, flags=re.IGNORECASE|re.DOTALL)
    html = re.sub(r'<b[^>]*>(.*?)</b>', r'**\1**', html, flags=re.IGNORECASE|re.DOTALL)
    html = re.sub(r'<em[^>]*>(.*?)</em>', r'*\1*', html, flags=re.IGNORECASE|re.DOTALL)
    html = re.sub(r'<i[^>]*>(.*?)</i>', r'*\1*', html, flags=re.IGNORECASE|re.DOTALL)
    html = re.sub(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', r'[\2](\1)', html, flags=re.IGNORECASE|re.DOTALL)
    html = re.sub(r'<p[^>]*>(.*?)</p>', r'\1\n\n', html, flags=re.IGNORECASE|re.DOTALL)
    html = re.sub(r'<li[^>]*>(.*?)</li>', r'- \1\n', html, flags=re.IGNORECASE|re.DOTALL)
    html = re.sub(r'</?ul[^>]*>', '\n', html, flags=re.IGNORECASE)
    html = re.sub(r'<br\s*/?>', '\n', html, flags=re.IGNORECASE)
    html = re.sub(r'<blockquote[^>]*>(.*?)</blockquote>', r'> \1\n\n', html, flags=re.IGNORECASE|re.DOTALL)
    html = re.sub(r'<hr[^>]*>', '\n---\n', html, flags=re.IGNORECASE)
    html = re.sub(r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>', r'![](\1)', html, flags=re.IGNORECASE)
    html = re.sub(r'<[^>]+>', '', html)
    html = re.sub(r'\n{3,}', '\n\n', html)
    return html.strip()

d = json.load(open('/tmp/ghost_posts.json'))
posts = d.get('posts', [])
print(f'Total posts to extract: {len(posts)}')

base = os.path.expanduser('~/Developer/PRH_Site/content/posts')
os.makedirs(base, exist_ok=True)

with open(os.path.expanduser('~/Developer/PRH_Site/posts_list.txt'), 'w') as f:
    f.write('POSTS EXTRACTED FROM GHOST\n')
    f.write('=' * 60 + '\n')
    f.write('Delete files from content/posts/ to remove posts.\n')
    f.write('Then run: hugo server from the PRH_Site directory to preview.\n')
    f.write('=' * 60 + '\n\n')

    for i, p in enumerate(posts, 1):
        title = p.get('title', 'Untitled')
        slug = p.get('slug', slugify(title))
        md_content = convert_html_to_md(p.get('html', p.get('plaintext', '')))

        tags = p.get('tags', [])
        tag_list = [t['name'] for t in tags if t.get('name')]
        tag_str = ', '.join(tag_list) if tag_list else ''

        pub_date = p.get('published_at', '')[:10]

        filename = f'{slug}.md'
        filepath = os.path.join(base, filename)

        with open(filepath, 'w') as pf:
            pf.write(f'---\n')
            pf.write(f'title: "{title}"\n')
            if pub_date:
                pf.write(f'date: {pub_date}T00:00:00Z\n')
            if tag_str:
                pf.write(f'tags: [{tag_str}]\n')
            pf.write(f'---\n\n')
            pf.write(md_content)

        f.write(f'{i}. [{filename}] {title}\n')
        f.write(f'   Date: {pub_date} | Tags: {tag_str or "(none)"}\n\n')

print(f'\nAll {len(posts)} posts extracted to ~/Developer/PRH_Site/content/posts/')
print(f'Review list: ~/Developer/PRH_Site/posts_list.txt')
