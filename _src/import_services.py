"""One-off import of the reviewed service pages (Bell-Cleaners-service-pages-REVIEW.zip, /preview/)
into _src/services.json, keeping the supplied copy and section order.

usage: python _src/import_services.py <preview_dir>
After importing, edit _src/services.json directly; build.py renders it.
"""
import html
import json
import pathlib
import re
import sys

SRC = pathlib.Path(__file__).resolve().parent
preview = pathlib.Path(sys.argv[1])

# preferred order: the hub, then the order used on the home page
ORDER = ['services', 'dry-cleaning', 'laundry-wash-and-fold', 'pickup-delivery', 'alterations',
         'wedding-dress-cleaning-preservation', 'comforter-household-cleaning', 'tablecloth-linen-cleaning',
         'leather-suede-cleaning', 'stain-removal-specialty-garment-care', 'shirt-laundry-professional-pressing',
         'business-commercial-laundry', 'shoe-repair']


def clean_inline(s):
    """Keep inline links, fix the phone links that were missing the country code."""
    s = s.replace('tel:+8645838668', 'tel:+18645838668')
    s = s.replace('href="https://bellcleaners.com/contact/"', 'href="/contact/"')
    return s.strip()


def text(s):
    return html.unescape(re.sub(r'<[^>]+>', '', s)).strip()


pages = []
for slug in ORDER:
    t = (preview / slug / 'index.html').read_text(encoding='utf-8')
    page = {
        'slug': slug,
        'title': text(re.search(r'<title>(.*?)</title>', t).group(1)),
        'description': text(re.search(r'name="description" content="(.*?)"', t).group(1)),
        'sections': [],
    }
    for m in re.finditer(r'<section class="section ([^"]*)"><div class="wrap">(.*?)</div></section>', t, re.S):
        cls, body = m.group(1).strip(), m.group(2)
        if cls == 'related':
            continue
        sec = {'band': cls == 'band', 'eyebrow': '', 'heading': '', 'items': []}
        for el in re.finditer(r'<p class="eyebrow">(.*?)</p>|<h([123])>(.*?)</h\2>|<p>(.*?)</p>|<div class="actions">(.*?)</div>', body, re.S):
            if el.group(1) is not None:
                sec['eyebrow'] = text(el.group(1))
            elif el.group(2) in ('1', '2'):
                sec['heading'] = text(el.group(3))
            elif el.group(2) == '3':
                sec['items'].append({'t': 'h3', 'text': text(el.group(3))})
            elif el.group(4) is not None:
                sec['items'].append({'t': 'p', 'html': clean_inline(el.group(4))})
            else:
                btns = [{'href': html.unescape(h), 'label': text(l)}
                        for h, l in re.findall(r'class="button" href="([^"]+)">(.*?)<span', el.group(5))]
                sec['items'].append({'t': 'btns', 'list': btns})
        page['sections'].append(sec)
    pages.append(page)

(SRC / 'services.json').write_text(json.dumps(pages, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
print(f'imported {len(pages)} pages, {sum(len(p["sections"]) for p in pages)} sections')
