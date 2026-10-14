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

from services_render import ICON as SERVICE_ICONS, SHORT as SHORT_NAMES, render_page as render_service

SRC = pathlib.Path(__file__).resolve().parent
ROOT = SRC.parent
SIGNUP = 'https://belllaundryanddrycleaning.smrtapp.com/customer/'

PAGES = {
    'home': {
        'path': '/',
        'title': 'Dry Cleaners in Spartanburg, SC | Bell Laundry & Cleaners',
        'description': 'Choose Bell Laundry & Cleaners in Spartanburg, SC, for dry cleaning, laundry, alterations, and pickup and delivery. Caring for your clothing since 1941.',
        'preload': '/assets/img/bags-bell.webp',
    },
    'about': {
        'path': '/about-us/', 'crumb': 'About Us',
        'title': 'About Bell Laundry & Cleaners | Serving Since 1941',
        'description': 'Learn about Bell Laundry & Cleaners, a family-owned cleaner established in Spartanburg, SC, in 1941, offering quality garment care and personal service.',
    },
    'contact': {
        'path': '/contact/', 'crumb': 'Contact',
        'title': 'Contact Bell Laundry & Cleaners | Spartanburg, SC',
        'description': 'Contact Bell Laundry & Cleaners in Spartanburg, SC, for dry cleaning, laundry, alterations, and pickup and delivery. Call or send our team a message today.',
    },
    'blog': {
        'path': '/blog/', 'crumb': 'Blog',
        'title': 'Garment Care Blog | Bell Laundry & Cleaners',
        'description': 'Explore clothing care tips, laundry advice, and guidance for everyday garments and special pieces from Bell Laundry & Cleaners in Upstate South Carolina.',
    },
    'media': {
        'path': '/media-room/', 'crumb': 'Media Room',
        'title': 'Media Room | Bell Laundry & Cleaners',
        'description': 'Company news and updates from Bell Laundry & Cleaners, established in Spartanburg in 1941. For media inquiries, contact our team at 864-583-8668.',
    },
    'work': {
        'path': '/work-with-us/', 'crumb': 'Work With Us',
        'title': 'Work With Us | Bell Laundry & Cleaners, Spartanburg',
        'description': 'Interested in joining Bell Laundry & Cleaners in Spartanburg, SC? Share your experience, availability, and resume through our online employment inquiry form.',
    },
    'new-customer': {
        'path': '/new-customer/', 'crumb': 'New Customer Offer',
        'title': '33% Off Your First Order | Bell Laundry & Cleaners',
        'description': 'New to Bell Laundry & Cleaners in Spartanburg, SC? Claim 33% off your first order of dry cleaning, laundry, and more. Fill out the form to get started.',
    },
    'thank-you': {
        'path': '/thank-you/', 'crumb': 'Thank You', 'sitemap': False,
        'title': 'Thank You | Bell Laundry & Cleaners',
        'description': 'Thank you for claiming 33% off your first order at Bell Laundry & Cleaners in Spartanburg, SC.',
    },
}

OFFER_PAGES = ('new-customer', 'thank-you')
OFFER_STRIP = '''<section class="offer-strip-wrap">
  <div class="container">
    <a class="offer-strip" href="/new-customer/" data-offer-cta="strip" data-reveal="up">
      <span class="offer-badge"><strong>33%</strong><span>Off</span></span>
      <span class="offer-strip-text"><small>New to Bell Laundry &amp; Cleaners?</small><strong>33% Off Your First Order</strong></span>
      <span class="btn">Claim Offer <span class="btn-ico"><svg aria-hidden="true"><use href="#i-arrow"/></svg></span></span>
    </a>
  </div>
</section>'''
OFFER_BAR = '''<div class="offer-bar" data-offer-bar>
  <div class="container">
    <a href="/new-customer/" data-offer-cta="top-bar"><span class="offer-tag">New customers</span><strong>33% Off Your First Order</strong><span class="offer-go">Claim offer <svg aria-hidden="true"><use href="#i-arrow"/></svg></span></a>
    <button type="button" class="offer-close" aria-label="Hide offer" data-offer-close><svg aria-hidden="true"><use href="#i-close"/></svg></button>
  </div>
</div>'''

