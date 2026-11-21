"""Generate items.html and skills.html from the Samurai Crow server datapack.

Usage: python tools/generate.py [path/to/L2J_Mobius_14.1_SamuraiCrow]
Default server path: ../L2J_Mobius_14.1_SamuraiCrow (next to this repo).

Sources (read only):
  dist/game/data/stats/items/Custom-*.xml   item stats
  dist/game/data/stats/skills/Custom-*.xml  custom skills
  client/patches/ItemName-eu.txt            item descriptions (what players see in game)
  client/patches/SetItemGrp-eu.txt          armor set bonuses
  client/patches/SkillName-eu.txt           skill names/descriptions
Layout (header, nav, footer) is taken from wiki.html, so edit the menu there.
"""
import glob
import html
import os
import re
import sys
import xml.etree.ElementTree as ET

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(SITE, '..', 'L2J_Mobius_14.1_SamuraiCrow'))
ITEMS = os.path.join(SERVER, 'dist', 'game', 'data', 'stats', 'items')
SKILLS = os.path.join(SERVER, 'dist', 'game', 'data', 'stats', 'skills')
PATCHES = os.path.join(SERVER, 'client', 'patches')

ITEM_FILES = ['Custom-Armors-*.xml', 'Custom-Shields-*.xml', 'Custom-Jewels-*.xml', 'Custom-Accessories-98000-*.xml']
# Skill files that belong to items (shown through the item descriptions) or to systems, not to classes.
SKILL_EXCLUDE = re.compile(r'Jewel|Armor|Talisman|EpicWeapon|Potions|SchemeBuffer|Page|Accessories|Zone|Starter|Ability')
STAT_NAMES = {'pDef': 'P. Def.', 'mDef': 'M. Def.', 'sDef': 'Shield Def.', 'rShld': 'Shield Rate', 'rEvas': 'Evasion',
              'pAtk': 'P. Atk.', 'mAtk': 'M. Atk.', 'maxHp': 'Max HP', 'maxMp': 'Max MP'}


def read_rows(name, begin):
    """Client .txt rows as dicts; values keep their [] / {} wrapping stripped of one level."""
    rows = []
    with open(os.path.join(PATCHES, name), encoding='utf-8') as f:
        for line in f:
            if not line.startswith(begin):
                continue
            row = {}
            for part in line.rstrip('\n').split('\t'):
                if '=' in part:
                    k, v = part.split('=', 1)
                    row[k] = v
            rows.append(row)
    return rows


def unwrap(v):
    v = v or ''
    return v[1:-1] if len(v) >= 2 and v[0] in '[{' else v


def text(v):
    """Client text -> safe HTML."""
    return html.escape(unwrap(v).replace('%%', '%')).replace('\\n', '<br>')


def load_items():
    items = []
    for pat in ITEM_FILES:
        for f in sorted(glob.glob(os.path.join(ITEMS, pat))):
            for it in ET.parse(f).getroot().iter('item'):
                sets = {s.get('name'): s.get('val') for s in it.findall('set')}
                items.append({
                    'id': it.get('id'),
                    'name': it.get('name'),
                    'add': it.get('additionalName') or '',
                    'armor': sets.get('armor_type') or '',
                    'part': sets.get('bodypart') or '',
                    'grade': sets.get('crystal_type') or '',
                    'stats': [(st.get('type'), st.text) for st in it.iter('stat')],
                })
    return items


def card(title, sub, body):
    sub = f'<div class="p4-card__sub">{sub}</div>' if sub else ''
    return f'<div class="p4-card"><div class="p4-card__title">{title}</div>{sub}<div class="p4-card__body">{body}</div></div>'


def stats_line(stats):
    shown = [f'{STAT_NAMES.get(k, k)} {v}' for k, v in stats if k in STAT_NAMES]
    return f'<div class="p4-card__stats">{" · ".join(shown)}</div>' if shown else ''


def tab(key, name, desc, intro, cards):
    nav = (f'<a href="#" class="wiki__nav-item flex-sc" data-open-tab="{key}"><div class="wiki__nav-item-icon flex-cc">'
           f'<i class="ra ra-scroll-unfurled"></i></div><div class="wiki__nav-item-info"><div class="wiki__nav-item-name">{name}</div>'
           f'<div class="wiki__nav-item-desc">{desc}</div></div></a>')
    box = (f'<div class="wiki__content" data-name-tab="{key}"><div class="wiki__content-title flex-sc"><div class="wiki__content-title-icon flex-cc">'
           f'<i class="ra ra-scroll-unfurled"></i></div><div class="wiki__content-title-info"><div class="wiki__content-title-name">{name}</div>'
           f'<div class="wiki__content-title-desc">{intro}</div></div></div><div class="p4-grid">{"".join(cards)}</div></div>')
    return nav, box


