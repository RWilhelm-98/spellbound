import os
import zipfile
import xml.etree.ElementTree as ET
import html
from django.conf import settings

PORTFOLIO_ITEMS = {
    'copyedit-sample': {
        'slug': 'copyedit-sample',
        'filename': 'Copyedit, Sample.docx',
        'title': 'Copyediting Sample: Statement of Purpose',
        'subtitle': 'Academic Essay & Punctuation Rules',
        'category': 'Copy & Proofreading',
        'category_code': 'copy',
        'badge_class': 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
        'author': 'Grace Zurawell',
        'genre': 'Academic / Classics & Library Studies',
        'description': 'A detailed copyediting sample demonstrating precision grammar, compound word dictionary rules, independent clause punctuation, and style consistency.',
        'icon': 'copyedit'
    },
    'developmental-edit-sample': {
        'slug': 'developmental-edit-sample',
        'filename': 'Developmental Edit, Sample.docx',
        'title': 'Developmental Edit: Beauty & The Beast',
        'subtitle': 'Structural Analysis & Literary Essay',
        'category': 'Developmental Editing',
        'category_code': 'dev',
        'badge_class': 'bg-amber-500/20 text-amber-300 border-amber-500/30',
        'author': 'Grace Zurawell',
        'genre': 'Academic Essay / Literary Analysis',
        'description': 'A comprehensive developmental edit focusing on structural cohesion, argument framing, audience engagement, MLA citation, and reception analysis.',
        'icon': 'dev'
    },
    'developmental-edit-editors-note': {
        'slug': 'developmental-edit-editors-note',
        'filename': "Developmental Edit, Sample Editor's Note.docx",
        'title': "Editor's Memo: Developmental Edit",
        'subtitle': 'Academic Essay Feedback Letter',
        'category': "Editor's Note",
        'category_code': 'dev-note',
        'badge_class': 'bg-purple-500/20 text-purple-300 border-purple-500/30',
        'author': 'Grace Zurawell',
        'genre': 'Editorial Feedback Letter',
        'description': "An in-depth editorial letter from Grace Zurawell detailing structural strengths, thesis alignment, argument flow, and actionable revision notes.",
        'icon': 'note'
    },
    'style-edit-sample': {
        'slug': 'style-edit-sample',
        'filename': 'Style Edit, Sample.docx',
        'title': "Style Edit: Jax's POV (Fantasy Prologue)",
        'subtitle': 'Line & Stylistic Revision',
        'category': 'Line & Stylistic Editing',
        'category_code': 'line',
        'badge_class': 'bg-blue-500/20 text-blue-300 border-blue-500/30',
        'author': 'Grace Zurawell',
        'genre': 'Fantasy Fiction Prologue',
        'description': 'A line and stylistic edit refining narrative cadence, eliminating modifier ambiguity and stacked verbals, enhancing tension, and polishing prose rhythm.',
        'icon': 'style'
    },
    'style-edit-editors-note': {
        'slug': 'style-edit-editors-note',
        'filename': "Style Edit, Sample Editor's Note.docx",
        'title': "Editor's Memo: Style & Line Edit",
        'subtitle': 'Fantasy Prologue Feedback Letter',
        'category': "Editor's Note",
        'category_code': 'line-note',
        'badge_class': 'bg-purple-500/20 text-purple-300 border-purple-500/30',
        'author': 'Grace Zurawell',
        'genre': 'Editorial Feedback Letter',
        'description': "A professional editor's note offering detailed guidance on narrative voice, sentence length variation, clarity considerations, and suspense building.",
        'icon': 'note'
    }
}

def get_portfolio_items():
    """Return list of all portfolio item dicts with metadata."""
    return list(PORTFOLIO_ITEMS.values())

def get_docx_filepath(filename):
    """Find absolute path for docx file across candidate static directories."""
    possible_paths = [
        os.path.join(settings.STATIC_ROOT, 'portfoliofiles', filename),
        os.path.join(settings.BASE_DIR, 'spellbound_project', 'static', 'portfoliofiles', filename),
        os.path.join(settings.BASE_DIR, 'staticfiles', 'portfoliofiles', filename),
    ]
    for p in possible_paths:
        if os.path.exists(p):
            return p
    # Fallback search
    for root_dir in [settings.BASE_DIR, getattr(settings, 'BASE_DIR').parent]:
        for dirpath, _, filenames in os.walk(root_dir):
            if filename in filenames:
                return os.path.join(dirpath, filename)
    return None

