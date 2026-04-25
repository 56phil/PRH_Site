#!/usr/bin/env python3
"""
Publish a Hugo markdown post to Ghost as a newsletter email.
Usage: publish-to-ghost.py <path-to-post.md>
"""
import os, sys, re, json, base64, hmac, hashlib, time, urllib.request

GHOST_URL = os.environ.get('GHOST_API_URL', 'https://prhuffman.ghost.io')
GHOST_KEY = os.environ.get('GHOST_ADMIN_API_KEY', '')

if not GHOST_KEY or ':' not in GHOST_KEY:
    print("Error: GHOST_ADMIN_API_KEY not set (should be id:secret)", file=sys.stderr)
    sys.exit(1)

KEY_ID, SECRET = GHOST_KEY.split(':', 1)


def b64url(data):
    if isinstance(data, str):
        data = data.encode()
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('ascii')


# ---- Create JWT ----
iat = int(time.time())
header = b64url(json.dumps({"alg": "HS256", "kid": KEY_ID, "typ": "JWT"}))
payload = b64url(json.dumps({"iat": iat, "exp": iat + 300, "aud": "/admin/"}))
sig = b64url(hmac.new(SECRET.encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest())
jwt_token = f"{header}.{payload}.{sig}"

# ---- Read post ----
post_file = sys.argv[1]
with open(post_file) as f:
    raw = f.read()

m = re.match(r'^---\n(.*?)\n---\n?(.*)', raw, re.DOTALL)
if not m:
    print("Error: Could not parse frontmatter", file=sys.stderr)
    sys.exit(1)

fm, body = m.group(1), m.group(2)

# Extract title
title_match = re.search(r'^title:\s*(.+)$', fm, re.M)
if not title_match:
    print("Error: No title found", file=sys.stderr)
    sys.exit(1)
title = title_match.group(1).strip().strip('"').strip("'")

# ---- Convert markdown → HTML ----
try:
    import markdown
    md = markdown.Markdown(extensions=['extra', 'nl2br'])
    html = md.convert(body)
except ImportError:
    # Minimal fallback
    paras = [p.strip() for p in body.split('\n\n') if p.strip()]
    parts = []
    for p in paras:
        if p.startswith('> '):
            parts.append(f'<blockquote><p>{p[2:]}</p></blockquote>')
        elif p.startswith('## '):
            parts.append(f'<h2>{p[3:]}</h2>')
        elif p.startswith('# '):
            parts.append(f'<h1>{p[2:]}</h1>')
        elif p.startswith('**') and p.endswith('**'):
            parts.append(f'<p><strong>{p[2:-2]}</strong></p>')
        else:
            parts.append(f'<p>{p}</p>')
    html = '\n'.join(parts)

# ---- Build & send request ----
post_data = {
    "posts": [{
        "title": title,
        "html": html,
        "status": "published",
        "send_email_when_published": True,
    }]
}

req = urllib.request.Request(
    f"{GHOST_URL}/ghost/api/admin/posts/",
    data=json.dumps(post_data).encode(),
    headers={
        "Content-Type": "application/json",
        "Authorization": f"Ghost {jwt_token}",
    },
    method="POST",
)

try:
    resp = urllib.request.urlopen(req)
    result = json.loads(resp.read().decode())
    post = result['posts'][0]
    print(f"Ghost post published: {post.get('url', 'N/A')}")
    email_status = post.get('email', {})
    print(f"Email status: {email_status.get('status', 'unknown')}")
except urllib.error.HTTPError as e:
    print(f"HTTP Error {e.code}: {e.reason}", file=sys.stderr)
    print(e.read().decode(), file=sys.stderr)
    sys.exit(1)
