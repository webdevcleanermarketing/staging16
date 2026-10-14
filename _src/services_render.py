"""Render the service pages from _src/services.json in the site's design.

Each supplied section is matched to a layout by its content: numbered h3s become the step
timeline, "FAQ" headings the accordion, the store block the visit card + map, h3 groups
become cards, and so on. The copy itself is used as supplied.
"""
import html
import json
import pathlib
import re

# CC0 / public-domain stock photos (source and license per file)
STOCK = json.loads((pathlib.Path(__file__).resolve().parent.parent / 'assets' / 'img' / 'stock' / 'CREDITS.json').read_text(encoding='utf-8'))

SIGNUP = 'https://belllaundryanddrycleaning.smrtapp.com/customer/'
MAPS = 'https://maps.google.com/?q=Bell+Laundry+%26+Cleaners+448+Marion+Ave+Spartanburg+SC+29306'

# short names for menus and the related-services grid
SHORT = {
    'dry-cleaning': 'Dry Cleaning',
    'laundry-wash-and-fold': 'Laundry & Wash and Fold',
    'pickup-delivery': 'Pickup & Delivery',
    'alterations': 'Alterations & Tailoring',
    'wedding-dress-cleaning-preservation': 'Wedding Dress Cleaning',
    'comforter-household-cleaning': 'Comforter & Household',
    'tablecloth-linen-cleaning': 'Tablecloths & Linens',
    'leather-suede-cleaning': 'Leather & Suede',
    'stain-removal-specialty-garment-care': 'Stain Removal & Specialty Care',
    'shirt-laundry-professional-pressing': 'Shirt Laundry & Pressing',
    'business-commercial-laundry': 'Business & Commercial',
    'shoe-repair': 'Shoe Repair',
    'location': 'Our Location',
    'service-areas': 'Service Areas',
}
# service names as the docs write them -> page slug
NAME_TO_SLUG = {
    'dry cleaning': 'dry-cleaning', 'laundry and wash and fold': 'laundry-wash-and-fold',
    'laundry & wash and fold': 'laundry-wash-and-fold', 'alterations & tailoring': 'alterations',
    'wedding dress cleaning and preservation': 'wedding-dress-cleaning-preservation',
    'comforter & household cleaning': 'comforter-household-cleaning',
    'tablecloths & linens cleaning service': 'tablecloth-linen-cleaning', 'leather & suede cleaning': 'leather-suede-cleaning',
    'stain removal and specialty garment care': 'stain-removal-specialty-garment-care',
    'stain removal & specialty garment care': 'stain-removal-specialty-garment-care',
    'shirt laundry & professional pressing': 'shirt-laundry-professional-pressing',
    'business & commercial laundry': 'business-commercial-laundry',
    'commercial & business cleaning services': 'business-commercial-laundry', 'pickup and delivery': 'pickup-delivery',
}
ICON = {
    'dry-cleaning': 'hanger', 'laundry-wash-and-fold': 'washer', 'pickup-delivery': 'truck',
    'alterations': 'scissors', 'wedding-dress-cleaning-preservation': 'dress',
    'comforter-household-cleaning': 'blanket', 'tablecloth-linen-cleaning': 'table',
    'leather-suede-cleaning': 'jacket', 'stain-removal-specialty-garment-care': 'drop',
    'shirt-laundry-professional-pressing': 'shirt', 'business-commercial-laundry': 'building',
    'shoe-repair': 'shoe', 'services': 'sparkle', 'location': 'pin', 'service-areas': 'truck',
}
# Bell's own photos, picked per page: [hero, second, third]
PHOTOS = {
    'services': ['wall-flag', 'conveyor-bags', 'sign-sanitone', 'threads', 'bags-bell'],
    'dry-cleaning': ['hero-care', 'conveyor-bags', 'conveyor-warm', 'bags-bell', 'sign-sanitone', 'conveyor-bw'],
    'laundry-wash-and-fold': ['stock/laundry-folded', 'stock/laundry-hangers', 'stock/laundry-laundromat', 'stock/laundry-basket', 'bags-bell'],
    'pickup-delivery': ['hero-pickup', 'team-van', 'storefront', 'bags-bell', 'conveyor-warm'],
    'alterations': ['sewing', 'stock/alt-tailor', 'stock/alt-scissors', 'threads', 'service-note'],
    'wedding-dress-cleaning-preservation': ['stock/wedding-hanging', 'stock/wedding-lace', 'stock/wedding-window', 'stock/wedding-rack', 'stock/wedding-gown'],
    'comforter-household-cleaning': ['stock/comforter-bed', 'stock/comforter-reading', 'stock/biz-towel-stack', 'stock/comforter-room', 'bags-bell'],
    'tablecloth-linen-cleaning': ['stock/table-reception', 'stock/table-napkins', 'stock/table-dining', 'stock/table-long', 'stock/table-white'],
    'leather-suede-cleaning': ['stock/leather-rack', 'stock/leather-detail', 'stock/leather-wearing', 'stock/leather-group', 'sewing'],
    'stain-removal-specialty-garment-care': ['stock/shirt-white', 'bags-pink', 'stock/table-napkins', 'stock/biz-towels', 'conveyor-bags'],
    'shirt-laundry-professional-pressing': ['stock/shirt-display', 'stock/laundry-hangers', 'stock/shirt-suitcase', 'stock/shirt-line', 'conveyor-bw'],
    'business-commercial-laundry': ['stock/biz-laundromat', 'stock/biz-towels', 'stock/biz-kitchen', 'stock/biz-towel-stack', 'team-van'],
    'shoe-repair': ['stock/shoe-brogues', 'stock/shoe-row', 'stock/shoe-black', 'stock/shoe-woven', 'stock/shoe-boots'],
    'location': ['wall-1941', 'sign-sanitone', 'building', 'hero-sameday', 'conveyor-bags', 'storefront'],
    'service-areas': ['hero-pickup', 'team-van', 'wall-flag', 'bags-bell', 'conveyor-warm'],
}
_used = {}