def parse_docx(slug):
    item = PORTFOLIO_ITEMS.get(slug)
    if not item:
        return None

    filepath = get_docx_filepath(item['filename'])
    if not filepath or not os.path.exists(filepath):
        return {
            'item': item,
            'html_content': '<p class="text-rose-400">File not found.</p>',
            'comments': [],
            'word_count': 0,
            'comment_count': 0,
            'revision_count': 0,
            'file_size_kb': 0,
            'relative_static_url': f"static/portfoliofiles/{item['filename']}"
        }

    file_size_kb = round(os.path.getsize(filepath) / 1024, 1)
    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

    with zipfile.ZipFile(filepath) as z:
        # Load comments
        comments_dict = {}
        if 'word/comments.xml' in z.namelist():
            ctree = ET.fromstring(z.read('word/comments.xml'))
            for c in ctree.findall('w:comment', ns):
                cid = c.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}id')
                author = c.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}author', 'Grace Zurawell')
                initials = c.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}initials', 'GZ')
                
                text_parts = []
                for p in c.findall('.//w:p', ns):
                    p_txt = ''.join(p.itertext()).strip()
                    if p_txt:
                        text_parts.append(p_txt)
                comments_dict[cid] = {
                    'id': cid,
                    'author': author,
                    'initials': initials,
                    'text': '\n\n'.join(text_parts),
                    'target_text': ''
                }

        # Parse document.xml
        dtree = ET.fromstring(z.read('word/document.xml'))
        body = dtree.find('w:body', ns)

        paragraphs_html = []
        doc_comments_used = set()
        total_words = 0
        total_ins = 0
        total_dels = 0
        comment_targets = {}

        def process_node(node, active_comments, is_ins=False, is_del=False):
            nonlocal total_words, total_ins, total_dels
            html_snippets = []
            tag = node.tag.split('}')[-1]

            if tag == 'commentRangeStart':
                cid = node.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}id')
                if cid in comments_dict:
                    active_comments.add(cid)
                    doc_comments_used.add(cid)
            elif tag == 'commentRangeEnd':
                cid = node.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}id')
                active_comments.discard(cid)
            elif tag == 'ins':
                total_ins += 1
                for child in node:
                    html_snippets.extend(process_node(child, active_comments, is_ins=True, is_del=is_del))
            elif tag == 'del':
                total_dels += 1
                for child in node:
                    html_snippets.extend(process_node(child, active_comments, is_ins=is_ins, is_del=True))
            elif tag == 'r':
                text_elems = node.findall('.//w:t', ns)
                r_text = ''.join([t.text for t in text_elems if t.text])
                if not r_text:
                    del_text_elems = node.findall('.//w:delText', ns)
                    r_text = ''.join([t.text for t in del_text_elems if t.text])

                if r_text:
                    if not is_del:
                        words = r_text.split()
                        total_words += len(words)

                    # Accumulate target text for comments
                    for cid in active_comments:
                        comment_targets[cid] = comment_targets.get(cid, '') + r_text

                    rPr = node.find('w:rPr', ns)
                    bold = rPr is not None and rPr.find('w:b', ns) is not None
                    italic = rPr is not None and rPr.find('w:i', ns) is not None

                    escaped_text = html.escape(r_text)
                    if bold:
                        escaped_text = f'<strong>{escaped_text}</strong>'
                    if italic:
                        escaped_text = f'<em>{escaped_text}</em>'
                    if is_ins:
                        escaped_text = f'<ins class="docx-ins bg-emerald-500/20 text-emerald-300 underline font-medium px-0.5 rounded" title="Added by Editor">{escaped_text}</ins>'
                    if is_del:
                        escaped_text = f'<del class="docx-del bg-rose-500/20 text-rose-300 line-through opacity-75 px-0.5 rounded" title="Deleted by Editor">{escaped_text}</del>'

                    if active_comments:
                        cids_str = ' '.join([f'comment-highlight-{c}' for c in active_comments])
                        cids_attr = ','.join(active_comments)
                        escaped_text = f'<mark class="docx-comment-highlight bg-amber-400/30 text-amber-100 border-b-2 border-amber-400 cursor-pointer hover:bg-amber-400/60 transition-all rounded px-0.5 {cids_str}" data-comment-ids="{cids_attr}">{escaped_text}</mark>'

                    html_snippets.append(escaped_text)
            else:
                for child in node:
                    html_snippets.extend(process_node(child, active_comments, is_ins, is_del))

            return html_snippets

        for p in body.findall('w:p', ns):
            active_comments = set()
            p_snippets = []
            for child in p:
                p_snippets.extend(process_node(child, active_comments))

            p_content = ''.join(p_snippets).strip()
            if not p_content:
                continue

            pPr = p.find('w:pPr', ns)
            pStyle_val = ''
            if pPr is not None:
                pStyle = pPr.find('w:pStyle', ns)
                if pStyle is not None:
                    pStyle_val = pStyle.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val', '')

            if 'Title' in pStyle_val:
                paragraphs_html.append(f'<h1 class="text-2xl sm:text-4xl font-display font-bold text-transparent bg-clip-text bg-gradient-to-r from-magic-gold to-yellow-200 mb-6 mt-4">{p_content}</h1>')
            elif 'Heading1' in pStyle_val or pStyle_val == '1':
                paragraphs_html.append(f'<h2 class="text-xl sm:text-2xl font-display font-bold text-slate-100 mb-4 mt-8 border-b border-white/10 pb-2 flex items-center gap-2"><span class="w-1.5 h-5 bg-magic-gold rounded-full inline-block"></span>{p_content}</h2>')
            elif 'Heading2' in pStyle_val or pStyle_val == '2':
                paragraphs_html.append(f'<h3 class="text-lg sm:text-xl font-display font-semibold text-slate-200 mb-3 mt-6">{p_content}</h3>')
            elif 'List' in pStyle_val or (pPr is not None and pPr.find('w:numPr', ns) is not None):
                paragraphs_html.append(f'<li class="ml-6 list-disc text-slate-300 mb-2 leading-relaxed">{p_content}</li>')
            else:
                paragraphs_html.append(f'<p class="text-slate-300 leading-relaxed mb-5 text-sm sm:text-base font-normal">{p_content}</p>')

        # Populate target text for comments
        used_comments_list = []
        for cid in doc_comments_used:
            if cid in comments_dict:
                cobj = comments_dict[cid]
                cobj['target_text'] = comment_targets.get(cid, '').strip()
                used_comments_list.append(cobj)

        # Sort comments by numeric id if possible
        try:
            used_comments_list.sort(key=lambda x: int(x['id']))
        except ValueError:
            pass

        return {
            'item': item,
            'html_content': ''.join(paragraphs_html),
            'comments': used_comments_list,
            'word_count': total_words,
            'comment_count': len(used_comments_list),
            'revision_count': total_ins + total_dels,
            'file_size_kb': file_size_kb,
            'relative_static_url': f"static/portfoliofiles/{item['filename']}"
        }
