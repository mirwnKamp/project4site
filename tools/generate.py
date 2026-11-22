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
# Stage 1 of the server: only the Epic tier is shown (Mythic / Eternal come with a later stage).
TIER = 'Epic'
# Jewels: the ones Paulina sells in the Epic jewel shop (the older boss jewels are hidden there).
JEWEL_SHOP = os.path.join(SERVER, 'dist', 'game', 'data', 'multisell', '3678361.xml')
STAGE_NOTE = ('<div class="message flex-sc green p4-stage"><div class="message__icon flex-cc"><i class="fas fa-info"></i></div>'
              '<div class="message__info"><b>Project4 grows in stages.</b> Stage 1 is the introduction: easy farm and fast gear-up '
              'on purpose, so everyone gets to know the server. This page shows the Stage 1 gear. Stage 2 comes later.</div></div>')
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


def shop_ids(path):
    """Item ids a multisell sells (commented-out entries are hidden in game, so skipped)."""
    xml = re.sub(r'<!--.*?-->', '', open(path, encoding='utf-8').read(), flags=re.S)
    return set(re.findall(r'<production id="(\d+)"', xml))


def card(title, sub, body):
    sub = f'<div class="p4-card__sub">{sub}</div>' if sub else ''
    return f'<div class="p4-card"><div class="p4-card__title">{title}</div>{sub}<div class="p4-card__body">{body}</div></div>'


def stats_line(stats):
    shown = [f'{STAT_NAMES.get(k, k)} {v}' for k, v in stats if k in STAT_NAMES]
    return f'<div class="p4-card__stats">{" · ".join(shown)}</div>' if shown else ''


def grid(cards, attrs=''):
    return f'<div class="p4-grid"{attrs}>{"".join(cards)}</div>'


def tab(key, name, desc, intro, cards):
    nav = (f'<a href="#" class="wiki__nav-item flex-sc" data-open-tab="{key}"><div class="wiki__nav-item-icon flex-cc">'
           f'<i class="ra ra-scroll-unfurled"></i></div><div class="wiki__nav-item-info"><div class="wiki__nav-item-name">{name}</div>'
           f'<div class="wiki__nav-item-desc">{desc}</div></div></a>')
    box = (f'<div class="wiki__content" data-name-tab="{key}"><div class="wiki__content-title flex-sc"><div class="wiki__content-title-icon flex-cc">'
           f'<i class="ra ra-scroll-unfurled"></i></div><div class="wiki__content-title-info"><div class="wiki__content-title-name">{name}</div>'
           f'<div class="wiki__content-title-desc">{intro}</div></div></div>{cards if isinstance(cards, str) else grid(cards)}</div>')
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
        if not pieces or not pieces[0]['armor'] or not pieces[0]['name'].startswith(TIER + ' '):
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

    jewels = shop_ids(JEWEL_SHOP)

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
            simple(lambda i: (i['part'] == 'lhand' or (i['armor'] and i['part'] not in ('hair', 'hair2'))) and i['name'].startswith(TIER + ' '))),
        tab('jewels', 'Jewelry', 'Rings, earrings, necklaces', 'Two identical rings or earrings do not stack.',
            simple(lambda i: i['id'] in jewels)),
        # Two slot buttons (ui.js shows one grid at a time; without JS both grids stay visible).
        tab('accessories', 'Accessories', 'Hair accessories, right and left slot', 'Hair accessories: one for each slot.',
            '<div class="p4-seg" role="tablist" aria-label="Slot"><button type="button" class="active" data-seg="right">Right Slot</button>'
            '<button type="button" data-seg="left">Left Slot</button></div>'
            + grid(simple(lambda i: i['part'] == 'hair'), ' data-seg-panel="right"')
            + grid(simple(lambda i: i['part'] == 'hair2'), ' data-seg-panel="left"')),
    ]
    return 'Items', tabs, STAGE_NOTE


TREES = os.path.join(SERVER, 'dist', 'game', 'data', 'stats', 'players', 'skillTrees')
TRANSFORMS = os.path.join(SERVER, 'dist', 'game', 'data', 'stats', 'transformations')
NPCS = os.path.join(SERVER, 'dist', 'game', 'data', 'stats', 'npcs')
ARCHETYPES = ['Sigel', 'Tyrr', 'Othell', 'Yul', 'Feoh', 'Iss', 'Wynn', 'Aeore']


def class_trees():
    """classId -> (display name, parent classId, skill ids) from the class skill trees."""
    trees = {}
    for f in glob.glob(os.path.join(TREES, '*', '*.xml')):
        src = open(f, encoding='utf-8').read()
        for st in ET.fromstring(src).iter('skillTree'):
            if st.get('type') != 'classSkillTree':
                continue
            cid = st.get('classId')
            if os.path.basename(os.path.dirname(f)) == '4rthClass':  # file names are spelled right, the comments not always
                name = re.sub(r"(?<=[a-z'])(?=[A-Z])", ' ', os.path.basename(f)[:-4])
            else:
                m = re.search(r'<!--\s*([^<>]+?)\s*-->\s*<skillTree[^>]*classId="%s"' % cid, src)
                name = m.group(1) if m else re.sub(r'\d+$', '', os.path.basename(f)[:-4])  # Warg4.xml -> Warg
            trees[cid] = (name, st.get('parentClassId'), {sk.get('skillId') for sk in st.iter('skill')})
    return trees