NAV = [
    ('home', 'Home', '/'),
    ('about', 'About', '/about-us/'),
    ('services', 'Services', '/services/'),
    ('pickup-delivery', 'Pickup & Delivery', '/pickup-delivery/'),
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


BASE = 'https://bellcleaners.com'


def plain(s):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', '', s))).strip()


def page_schema(key, meta):
    """JSON-LD for a page: the business on home/location, breadcrumbs on inner pages,
    Service + FAQPage on content pages (FAQ text is exactly what the page shows)."""
    out = []
    if key in ('home', 'location'):
        out.append(SCHEMA)
    if meta['path'] != '/':
        crumbs = [('Home', '/')]
        if meta.get('parent'):
            crumbs.append(meta['parent'])
        crumbs.append((meta.get('crumb') or meta['title'].split(' | ')[0], meta['path']))
        out.append({'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': i + 1, 'name': n, 'item': BASE + p} for i, (n, p) in enumerate(crumbs)]})
    if meta.get('service'):
        out.append({'@context': 'https://schema.org', '@type': 'Service', 'name': meta['service'],
                    'serviceType': meta['service'], 'description': meta['description'], 'url': BASE + meta['path'],
                    'areaServed': {'@type': 'City', 'name': 'Spartanburg, SC'},
                    'provider': {'@type': 'DryCleaningOrLaundry', 'name': SCHEMA['name'], 'url': SCHEMA['url'],
                                 'telephone': SCHEMA['telephone'], 'address': SCHEMA['address']}})
    if meta.get('faq'):
        out.append({'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [
            {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in meta['faq']]})
    return out


def faq_pairs(page):
    """Question/answer pairs from a page's FAQ section."""
    pairs = []
    for sec in page['sections']:
        if 'FAQ' not in sec['heading'] and 'Frequently Asked' not in sec['heading']:
            continue
        q = None
        for it in sec['items']:
            if it['t'] == 'h3':
                q = [it['text'], []]
                pairs.append(q)
            elif it['t'] == 'p' and q:
                q[1].append(plain(it['html']))
    return [(q, ' '.join(a)) for q, a in pairs if a]


SERVICE_MENU = []  # (slug, name, icon), filled from services.json in main()


def services_menu(key, cur):
    """Desktop Services item: link to the hub plus a dropdown of every service page."""
    links = '\n'.join(
        f'            <li><a href="/{s}/"{" aria-current=\"page\"" if s == key else ""}>'
        f'<span class="mi">{icon(ic)}</span>{html.escape(n)}</a></li>' for s, n, ic in SERVICE_MENU)
    return f'''        <li class="has-menu">
          <a href="/services/"{cur}>Services</a>
          <button class="menu-toggle" type="button" aria-expanded="false" aria-controls="services-menu" aria-label="Show all services">{icon('arrow')}</button>
          <div class="mega" id="services-menu">
            <ul>
{links}
            </ul>
            <a class="mega-all" href="/services/">View all services {icon('arrow')}</a>
          </div>
        </li>'''


def services_menu_mobile(key, cur, i):
    links = '\n'.join(f'        <li><a href="/{s}/"{" aria-current=\"page\"" if s == key else ""}>{html.escape(n)}</a></li>'
                      for s, n, ic in SERVICE_MENU)
    return f'''    <li style="--i:{i}" class="has-sub">
      <div class="sub-row"><a href="/services/"{cur}>Services</a><button class="sub-toggle" type="button" aria-expanded="false" aria-controls="m-services" aria-label="Show all services">{icon('arrow')}</button></div>
      <ul class="sub" id="m-services">
{links}
      </ul>
    </li>'''