def items_page():
    items = load_items()
    names = {r['id']: r for r in read_rows('ItemName-eu.txt', 'item_name_begin')}
    sets = read_rows('SetItemGrp-eu.txt', 'setitem_group_begin')
    by_id = {i['id']: i for i in items}
    in_set = set()
    set_cards = {'HEAVY': [], 'LIGHT': [], 'MAGIC': []}
    for s in sets:
        piece_ids = re.findall(r'\d+', s.get('essential_setitem_id', ''))
        pieces = [by_id[i] for i in dict.fromkeys(piece_ids) if i in by_id]
        if not pieces or not pieces[0]['armor']:
            continue
        in_set.update(p['id'] for p in pieces)
        first = pieces[0]
        tier = first['name'].split()[0]
        title = html.escape(f'{tier} {first["armor"].title().replace("Magic", "Robe")} Set')
        rows = ''.join(f'<li>{html.escape(p["name"])}{stats_line(p["stats"])}</li>' for p in pieces)
        desc = text(names.get(first['id'], {}).get('description'))
        bonus = ''.join(f'<li>{text(b)}</li>' for b in re.findall(r'\[([^\]]+)\]', s.get('essential_setitem_desc', '')))
        enchant = ''.join(f'<li>{text(b)}</li>' for b in re.findall(r'\{\d+;\[([^\]]*)\]\}', s.get('enchant_setitem_condition', '')))
        body = (f'<p>{desc}</p><ul class="p4-list">{rows}</ul>'
                + (f'<div class="p4-card__label">Set bonus</div><ul class="p4-list">{bonus}</ul>' if bonus else '')
                + (f'<div class="p4-card__label">Enchant set bonus</div><ul class="p4-list">{enchant}</ul>' if enchant else ''))
        set_cards.setdefault(first['armor'], []).append(card(title, html.escape(first['add']), body))

    def simple(pred):
        out = []
        for i in items:
            if i['id'] in in_set or not pred(i):
                continue
            desc = text(names.get(i['id'], {}).get('description'))
            out.append(card(html.escape(i['name']), html.escape(i['add']), f'{stats_line(i["stats"])}<p>{desc}</p>'))
        return out

    tabs = [
        tab('heavy', 'Heavy Armors', 'Heavy armor sets', 'Heavy armor sets and their bonuses.', set_cards['HEAVY']),
        tab('light', 'Light Armors', 'Light armor sets', 'Light armor sets and their bonuses.', set_cards['LIGHT']),
        tab('robe', 'Robe Armors', 'Robe armor sets', 'Robe armor sets and their bonuses.', set_cards['MAGIC']),
        tab('other', 'Shields & Sigils', 'Shields, sigils and single pieces', 'Shields, sigils and armor pieces outside a set.',
            simple(lambda i: i['part'] == 'lhand' or (i['armor'] and i['part'] not in ('hair', 'hair2')))),
        tab('jewels', 'Jewelry', 'Rings, earrings, necklaces', 'Two identical rings or earrings do not stack.',
            simple(lambda i: i['part'] in ('rfinger;lfinger', 'rear;lear', 'neck'))),
        tab('accessories', 'Accessories', 'Hair accessories', 'Hair accessories (left and right slot).',
            simple(lambda i: i['part'] in ('hair', 'hair2'))),
    ]
    return 'Items', tabs


def skills_page():
    rows = read_rows('SkillName-eu.txt', 'skill_begin')
    by_skill = {}
    for r in rows:
        by_skill.setdefault(r['skill_id'], []).append(r)
    groups = {}  # group name -> cards; files like SamuraiNinja and SamuraiNinja2 share one tab
    for f in sorted(glob.glob(os.path.join(SKILLS, 'Custom-*.xml'))):
        base = os.path.basename(f)
        if SKILL_EXCLUDE.search(base):
            continue
        group = re.sub(r'^Custom-|(-\d+)+\.xml$|\.xml$', '', base)
        group = re.sub(r'Skills$|\d+$', '', group)
        group = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', group)
        cards = groups.setdefault(group, [])
        for sk in ET.parse(f).getroot().iter('skill'):
            levels = by_skill.get(sk.get('id'))
            if not levels:
                continue
            first = levels[0]
            last = max(levels, key=lambda r: (int(r['skill_level']), int(r.get('skill_sublevel', 0))))
            desc = unwrap(last.get('desc')) or unwrap(first.get('desc'))
            params = [p for p in unwrap(last.get('desc_param')).split(';')]
            for n, p in enumerate(params, 1):
                desc = desc.replace(f'$s{n}', p)
            lv = int(last['skill_level'])
            cards.append(card(text(first.get('name')), f'Max level {lv}' if lv > 1 else '', f'<p>{text("[" + desc + "]")}</p>' if desc else ''))
    tabs = [tab(re.sub(r'\W', '', g).lower(), html.escape(g), f'{len(c)} skills', 'Custom skills of this server.', c)
            for g, c in groups.items() if c]
    return 'Skills', tabs


def write(filename, page):
    title, tabs = page
    layout = open(os.path.join(SITE, 'wiki.html'), encoding='utf-8').read()
    start = layout.index('<section class="section inner-page">')
    end = layout.index('</section>', start) + len('</section>')
    head = layout[:start].replace('</head>', '<!-- Generated by tools/generate.py from the server datapack. Do not edit by hand. -->\n'
                                  '<link rel="stylesheet" href="scripts/generated.css">\n</head>', 1)
    section = (f'<section class="section inner-page"><div class="section__title flex-cc"><div class="section__title-left"></div>'
               f'<div class="section__title-center"><div class="section__title-center-big">{title}</div></div>'
               f'<div class="section__title-right"></div><div class="section__title-small"></div></div>'
               f'<div class="content-area"><div class="wiki flex-sbs"><div class="wiki__nav">{"".join(n for n, _ in tabs)}</div>'
               f'<div class="wiki__box">{"".join(b for _, b in tabs)}</div></div></div></section>')
    out = f'{head}{section}{layout[end:]}'
    with open(os.path.join(SITE, filename), 'w', encoding='utf-8', newline='\n') as f:
        f.write(out)
    print(filename, {re.search(r'data-name-tab="(\w+)"', b).group(1): b.count('class="p4-card"') for _, b in tabs})


if __name__ == '__main__':
    if not os.path.isdir(ITEMS):
        sys.exit(f'Server datapack not found: {SERVER}')
    write('items.html', items_page())
    write('skills.html', skills_page())