def next_photo(slug):
    """Hand out the page's photos in turn (the hero uses the first), so neighbours never repeat."""
    pool = PHOTOS[slug]
    i = _used.get(slug, 1)
    _used[slug] = i + 1
    return pool[1 + (i - 1) % (len(pool) - 1)]

PHOTO_ALT = {
    'stock/alt-tailor': 'Tailor sewing at a machine', 'stock/alt-scissors': 'Tailoring shears, thread and buttons',
    'stock/wedding-hanging': 'Wedding dress hanging in a bright hallway', 'stock/wedding-lace': 'Close-up of wedding gown lace',
    'stock/wedding-window': 'Wedding gown hanging by a window', 'stock/wedding-rack': 'Wedding dresses on a rack',
    'stock/wedding-gown': 'Wedding gown on display', 'stock/laundry-folded': 'Stack of neatly folded clothes',
    'stock/laundry-hangers': 'Fresh shirts on wooden hangers', 'stock/laundry-laundromat': 'Rows of washers and dryers',
    'stock/laundry-basket': 'Woven laundry basket', 'stock/comforter-bed': 'Bed made with a fresh white comforter',
    'stock/comforter-reading': 'Relaxing on fresh white bedding', 'stock/comforter-room': 'Bedroom with clean bedding',
    'stock/biz-towel-stack': 'Stack of folded linens', 'stock/table-reception': 'Tables set with white tablecloths',
    'stock/table-napkins': 'Table set with folded cloth napkins', 'stock/table-dining': 'Dining table with a white tablecloth',
    'stock/table-long': 'Long banquet table with white linens', 'stock/table-white': 'Table laid with white linens',
    'stock/leather-rack': 'Leather jackets on a rack', 'stock/leather-detail': 'Close-up of a leather jacket zipper',
    'stock/leather-wearing': 'Person wearing a leather jacket', 'stock/leather-group': 'Friends wearing jackets',
    'stock/shirt-white': 'Crisp white dress shirt', 'stock/shirt-display': 'Pressed collared shirts on display',
    'stock/shirt-suitcase': 'Folded striped dress shirt', 'stock/shirt-line': 'Shirts hanging in a row',
    'stock/biz-laundromat': 'Commercial washers and dryers', 'stock/biz-towels': 'Folded white towels',
    'stock/biz-kitchen': 'Busy restaurant kitchen', 'stock/shoe-brogues': 'Brown leather brogues',
    'stock/shoe-row': 'Row of leather dress shoes', 'stock/shoe-black': 'Polished black leather shoes',
    'stock/shoe-woven': 'Woven leather shoes', 'stock/shoe-boots': 'Leather work boots',
    'wall-1941': 'Painted Bell sign: Certified Master Dry Cleaner, Since 1941',
    'wall-flag': 'Bell building with the painted Bell script',
    'conveyor-bags': 'Garments in Bell bags on the conveyor',
    'conveyor-warm': 'Rows of finished orders in Bell bags',
    'conveyor-bw': 'Garment conveyor at Bell',
    'sign-sanitone': 'Bell Laundry & Cleaners sign with the Sanitone sign',
    'hero-care': 'Cleaned garments in Bell bags on the conveyor',
    'hero-sameday': 'Finished orders hanging inside the Bell store',
    'hero-pickup': 'Bell delivery van',
    'team-van': 'Two Bell team members by a Bell van',
    'storefront': 'Bell Laundry & Cleaners storefront',
    'bags-bell': 'Finished orders in Bell bags',
    'bags-pink': 'Tagged orders in Bell bags',
    'building': 'The Bell building',
    'sewing': 'Sewing machine used for alterations',
    'threads': 'Wall of thread spools',
    'service-note': 'Framed customer service note at Bell',
}
PHOTO_SIZE = {'hero-pickup': (1500, 692), 'team-van': (1400, 495), 'storefront': (1500, 542), 'service-note': (900, 1162)}
CARD_ICONS = [
    (r'^spartanburg$|^greenville$', 'pin'), (r'sanitone|certif|credential|quality', 'award'), (r'family|keepsake|memor|meaning|care that|matters', 'heart'),
    (r'same-day|fast|quick', 'bolt'), (r'team|people|relationship|knows you|personal', 'users'),
    (r'talk|tell|communicat|conversation|ask|explain|describe|details|history|noticed', 'chat'),
    (r'schedule|monday|day|date|timing|week|prepare ahead|routine', 'calendar'), (r'turnaround|time|expect', 'clock'),
    (r'pric|bag', 'news'), (r'comforter|blanket|bedspread|sheet|pillow', 'blanket'),
    (r'tablecloth|napkin|linen', 'table'), (r'leather|suede|overcoat', 'jacket'), (r'shirt|press|iron', 'shirt'),
    (r'gown|bridal|dress|veil', 'dress'), (r'hem|sleeve|suit|blazer|tuxedo|denim|alter|restyl|resiz|fit', 'scissors'),
    (r'shoe|sole|heel|footwear|stretch|shine|fastener|zipper|recondition', 'shoe'),
    (r'store|visit|marion|^spartanburg$|^greenville$', 'pin'), (r'pickup|picked up|deliver', 'truck'), (r'items|volume|location|business', 'building'),
    (r'stain|spill|mark|clean', 'drop'), (r'label|check', 'check'),
]