def render(key, meta, layout, icons, versions, body=None, nav_key=None):
    if body is None:
        body = (SRC / 'pages' / f'{key}.html').read_text(encoding='utf-8')
        body = body.replace('{{blog_posts}}', blog_cards() if '{{blog_posts}}' in body else '')
    body = body.replace('{{offer_form}}', (SRC / 'offer-form.html').read_text(encoding='utf-8').strip())
    body = body.replace('{{offer_strip}}', OFFER_STRIP)
    body = body.replace('{{service_links}}', '\n'.join(
        f'      <a class="rel-link" href="/{s}/"><span class="svc-ico">{icon(ic)}</span><span>{html.escape(n)}</span>{icon("arrow")}</a>'
        for s, n, ic in SERVICE_MENU))
    nav_key = nav_key or key
    if not meta.get('faq') and '<details' in body:
        # hand-written pages: read the questions and answers off the accordion itself
        meta = dict(meta, faq=[(plain(q), plain(a)) for q, a in re.findall(
            r'<summary>.*?</span>(.*?)</summary>\s*<div class="answer">(.*?)</div>', body, re.S)])
    nav, nav_m = [], []
    for i, (k, label, href) in enumerate(NAV):
        cur = ' aria-current="page"' if k == nav_key else ''
        if k == 'services' and SERVICE_MENU:
            nav.append(services_menu(key, cur))
            nav_m.append(services_menu_mobile(key, cur, i))
            continue
        nav.append(f'        <li><a href="{href}"{cur}>{html.escape(label)}</a></li>')
        nav_m.append(f'    <li style="--i:{i}"><a href="{href}"{cur}>{html.escape(label)}</a></li>')
    for j, (label, href) in enumerate([('Media Room', '/media-room/'), ('Work With Us', '/work-with-us/')]):
        nav_m.append(f'    <li style="--i:{len(NAV) + j}"><a href="{href}">{label}</a></li>')
    preload = ''
    if meta.get('preload'):
        preload = f'<link rel="preload" as="image" href="{meta["preload"]}" fetchpriority="high">'
    schema = ''.join('<script type="application/ld+json">' + json.dumps(s, separators=(',', ':'), ensure_ascii=False) + '</script>'
                     for s in page_schema(key, meta))
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
        'offer_bar': '' if key in OFFER_PAGES else OFFER_BAR,
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
    for p in json.loads((SRC / 'services.json').read_text(encoding='utf-8')):
        if p['slug'] != 'services':
            SERVICE_MENU.append((p['slug'], SHORT_NAMES[p['slug']], SERVICE_ICONS[p['slug']]))
    layout = (SRC / 'layout.html').read_text(encoding='utf-8')
    icons = (SRC / 'icons.svg').read_text(encoding='utf-8').strip()
    versions = {
        'css': stamp(ROOT / 'assets' / 'css' / 'site.css'),
        'js': stamp(ROOT / 'assets' / 'js' / 'site.js'),
    }
    for key, meta in PAGES.items():
        render(key, meta, layout, icons, versions)
    services = json.loads((SRC / 'services.json').read_text(encoding='utf-8'))
    locations = json.loads((SRC / 'locations.json').read_text(encoding='utf-8'))
    for page in services + locations:
        slug = page['slug']
        is_service = page in services and slug != 'services'
        meta = {
            'path': f'/{slug}/', 'title': page['title'], 'description': page['description'],
            'crumb': SHORT_NAMES.get(slug), 'faq': faq_pairs(page),
            'parent': ('Services', '/services/') if is_service else None,
            'service': SHORT_NAMES.get(slug) if is_service else None,
        }
        nav_key = 'pickup-delivery' if slug == 'pickup-delivery' else ('services' if page in services else None)
        render(slug, meta, layout, icons, versions, body=render_service(page, services), nav_key=nav_key)
    # sitemap for the production domain (staging itself stays robots-disallowed)
    paths = [m['path'] for m in PAGES.values() if m.get('sitemap', True)] + [f'/{p["slug"]}/' for p in services + locations]
    today = date.today().isoformat()
    urls = '\n'.join(f'  <url><loc>{BASE}{p}</loc><lastmod>{today}</lastmod></url>' for p in paths)
    (ROOT / 'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                                      f'{urls}\n</urlset>\n', encoding='utf-8', newline='\n')
    print(f'built sitemap.xml ({len(paths)} urls)')


if __name__ == '__main__':
    main()
