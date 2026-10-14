"""Build the static pages: wraps each _src/pages/*.html body in _src/layout.html.

usage: python _src/build.py
Output goes to the repo root (index.html, about-us/index.html, ...), which the
SiteGround deploy uploads as-is. _src/ itself is not deployed.
"""
import hashlib
import html
import json
import pathlib
import re
from datetime import date

SRC = pathlib.Path(__file__).resolve().parent
ROOT = SRC.parent
SIGNUP = 'https://belllaundryanddrycleaning.smrtapp.com/customer/'

PAGES = {
    'home': {
        'path': '/',
        'title': 'Dry Cleaners in Spartanburg, SC | Bell Laundry & Cleaners',
        'description': 'Choose Bell Laundry & Cleaners in Spartanburg, SC, for dry cleaning, laundry, alterations, and pickup and delivery. Caring for your clothing since 1941.',
        'preload': '/assets/img/hero-pickup.webp',
    },
    'about': {
        'path': '/about-us/',
        'title': 'About Bell Laundry & Cleaners | Serving Since 1941',
        'description': 'Learn about Bell Laundry & Cleaners, a family-owned cleaner established in Spartanburg, SC, in 1941, offering quality garment care and personal service.',
    },
    'contact': {
        'path': '/contact/',
        'title': 'Contact Bell Laundry & Cleaners | Spartanburg, SC',
        'description': 'Contact Bell Laundry & Cleaners in Spartanburg, SC, for dry cleaning, laundry, alterations, and pickup and delivery. Call or send our team a message today.',
    },
    'blog': {
        'path': '/blog/',
        'title': 'Garment Care Blog | Bell Laundry & Cleaners',
        'description': 'Explore clothing care tips, laundry advice, and guidance for everyday garments and special pieces from Bell Laundry & Cleaners in Upstate South Carolina.',
    },
    'media': {
        'path': '/media-room/',
        'title': 'Media Room | Bell Laundry & Cleaners',
        'description': 'Company news and updates from Bell Laundry & Cleaners, established in Spartanburg in 1941. For media inquiries, contact our team at 864-583-8668.',
    },
    'work': {
        'path': '/work-with-us/',
        'title': 'Work With Us | Bell Laundry & Cleaners, Spartanburg',
        'description': 'Interested in joining Bell Laundry & Cleaners in Spartanburg, SC? Share your experience, availability, and resume through our online employment inquiry form.',
    },
}

NAV = [
    ('home', 'Home', '/'),
    ('about', 'About', '/about-us/'),
    (None, 'Services', '/#services'),
    (None, 'Pickup & Delivery', '/#pickup'),
    ('blog', 'Blog', '/blog/'),
    ('contact', 'Contact', '/contact/'),
]