def icon(name):
    return f'<svg aria-hidden="true"><use href="#i-{name}"/></svg>'


def esc(s):
    return html.escape(s, quote=False)


def card_icon(title):
    t = title.lower()
    for pat, name in CARD_ICONS:
        if re.search(pat, t):
            return name
    return 'sparkle'


def img(name, cls='', eager=False, alt=None):
    if name.startswith('stock/') and name[6:] in STOCK:
        PHOTO_SIZE[name] = tuple(STOCK[name[6:]]['size'])
    w, h = PHOTO_SIZE.get(name, (1200, 800) if name not in ('hero-care', 'hero-sameday', 'wall-flag', 'building') else (1500, 1000))
    alt = PHOTO_ALT.get(name, '') if alt is None else alt
    load = 'fetchpriority="high"' if eager else 'loading="lazy"'
    return f'<img src="/assets/img/{name}.webp" width="{w}" height="{h}" alt="{html.escape(alt)}" {load}{cls}>'


def heading_html(text, tag='h2', cls='h2'):
    """Set the last two or three words of a heading in the script accent, like the rest of the site."""
    words = text.split(' ')
    n = 2 if len(words) > 3 else 1
    if len(words) > 7:
        n = 3
    head, tail = ' '.join(words[:-n]), ' '.join(words[-n:])
    inner = f'{esc(head)} <span class="script">{esc(tail)}</span>' if head else f'<span class="script">{esc(tail)}</span>'
    return f'<{tag} class="{cls}" data-split>{inner}</{tag}>'


