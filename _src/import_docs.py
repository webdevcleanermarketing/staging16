"""Import pages from a Bell content .docx (the Google Doc downloaded as Word) into a JSON page list
in the same shape as services.json, so services_render.py can render them.

usage: python _src/import_docs.py <file.docx> <out.json>

Doc conventions: "SEO Data" block (URL Slug, Meta Title, Meta Description, H1), "Miniheader: [..]"
eyebrows, Heading2/Heading3 section headings, Heading4 items, "[Label] [Label]" button lines.
Developer and client notes in [brackets] are skipped.
"""
import html
import json
import pathlib
import re
import sys
import zipfile


def paragraphs(path):
    xml = zipfile.ZipFile(path).read('word/document.xml').decode('utf-8')
    for para in re.findall(r'<w:p[ >].*?</w:p>', xml, re.S):
        style = re.search(r'<w:pStyle w:val="([^"]+)"', para)
        txt = ''.join(re.findall(r'<w:t(?: [^>]*)?>([^<]*)</w:t>', para.replace('<w:tab/>', '<w:t>\t</w:t>')))
        txt = html.unescape(txt).strip()
        if txt:
            yield (style.group(1) if style else ''), txt


def is_buttons(t):
    groups = re.findall(r'\[([^\]]+)\]', t)
    return groups and re.fullmatch(r'(\s*\[[^\]]+\]\s*)+', t) and all(len(g) < 45 for g in groups) \
        and not any(g.lower().startswith(('developer', 'client')) for g in groups)


def esc(t):
    t = html.escape(t, quote=False)
    return re.sub(r'864-583-8668', '<a href="tel:+18645838668">864-583-8668</a>', t)


pages, page, sec, eyebrow = [], None, None, ''
for style, t in paragraphs(sys.argv[1]):
    if t == 'SEO Data':
        page = {'sections': []}
        pages.append(page)
        sec = None
        continue
    m = re.match(r'(URL Slug|Meta Title|Meta Description|H1|Primary Keyword|Secondary Keywords):\s*(.*)', t)
    if m and page is not None and not page['sections']:
        key = {'URL Slug': 'slug', 'Meta Title': 'title', 'Meta Description': 'description', 'H1': 'h1',
               'Primary Keyword': 'keyword', 'Secondary Keywords': 'keywords'}[m.group(1)]
        page[key] = m.group(2).strip('/') if key == 'slug' else m.group(2)
        continue
    if page is None:
        continue
    if t.startswith('Miniheader:'):
        eyebrow = t.split(':', 1)[1].strip().strip('[]')
        continue
    if style in ('Heading2', 'Heading3'):
        sec = {'band': len(page['sections']) % 3 == 2, 'eyebrow': eyebrow, 'heading': t, 'items': []}
        page['sections'].append(sec)
        eyebrow = ''
        continue
    if sec is None:
        continue
    if style == 'Heading4':
        sec['items'].append({'t': 'h3', 'text': t})
    elif is_buttons(t):
        sec['items'].append({'t': 'btns', 'list': [{'href': '', 'label': g.strip()} for g in re.findall(r'\[([^\]]+)\]', t)]})
    elif t.startswith('[') and t.endswith(']'):
        continue  # developer / client notes
    else:
        sec['items'].append({'t': 'p', 'html': esc(t)})

# sections that only held a developer note (e.g. reviews still to be verified) are dropped
for p in pages:
    p['sections'] = [s for s in p['sections'] if s['items']]
pathlib.Path(sys.argv[2]).write_text(json.dumps(pages, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
print(f'imported {len(pages)} pages: ' + ', '.join(f'/{p["slug"]}/ ({len(p["sections"])} sections)' for p in pages))