SCHEMA = {
    '@context': 'https://schema.org',
    '@type': 'DryCleaningOrLaundry',
    'name': 'Bell Laundry & Cleaners',
    'url': 'https://bellcleaners.com/',
    'telephone': '+1-864-583-8668',
    'email': 'darshan@bellcleaners.com',
    'foundingDate': '1941',
    'address': {
        '@type': 'PostalAddress',
        'streetAddress': '448 Marion Ave',
        'addressLocality': 'Spartanburg',
        'addressRegion': 'SC',
        'postalCode': '29306',
        'addressCountry': 'US',
    },
    'openingHoursSpecification': [
        {'@type': 'OpeningHoursSpecification', 'dayOfWeek': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'], 'opens': '07:30', 'closes': '18:00'},
        {'@type': 'OpeningHoursSpecification', 'dayOfWeek': 'Saturday', 'opens': '08:00', 'closes': '12:00'},
    ],
    'sameAs': ['https://www.facebook.com/Bell-Laundry-Cleaners-660812587439919/'],
}


def stamp(path):
    return hashlib.sha1(path.read_bytes()).hexdigest()[:8]


def icon(name):
    return f'<svg aria-hidden="true"><use href="#i-{name}"/></svg>'


def blog_cards():
    posts = json.loads((SRC / 'posts.json').read_text(encoding='utf-8'))
    out = []
    for i, p in enumerate(posts):
        d = date.fromisoformat(p['date'])
        nice = f'{d:%b} {d.day}, {d.year}'
        lead = ' is-lead' if i == 0 else ''
        out.append(f'''      <a class="post-card{lead}" href="{html.escape(p['link'])}" target="_blank" rel="noopener">
        <div class="thumb"><img src="/{p['image']}" width="900" height="600" alt="" loading="lazy"><span class="date">{icon('calendar')}{nice}</span></div>
        <div class="body">
          <h3>{html.escape(p['title'])}</h3>
          <p>{html.escape(p['excerpt'])}</p>
          <span class="link-arrow">Read Article {icon('arrow')}</span>
        </div>
      </a>''')
        if i == 0:
            out.append(f'''      <div class="ask-card">
        <span class="sparkle">{icon('sparkle')}</span>
        <span class="eyebrow">Ask Our Team</span>
        <h3 class="h3">Have a Garment Care Question?</h3>
        <p>Call 864-583-8668 to speak with our team about your cleaning needs.</p>
        <a class="btn btn-dark" href="tel:+18645838668">Call Our Team <span class="btn-ico">{icon('phone')}</span></a>
      </div>''')
    return '\n'.join(out)


def render(key, meta, layout, icons, versions):
    body = (SRC / 'pages' / f'{key}.html').read_text(encoding='utf-8')
    body = body.replace('{{blog_posts}}', blog_cards() if '{{blog_posts}}' in body else '')
    nav, nav_m = [], []
    for i, (k, label, href) in enumerate(NAV):
        cur = ' aria-current="page"' if k == key else ''
        nav.append(f'        <li><a href="{href}"{cur}>{html.escape(label)}</a></li>')
        nav_m.append(f'    <li style="--i:{i}"><a href="{href}"{cur}>{html.escape(label)}</a></li>')
    for j, (label, href) in enumerate([('Media Room', '/media-room/'), ('Work With Us', '/work-with-us/')]):
        nav_m.append(f'    <li style="--i:{len(NAV) + j}"><a href="{href}">{label}</a></li>')
    preload = ''
    if meta.get('preload'):
        preload = f'<link rel="preload" as="image" href="{meta["preload"]}" fetchpriority="high">'
    schema = ''
    if key == 'home':
        schema = '<script type="application/ld+json">' + json.dumps(SCHEMA, separators=(',', ':')) + '</script>'
    out = layout
    for k, v in {
        'title': html.escape(meta['title']),
        'description': html.escape(meta['description']),
        'path': meta['path'],
        'preload': preload,
        'schema': schema,
        'icons': icons,
        'nav': '\n'.join(nav),
        'nav_mobile': '\n'.join(nav_m),
        'content': body,
        'v_css': versions['css'],
        'v_js': versions['js'],
    }.items():
        out = out.replace('{{' + k + '}}', v)
    out = out.replace('{{signup}}', SIGNUP)
    out = re.sub(r'\{\{icon:([a-z-]+)\}\}', lambda m: icon(m.group(1)), out)
    left = re.findall(r'\{\{[^}]+\}\}', out)
    if left:
        raise SystemExit(f'{key}: unreplaced placeholders {left}')
    dest = ROOT / meta['path'].strip('/') / 'index.html' if meta['path'] != '/' else ROOT / 'index.html'
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(out, encoding='utf-8', newline='\n')
    print(f'built {dest.relative_to(ROOT).as_posix()}')


def main():
    layout = (SRC / 'layout.html').read_text(encoding='utf-8')
    icons = (SRC / 'icons.svg').read_text(encoding='utf-8').strip()
    versions = {
        'css': stamp(ROOT / 'assets' / 'css' / 'site.css'),
        'js': stamp(ROOT / 'assets' / 'js' / 'site.js'),
    }
    for key, meta in PAGES.items():
        render(key, meta, layout, icons, versions)


if __name__ == '__main__':
    main()