def map_button(b, variant):
    """Turn a supplied button into a site button with the right destination and icon."""
    label, href = b['label'], b['href']
    low = label.lower()
    ext = ''
    if 'maps' in href or 'directions' in low:
        href, ico = MAPS, 'pin'
        ext = ' target="_blank" rel="noopener"'
    elif 'sign up' in low:
        href, ico = SIGNUP, 'arrow'
        ext = ' target="_blank" rel="noopener"'
    elif href.startswith('tel:') or low.startswith('call') or low.startswith('check service'):
        href, ico = 'tel:+18645838668', 'phone'
    elif 'pickup and delivery' in low:
        href, ico = '/pickup-delivery/', 'truck'
    elif low == 'explore our services':
        href, ico = '/services/', 'arrow'
    elif low.startswith('explore '):
        href, ico = href, 'arrow'
    else:
        href = '/contact/' if not href or 'bellcleaners.com/contact' in href else href
        ico = 'arrow'
    return f'<a class="btn {variant}" href="{html.escape(href)}"{ext}>{esc(label)} <span class="btn-ico">{icon(ico)}</span></a>'


def buttons(items, dark_first=True, on_dark=False):
    out = []
    for it in items:
        if it['t'] != 'btns':
            continue
        for i, b in enumerate(it['list']):
            if on_dark:
                variant = '' if i == 0 else 'btn-ghost'
            else:
                variant = ('btn-dark' if dark_first else '') if i == 0 else 'btn-ghost on-light'
            out.append(map_button(b, variant))
    return f'<div class="btn-row" data-reveal="up">{"".join(out)}</div>' if out else ''


def paras(items, lead_first=False):
    ps = [it['html'] for it in items if it['t'] == 'p']
    out = []
    for i, p in enumerate(ps):
        cls = ' class="lead"' if lead_first and i == 0 else ''
        out.append(f'<p{cls}>{p}</p>')
    return '\n'.join(out)


def groups(items):
    """Split items into (intro paragraphs, [(h3, [p...])], trailing buttons)."""
    intro, grps = [], []
    for it in items:
        if it['t'] == 'h3':
            grps.append([it['text'], []])
        elif it['t'] == 'p':
            (grps[-1][1] if grps else intro).append(it['html'])
    return intro, grps


def kind(sec, idx, last_idx):
    items = sec['items']
    h3s = [i['text'] for i in items if i['t'] == 'h3']
    ps = [i['html'] for i in items if i['t'] == 'p']
    labels = [i['label'] for i in items if i['t'] == 'btns' for i in i['list']]
    if idx == 0:
        return 'hero'
    if any(re.match(r'Saturday', h) for h in h3s) or any(p.strip().startswith(('Store Hours:', 'Address:')) for p in ps):
        return 'visit'
    if 'FAQ' in sec['heading'] or 'Frequently Asked' in sec['heading']:
        return 'faq'
    if sum(1 for h in h3s if re.match(r'\d+\.\s', h)) >= 2:
        return 'steps'
    if 'Word From Our Customers' in sec['heading']:
        return 'review'
    if sum(1 for l in labels if l.startswith('Explore ')) >= 4 or sum(1 for h in h3s if h.lower() in NAME_TO_SLUG) >= 4:
        return 'hub'
    if len(h3s) >= 2:
        return 'cards'
    if sum(1 for p in ps if re.match(r'^[A-Z][A-Za-z ]{2,30}: ', p)) >= 2:
        return 'labels'
    if idx == last_idx:
        return 'closing'
    return 'text'