def skill_owners(custom):
    """Custom skill id -> {class name: how it is learned}. Final classes only, with the skills of their parent classes.
    Also the skills of a transformation or a servitor that a class skill calls (Golem Armor, summons)."""
    trees = class_trees()
    parents = {p for _, p, _ in trees.values() if p}
    owners = {}
    for cid, (name, _, _) in trees.items():
        if cid in parents:
            continue
        c, learned = cid, set()
        while c in trees:
            learned |= trees[c][2]
            c = trees[c][1]
        for sid in learned:
            owners.setdefault(sid, {})[name] = ''
    transforms = {}
    for f in glob.glob(os.path.join(TRANSFORMS, '*.xml')):
        for tr in ET.parse(f).getroot().iter('transform'):
            transforms[tr.get('id')] = {sk.get('id') for sk in tr.iter('skill')}
    servitors = {}
    for f in glob.glob(os.path.join(NPCS, 'custom', '*.xml')):
        for npc in ET.parse(f).getroot().iter('npc'):
            servitors[npc.get('id')] = (npc.get('name'), {sk.get('id') for sk in npc.iter('skill')})
    # Every skill a class learns (retail ones too: the summon skills) may call a transformation or a servitor.
    calls = {}
    for f in glob.glob(os.path.join(SKILLS, '*.xml')):
        src = open(f, encoding='utf-8').read()
        if '<npcId>' not in src and 'ransform' not in src:
            continue
        for m in re.finditer(r'<skill id="(\d+)"(.*?)</skill>', src, re.S):
            if m.group(1) in owners and ('<npcId>' in m.group(2) or 'ransform' in m.group(2)):
                calls[m.group(1)] = calls.get(m.group(1), '') + m.group(2)
    for sid, xml in calls.items():
        classes = dict(owners[sid])
        for tid in re.findall(r'<transform(?:ation)?Id>(\d+)<', xml):
            for sub in transforms.get(tid, ()) & set(custom):
                for c in classes:
                    owners.setdefault(sub, {}).setdefault(c, 'Transformation skill')
        for nid in re.findall(r'<npcId>(\d+)<', xml):
            sname, subs = servitors.get(nid, ('', set()))
            for sub in subs & set(custom):
                for c in classes:
                    owners.setdefault(sub, {}).setdefault(c, f'Servitor skill ({sname})' if sname else 'Servitor skill')
    return {sid: c for sid, c in owners.items() if sid in custom}


def skills_page():
    rows = read_rows('SkillName-eu.txt', 'skill_begin')
    by_skill = {}
    for r in rows:
        by_skill.setdefault(r['skill_id'], []).append(r)
    custom = {}  # id -> xml; item, system and Eigis Rare (weapon) skills are not class skills
    for f in sorted(glob.glob(os.path.join(SKILLS, 'Custom-*.xml'))):
        base = os.path.basename(f)
        if SKILL_EXCLUDE.search(base) or 'Eigis' in base:
            continue
        for sk in ET.parse(f).getroot().iter('skill'):
            custom[sk.get('id')] = ET.tostring(sk, encoding='unicode')
    by_class = {}
    for sid, classes in skill_owners(custom).items():
        levels = by_skill.get(sid)
        if not levels:
            continue
        first = levels[0]
        last = max(levels, key=lambda r: (int(r['skill_level']), int(r.get('skill_sublevel', 0))))
        desc = unwrap(last.get('desc')) or unwrap(first.get('desc'))
        for n, p in enumerate(unwrap(last.get('desc_param')).split(';'), 1):
            desc = desc.replace(f'$s{n}', p)
        lv = int(last['skill_level'])
        for cname, how in classes.items():
            sub = ' · '.join(x for x in (how, f'Max level {lv}' if lv > 1 else '') if x)
            by_class.setdefault(cname, []).append(
                (how, text(first.get('name')), card(text(first.get('name')), sub, f'<p>{text("[" + desc + "]")}</p>' if desc else '')))
    order = lambda n: (next((i for i, a in enumerate(ARCHETYPES) if n.startswith(a + ' ')), len(ARCHETYPES)), n)
    tabs = []
    for cname in sorted(by_class, key=order):
        cards = [c for _, _, c in sorted(by_class[cname], key=lambda x: (x[0] != '', x[0], x[1]))]
        tabs.append(tab(re.sub(r'\W', '', cname).lower(), html.escape(cname), f'{len(cards)} new skills',
                        f'New and reworked skills of the {html.escape(cname)}.', cards))
    return 'Skills', tabs


def write(filename, page):
    title, tabs = page[:2]
    note = page[2] if len(page) > 2 else ''
    layout = open(os.path.join(SITE, 'wiki.html'), encoding='utf-8').read()
    start = layout.index('<section class="section inner-page">')
    end = layout.index('</section>', start) + len('</section>')
    head = layout[:start].replace('</head>', '<!-- Generated by tools/generate.py from the server datapack. Do not edit by hand. -->\n</head>', 1)
    section = (f'<section class="section inner-page"><div class="section__title flex-cc"><div class="section__title-left"></div>'
               f'<div class="section__title-center"><div class="section__title-center-big">{title}</div></div>'
               f'<div class="section__title-right"></div><div class="section__title-small"></div></div>'
               f'<div class="content-area">{note}<div class="wiki flex-sbs"><div class="wiki__nav">{"".join(n for n, _ in tabs)}</div>'
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