def section_head(sec, center=False, dark=False):
    eb = f'<span class="eyebrow" data-reveal="up">{esc(sec["eyebrow"])}</span>' if sec['eyebrow'] else ''
    cls = 'section-head center' if center else 'section-head'
    return f'<div class="{cls}">{eb}{heading_html(sec["heading"])}'


def render_hero(page, sec):
    photo = PHOTOS[page['slug']][0]
    ps = [it['html'] for it in sec['items'] if it['t'] == 'p']
    lead = f'<p class="lead" data-reveal="up">{ps[0]}</p>' if ps else ''
    crumbs = '<li><a href="/">Home</a></li>'
    if page['slug'] not in ('services', 'location', 'service-areas'):
        crumbs += '<li><a href="/services/">Services</a></li>'
        crumbs += f'<li>{esc(SHORT[page["slug"]])}</li>'
    else:
        crumbs += f'<li>{esc(SHORT.get(page["slug"], "Services"))}</li>'
    btns = buttons(sec['items'], dark_first=False, on_dark=True)
    hero = f'''<section class="page-hero svc-hero">
  <span class="sparkle" style="left:6%;top:18%;width:18px;height:18px">{icon('sparkle')}</span>
  <div class="container">
    <div class="svc-hero-text">
      <ol class="crumbs" data-reveal="up">{crumbs}</ol>
      <span class="eyebrow" data-reveal="up">{esc(sec['eyebrow'])}</span>
      {heading_html(sec['heading'], 'h1', 'h1')}
      {lead}
      {btns}
    </div>
    <div class="svc-hero-media">
      <span class="arch-outline" aria-hidden="true"></span>
      <div class="arch" data-parallax="0.05">{img(photo, eager=True)}</div>
      <span class="svc-hero-badge bob">{icon(ICON[page['slug']])}</span>
    </div>
  </div>
</section>'''
    rest = ps[1:]
    if not rest:
        return hero
    body = '\n'.join(f'<p{" class=\"lead\"" if i == 0 else ""}>{p}</p>' for i, p in enumerate(rest))
    intro = f'''<section class="section-tight svc-intro">
  <div class="container"><div class="svc-intro-card prose" data-reveal="up">{body}</div></div>
</section>'''
    return hero + '\n' + intro


def render_text(page, sec, n, band):
    photo = next_photo(page['slug'])
    flip = ' flip' if n % 2 else ''
    sand = ' section-sand' if band else ''
    eb = f'<span class="eyebrow" data-reveal="up">{esc(sec["eyebrow"])}</span>' if sec['eyebrow'] else ''
    return f'''<section class="section{sand}">
  <div class="container text-media{flip}">
    <div class="media-frame" data-reveal="clip" data-parallax="0.08">{img(photo)}</div>
    <div>
      {eb}
      {heading_html(sec['heading'])}
      <div class="prose" data-reveal="up">{paras(sec['items'])}</div>
      {buttons(sec['items'])}
    </div>
  </div>
</section>'''


def render_cards(page, sec, band, label_mode=False):
    outro = []
    if label_mode:
        # "Shirts: Dress shirts and blouses..." paragraphs become cards
        intro, grps = [], []
        for it in sec['items']:
            if it['t'] != 'p':
                continue
            m = re.match(r'^([A-Z][A-Za-z ]{2,30}): (.*)$', it['html'], re.S)
            if m:
                grps.append([m.group(1), [m.group(2)]])
            elif grps:
                outro.append(it['html'])
            else:
                intro.append(it['html'])
    else:
        intro, grps = groups(sec['items'])
    dark = band and len(grps) <= 4 and not label_mode
    cls = 'section section-dark' if dark else ('section section-sand' if band else 'section')
    cols = 'cards-3' if len(grps) in (3, 6) or len(grps) > 6 else ('cards-4' if len(grps) == 4 else 'cards-2g')
    cards = []
    for i, (title, body) in enumerate(grps):
        text_html = ''.join(f'<p>{p}</p>' for p in body)
        cards.append(f'''<article class="info-tile{' on-dark' if dark else ''}">
        <span class="num" aria-hidden="true">{i + 1:02d}</span>
        <span class="svc-ico">{icon(card_icon(title))}</span>
        <h3>{esc(title)}</h3>
        {text_html}
      </article>''')
    intro_html = f'<div class="prose lead-block" data-reveal="up">{"".join(f"<p>{p}</p>" for p in intro)}</div>' if intro else ''
    outro_html = f'<div class="prose outro" data-reveal="up">{"".join(f"<p>{p}</p>" for p in outro)}</div>' if outro else ''
    eb = f'<span class="eyebrow" data-reveal="up">{esc(sec["eyebrow"])}</span>' if sec['eyebrow'] else ''
    btns = buttons(sec['items'], dark_first=not dark, on_dark=dark)
    return f'''<section class="{cls}">
  <div class="container">
    <div class="section-head split-head">
      <div>{eb}{heading_html(sec['heading'])}</div>
      {intro_html}
    </div>
    <div class="tile-grid {cols}" data-stagger=".08">
      {''.join(cards)}
    </div>
    {outro_html}
    {f'<div class="tile-cta">{btns}</div>' if btns else ''}
  </div>
</section>'''


def render_steps(page, sec, band):
    intro, grps = groups(sec['items'])
    photo = next_photo(page['slug'])
    steps = []
    for title, body in grps:
        m = re.match(r'(\d+)\.\s*(.*)', title)
        num, t = (m.group(1), m.group(2)) if m else ('', title)
        steps.append(f'''<li class="step" data-reveal="up">
        <span class="step-dot">{num}</span>
        <h3>{esc(t)}</h3>
        {''.join(f'<p>{p}</p>' for p in body)}
      </li>''')
    eb = f'<span class="eyebrow" data-reveal="up">{esc(sec["eyebrow"])}</span>' if sec['eyebrow'] else ''
    intro_html = f'<div class="prose" data-reveal="up">{"".join(f"<p>{p}</p>" for p in intro)}</div>' if intro else ''
    sand = ' section-sand' if band else ''
    return f'''<section class="section{sand}">
  <div class="container steps-grid">
    <div class="steps-aside">
      {eb}
      {heading_html(sec['heading'])}
      {intro_html}
      {buttons(sec['items'])}
      <div class="frame" data-reveal="clip">{img(photo)}</div>
    </div>
    <ol class="steps">
      {''.join(steps)}
    </ol>
  </div>
</section>'''


def render_faq(page, sec):
    intro, grps = groups(sec['items'])
    photo = next_photo(page['slug'])
    items = []
    for i, (q, body) in enumerate(grps):
        items.append(f'''<details{' open' if i == 0 else ''}>
          <summary><span class="tog">{icon('arrow')}</span>{esc(q)}</summary>
          <div class="answer">{''.join(f'<p>{p}</p>' for p in body)}</div>
        </details>''')
    eb = f'<span class="eyebrow" data-reveal="up">{esc(sec["eyebrow"])}</span>' if sec['eyebrow'] else ''
    return f'''<section class="section">
  <div class="container faq-grid">
    <div>
      {eb}
      {heading_html(sec['heading'])}
      <div class="faq" data-stagger=".07">
        {''.join(items)}
      </div>
    </div>
    <div class="faq-media" data-reveal="clip" data-parallax="0.06">
      {img(photo)}
      <a class="call-chip" href="tel:+18645838668">
        <span class="ring">{icon('phone')}</span>
        <span><small>Still have a question?</small><strong>864-583-8668</strong></span>
      </a>
    </div>
  </div>
</section>'''


def render_visit(page, sec, band):
    ps = []
    for it in sec['items']:
        if it['t'] != 'p':
            continue
        raw = html.unescape(re.sub(r'<[^>]+>', '', it['html'])).strip()
        if raw in ('Address:', 'Phone:', 'Store Hours:') or raw.startswith(('448 Marion', 'Monday through Friday', '864-583-8668', 'Bell Laundry & Cleaners 448', 'Phone:', 'Store Hours:', 'Address:')) or raw == 'Bell Laundry & Cleaners':
            continue
        ps.append(it['html'])
    btns = buttons(sec['items'])
    eb = f'<span class="eyebrow" data-reveal="up">{esc(sec["eyebrow"])}</span>' if sec['eyebrow'] else ''
    sand = ' section-sand' if band else ''
    lead = f'<div class="prose center-prose" data-reveal="up">{"".join(f"<p>{p}</p>" for p in ps)}</div>' if ps else ''
    return f'''<section class="section{sand}">
  <div class="container">
    <div class="section-head center">
      {eb}
      {heading_html(sec['heading'])}
      {lead}
    </div>
    <div class="visit-grid">
      <div class="info-card" data-reveal="left">
        <div class="info-row"><span class="i">{icon('pin')}</span><div><small>Address</small><strong>Bell Laundry &amp; Cleaners<br>448 Marion Ave, Spartanburg, SC 29306</strong></div></div>
        <div class="info-row"><span class="i">{icon('phone')}</span><div><small>Phone</small><a href="tel:+18645838668">864-583-8668</a></div></div>
        <div class="info-row"><span class="i">{icon('clock')}</span><div><small>Store Hours</small>
          <dl class="hours-table"><dt>Monday – Friday</dt><dd>7:30 a.m. to 6 p.m.</dd><dt>Saturday</dt><dd>8 a.m. to noon</dd></dl>
          <span class="open-status" data-open-status aria-live="polite"></span>
        </div></div>
        {btns.replace('data-reveal="up"', 'style="margin-top:18px"')}
      </div>
      <div class="map-card" data-reveal="right">
        <iframe title="Map to Bell Laundry &amp; Cleaners, 448 Marion Ave, Spartanburg, SC" src="https://www.google.com/maps?q=Bell+Laundry+%26+Cleaners,+448+Marion+Ave,+Spartanburg,+SC+29306&amp;output=embed" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe>
        <div class="map-pin-card"><img src="/assets/img/wall-1941.webp" width="1400" height="820" alt="" loading="lazy"><div><strong>Bell Laundry &amp; Cleaners</strong><span>448 Marion Ave, Spartanburg</span></div></div>
      </div>
    </div>
  </div>
</section>'''


def render_review(page, sec):
    ps = [re.sub(r'<[^>]+>', '', it['html']) for it in sec['items'] if it['t'] == 'p']
    quote, name = (ps + ['', ''])[:2]
    eb = f'<span class="eyebrow" data-reveal="up">{esc(sec["eyebrow"])}</span>' if sec['eyebrow'] else ''
    return f'''<section class="section section-dark">
  <span class="sparkle" style="right:8%;top:16%;width:22px;height:22px">{icon('sparkle')}</span>
  <div class="container">
    <div class="section-head center">{eb}{heading_html(sec['heading'])}</div>
    <figure class="review review-solo" data-reveal="up">
      <svg class="q" aria-hidden="true"><use href="#i-quote"/></svg>
      <blockquote>{html.unescape(quote)}</blockquote>
      <figcaption><span class="avatar" aria-hidden="true">{esc(html.unescape(name)[:1])}</span><span><strong>{esc(html.unescape(name))}</strong><span>Bell customer</span></span></figcaption>
    </figure>
  </div>
</section>'''


def render_hub(page, sec, all_pages):
    intro, grps = groups(sec['items'])
    by_label = {}
    for it in sec['items']:
        if it['t'] == 'btns':
            for b in it['list']:
                by_label[b['label'].replace('Explore ', '', 1)] = b['href'].strip('/')
    cards = []
    for i, (title, body) in enumerate(grps):
        slug = by_label.get(title) or NAME_TO_SLUG.get(title.lower()) or next((s for s, n in SHORT.items() if n == title), '')
        feat = ' is-feature span-2' if i == 0 else (' is-gold span-2' if i == len(grps) - 1 and len(grps) % 4 == 2 else '')
        cards.append(f'''<a class="svc-card{feat}" href="/{slug}/">
        <div class="svc-top"><span class="svc-num">{i + 1:02d}</span><span class="svc-ico">{icon(ICON.get(slug, 'sparkle'))}</span></div>
        <h3>{esc(title)}</h3>
        {''.join(f'<p>{p}</p>' for p in body)}
        <span class="link-arrow">Explore {esc(title)} {icon('arrow')}</span>
      </a>''')
    eb = f'<span class="eyebrow" data-reveal="up">{esc(sec["eyebrow"])}</span>' if sec['eyebrow'] else ''
    intro_html = f'<p class="lead" data-reveal="up">{intro[0]}</p>' if intro else ''
    return f'''<section class="section section-sand" id="services">
  <div class="container">
    <div class="section-head split-head"><div>{eb}{heading_html(sec['heading'])}</div>{intro_html}</div>
    <div class="svc-grid svc-grid-links" data-stagger=".05">
      {''.join(cards)}
    </div>
    {f'<div class="tile-cta">{buttons(sec["items"])}</div>' if page['slug'] != 'services' else ''}
  </div>
</section>'''


def render_closing(page, sec):
    photo = next_photo(page['slug'])
    eb = f'<span class="eyebrow" style="color:var(--gold)">{esc(sec["eyebrow"])}</span>' if sec['eyebrow'] else ''
    ps = [it['html'] for it in sec['items'] if it['t'] == 'p']
    body = ''.join(f'<p{" class=\"lead\"" if i == 0 else ""}>{p}</p>' for i, p in enumerate(ps))
    return f'''<section class="section-tight">
  <div class="container">
    <div class="panel" data-reveal="up">
      <div class="panel-media" data-reveal="clip-x">{img(photo)}</div>
      <div class="panel-body">
        {eb}
        {heading_html(sec['heading']).replace('class="script"', 'class="script" style="color:var(--gold)"')}
        {body}
        {buttons(sec['items'], on_dark=True).replace(' data-reveal="up"', '')}
      </div>
    </div>
  </div>
</section>'''


def render_related(page, all_pages):
    links = []
    for p in all_pages:
        s = p['slug']
        if s in ('services', page['slug']):
            continue
        links.append(f'<a class="rel-link" href="/{s}/"><span class="svc-ico">{icon(ICON[s])}</span><span>{esc(SHORT[s])}</span>{icon("arrow")}</a>')
    return f'''<section class="section section-sand">
  <div class="container">
    <div class="section-head split-head">
      <div><span class="eyebrow" data-reveal="up">More Ways We Can Help</span><h2 class="h2" data-split>Explore More <span class="script">Services</span></h2></div>
      <a class="btn btn-dark" href="/services/" data-reveal="up">All Services <span class="btn-ico">{icon('arrow')}</span></a>
    </div>
    <div class="rel-grid" data-stagger=".04">{''.join(links)}</div>
  </div>
</section>'''


def render_page(page, all_pages):
    _used[page['slug']] = 1
    secs = page['sections']
    last = len(secs) - 1
    out, text_n = [], 0
    for i, sec in enumerate(secs):
        k = kind(sec, i, last)
        if k == 'hero':
            out.append(render_hero(page, sec))
            out.append('{{offer_strip}}')  # new-customer offer, filled in by build.py
        elif k == 'visit':
            out.append(render_visit(page, sec, sec['band']))
        elif k == 'faq':
            out.append(render_faq(page, sec))
        elif k == 'steps':
            out.append(render_steps(page, sec, sec['band']))
        elif k == 'review':
            out.append(render_review(page, sec))
        elif k == 'hub':
            out.append(render_hub(page, sec, all_pages))
        elif k == 'cards':
            out.append(render_cards(page, sec, sec['band']))
        elif k == 'labels':
            out.append(render_cards(page, sec, sec['band'], label_mode=True))
        elif k == 'closing':
            out.append(render_closing(page, sec))
        else:
            out.append(render_text(page, sec, text_n, sec['band']))
            text_n += 1
    # pages that already show the full services grid don't need the "Explore More Services" strip
    if not any(kind(sec, i, last) == 'hub' for i, sec in enumerate(secs)):
        out.append(render_related(page, all_pages))
    return '\n\n'.join(out)
