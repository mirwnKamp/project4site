"""Generate items.html and the Gameplay race pages (class.html, elf.html, ...) from the server datapack.

Usage: python tools/generate.py [path/to/L2J_Mobius_14.1_SamuraiCrow]
Default server path: ../L2J_Mobius_14.1_SamuraiCrow (next to this repo).

Sources (read only):
  dist/game/data/stats/items/Custom-*.xml   item stats
  dist/game/data/stats/skills/Custom-*.xml  custom skills
  client/patches/ItemName-eu.txt            item descriptions (what players see in game)
  client/patches/SetItemGrp-eu.txt          armor set bonuses
  dist/game/data/stats/players/skillTrees   which class learns which skill
  client/ (via tools/clientdata.py)         skill names, descriptions and icons as in game (needs Java once)
Layout (header, nav, footer) is taken from wiki.html, so edit the menu there.
"""
import glob
import html
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

import clientdata

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


def card(title, sub, body, icon=''):
    sub = f'<div class="p4-card__sub">{sub}</div>' if sub else ''
    head = (f'<div class="p4-card__head">{icon}<div><div class="p4-card__title">{title}</div>{sub}</div></div>' if icon
            else f'<div class="p4-card__title">{title}</div>{sub}')
    return f'<div class="p4-card">{head}<div class="p4-card__body">{body}</div></div>'


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


def items_page(client):
    items = load_items()
    icons = client.item_icons()
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
        rows = ''.join(f'<li class="p4-piece">{item_icon(client, icons, p["id"], 32)}<div>{html.escape(p["name"])}{stats_line(p["stats"])}</div></li>'
                       for p in pieces)
        desc = text(names.get(first['id'], {}).get('description'))
        bonus = ''.join(f'<li>{text(b)}</li>' for b in re.findall(r'\[([^\]]+)\]', s.get('essential_setitem_desc', '')))
        enchant = ''.join(f'<li>{text(b)}</li>' for b in re.findall(r'\{\d+;\[([^\]]*)\]\}', s.get('enchant_setitem_condition', '')))
        body = (f'<p>{desc}</p><ul class="p4-list">{rows}</ul>'
                + (f'<div class="p4-card__label">Set bonus</div><ul class="p4-list">{bonus}</ul>' if bonus else '')
                + (f'<div class="p4-card__label">Enchant set bonus</div><ul class="p4-list">{enchant}</ul>' if enchant else ''))
        set_cards.setdefault(first['armor'], []).append(card(title, html.escape(first['add']), body, item_icon(client, icons, first['id'], 48)))

    jewels = shop_ids(JEWEL_SHOP)

    def simple(pred):
        out = []
        for i in items:
            if i['id'] in in_set or not pred(i):
                continue
            desc = text(names.get(i['id'], {}).get('description'))
            out.append(card(html.escape(i['name']), html.escape(i['add']), f'{stats_line(i["stats"])}<p>{desc}</p>',
                            item_icon(client, icons, i['id'], 48)))
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
ICONS = os.path.join(SITE, 'icons')
ARCHETYPES = ['Sigel', 'Tyrr', 'Othell', 'Yul', 'Feoh', 'Iss', 'Wynn', 'Aeore']
# Gameplay pages, one per race (the old race page names, so links keep working). Awakened classes get their race from
# their 3rd class (parentClassId); the newer races are listed by their final class id.
RACES = [('class', 'Human', range(88, 99)), ('elf', 'Elf', range(99, 106)), ('darkElf', 'Dark Elf', range(106, 113)),
         ('orc', 'Orc', range(113, 117)), ('dwarf', 'Dwarf', range(117, 119)), ('kamael', 'Kamael', range(131, 135)),
         ('ertheia', 'Ertheia', (188, 189)), ('samurai', 'Samurai', (268,)), ('warg', 'Warg', (259,)),
         ('shinemaker', 'Shine Maker', (235,))]
DESCRIPTIONS = os.path.join(SITE, 'tools', 'class_descriptions.json')  # hand-written class texts of the old Gameplay pages


def class_trees():
    """classId -> dict(name, arch, parent, skills {id: max level}, folder) from the class skill trees."""
    trees = {}
    for f in glob.glob(os.path.join(TREES, '*', '*.xml')):
        src = open(f, encoding='utf-8').read()
        folder = os.path.basename(os.path.dirname(f))
        for st in ET.fromstring(src).iter('skillTree'):
            if st.get('type') != 'classSkillTree':
                continue
            cid = st.get('classId')
            arch = ''
            if folder == '4rthClass':  # file names are spelled right, the comments not always: TyrrDreadnought -> Tyrr, Dreadnought
                arch, name = re.sub(r"(?<=[a-z'])(?=[A-Z])", ' ', os.path.basename(f)[:-4]).split(' ', 1)
            else:
                m = re.search(r'<!--\s*([^<>]+?)\s*-->\s*<skillTree[^>]*classId="%s"' % cid, src)
                name = m.group(1) if m else re.sub(r'\d+$', '', os.path.basename(f)[:-4])  # Warg4.xml -> Warg
            skills = {}
            for sk in st.iter('skill'):
                skills[sk.get('skillId')] = max(skills.get(sk.get('skillId'), 0), int(sk.get('skillLevel')))
            trees[cid] = dict(name=name, arch=arch, parent=st.get('parentClassId'), skills=skills, folder=folder)
    return trees


def final_classes(trees, custom):
    """classId -> {skill id: (level, how)} for the classes players end up with: the skills of the class and its parents,
    plus the custom skills of a transformation or servitor that one of them calls (Golem Armor, summons)."""
    parents = {t['parent'] for t in trees.values() if t['parent']}
    out = {}
    for cid, t in trees.items():
        # Players are awakened (4rthClass) or one of the newer races; Death Knight is off on this server.
        if cid in parents or t['folder'] not in ('4rthClass', 'Samurai', 'Warg', 'Ertheia', 'ShineMaker'):
            continue
        c, learned = cid, {}
        while c in trees:
            for sid, lv in trees[c]['skills'].items():
                learned.setdefault(sid, (lv, ''))
            c = trees[c]['parent']
        out[cid] = learned
    transforms = {}
    for f in glob.glob(os.path.join(TRANSFORMS, '*.xml')):
        for tr in ET.parse(f).getroot().iter('transform'):
            transforms[tr.get('id')] = {sk.get('id') for sk in tr.iter('skill')}
    servitors = {}
    for f in glob.glob(os.path.join(NPCS, 'custom', '*.xml')):
        for npc in ET.parse(f).getroot().iter('npc'):
            servitors[npc.get('id')] = (npc.get('name'), {sk.get('id') for sk in npc.iter('skill')})
    owned = set().union(*out.values())
    for f in glob.glob(os.path.join(SKILLS, '*.xml')):
        src = open(f, encoding='utf-8').read()
        if '<npcId>' not in src and 'ransform' not in src:
            continue
        for m in re.finditer(r'<skill id="(\d+)"(.*?)</skill>', src, re.S):
            sid, xml = m.group(1), m.group(2)
            if sid not in owned:
                continue
            subs = [(x, 'Transformation skill') for tid in re.findall(r'<transform(?:ation)?Id>(\d+)<', xml) for x in transforms.get(tid, ())]
            for nid in re.findall(r'<npcId>(\d+)<', xml):
                sname, ids = servitors.get(nid, ('', set()))
                subs += [(x, f'Servitor skill ({sname})') for x in ids]
            for sub, how in subs:
                if sub in custom:
                    for learned in out.values():
                        if sid in learned:
                            learned.setdefault(sub, (99, how))
    return out


def icon_img(client, icon, size):
    f = client.icon_png(icon, ICONS)
    return (f'<img class="p4-ico-{size}" src="icons/{f}" alt="" width="{size}" height="{size}" loading="lazy">' if f
            else f'<span class="p4-ico-{size} p4-ico-none"></span>')


def item_icon(client, icons, iid, size):
    return icon_img(client, icons.get(iid), size)


def skill_card(client, sid, info, names, icons, custom):
    """(name, passive, new, html) of one skill at the highest level the class reaches, or None (no client text)."""
    lv, how = info
    levels = sorted((int(k) for k in names.get(sid, {})), reverse=True)
    if not levels:
        return None
    lv = next((l for l in levels if l <= lv), levels[-1])
    row = names[sid][str(lv)]
    name = client._value(row['name'])
    if not name or name == 'None':
        return None
    # Some levels have no text of their own: take the closest lower level that has one.
    textrow = next((names[sid][str(l)] for l in levels if l <= lv and client._value(names[sid][str(l)]['desc'])), row)
    desc = client._value(textrow['desc'])
    for n, p in enumerate(client._value(textrow['desc_param']).split(';'), 1):
        desc = desc.replace(f'$s{n}', p)
    icon, op = icons.get((sid, str(lv)), icons.get((sid, '1'), ('', '')))
    new = sid in custom
    badges = (f'<span class="p4-skill__lv">Lv. {lv}</span>' if lv > 1 else '') + ('<span class="p4-badge">New</span>' if new else '')
    how_html = f'<div class="p4-skill__how">{html.escape(how)}</div>' if how else ''
    row_html = (f'<div class="p4-skill{" is-new" if new else ""}">{icon_img(client, icon, 40)}<div class="p4-skill__body">'
                f'<div class="p4-skill__name">{html.escape(name)}{badges}</div>{how_html}'
                f'<div class="p4-skill__desc">{text("[" + desc + "]")}</div></div></div>')
    return name, op == '2', new, row_html


def gameplay_pages(client):
    trees = class_trees()
    custom = set()
    for f in glob.glob(os.path.join(SKILLS, 'Custom-*.xml')):
        if not SKILL_EXCLUDE.search(os.path.basename(f)) and 'Eigis' not in f:
            custom |= {sk.get('id') for sk in ET.parse(f).getroot().iter('skill')}
    finals = final_classes(trees, custom)
    names = {}
    for k, r in client.rows('SkillName-eu', ('skill_id', 'skill_level', 'skill_sublevel'), ('name', 'desc', 'desc_param')).items():
        if k[2] in ('0', ''):
            names.setdefault(k[0], {})[k[1]] = r
    icons = client.skill_icons()
    texts = json.load(open(DESCRIPTIONS, encoding='utf-8'))
    strip = lambda cur: ''.join(f'<a href="{f}" class="race-btn{" active" if f == cur else ""}"{" aria-current=page" if f == cur else ""}>{r}</a>'
                                for f, r, _ in RACES)
    pages = []
    for fname, race, ids in RACES:
        tabs = []
        members = [c for c in finals if (int(trees[c]['parent']) if trees[c]['folder'] == '4rthClass' else int(c)) in ids]
        members.sort(key=lambda c: (next((i for i, a in enumerate(ARCHETYPES) if a == trees[c]['arch']), 99), trees[c]['name']))
        for cid in members:
            t = trees[cid]
            rows = {}
            for sid, info in finals[cid].items():
                r = skill_card(client, sid, info, names, icons, custom)
                if r and (r[0] not in rows or (r[2] and not rows[r[0]][2])):  # one row per name (weapon variants), the custom one wins
                    rows[r[0]] = r
            ordered = sorted(rows.values(), key=lambda r: (not r[2], r[0]))
            act = [r[3] for r in ordered if not r[1]]
            pas = [r[3] for r in ordered if r[1]]
            new = sum(1 for r in rows.values() if r[2])
            about = texts.get(re.sub(r'[^a-z]', '', t['name'].lower()), {}).get('text', '')
            if about[:1].islower():  # the old texts start after the class name ("is a master craftsman ...")
                about = f'The {t["name"]} {about}'
            body = ((f'<p class="p4-class-about">{html.escape(about)}</p>' if about else '')
                    + '<div class="p4-seg" role="tablist" aria-label="Skills">'
                    + f'<button type="button" class="active" data-seg="active">Active · {len(act)}</button>'
                    + f'<button type="button" data-seg="passive">Passive · {len(pas)}</button></div>'
                    + f'<div class="p4-skills" data-seg-panel="active">{"".join(act)}</div>'
                    + f'<div class="p4-skills" data-seg-panel="passive">{"".join(pas)}</div>')
            sub = ' · '.join(x for x in (t['arch'], f'{len(rows)} skills', f'{new} new' if new else '') if x)
            full = f'{t["arch"]} {t["name"]}'.strip()
            tabs.append(tab(re.sub(r'\W', '', t['name']), html.escape(t['name']), html.escape(sub),
                            html.escape(full) + (f' · {new} new skills on Project4' if new else ''), body))
        pages.append((fname + '.html', ('Gameplay', tabs, '', f'<nav class="race-strip" aria-label="Races">{strip(fname)}</nav>')))
    return pages


def write(filename, page):
    title, tabs = page[:2]
    note = page[2] if len(page) > 2 else ''
    strip = page[3] if len(page) > 3 else ''
    layout = open(os.path.join(SITE, 'wiki.html'), encoding='utf-8').read()
    start = layout.index('<section class="section inner-page">')
    end = layout.index('</section>', start) + len('</section>')
    head = layout[:start].replace('</head>', '<!-- Generated by tools/generate.py from the server datapack. Do not edit by hand. -->\n</head>', 1)
    if strip:  # the Gameplay pages keep their own header video
        head = head.replace('wiki-page/human.webm', 'class-page/chars.webm')
    center = (f'<div class="section__title-center race-container">{strip}</div>' if strip
              else f'<div class="section__title-center"><div class="section__title-center-big">{title}</div></div>')
    section = (f'<section class="section inner-page"><div class="section__title flex-cc"><div class="section__title-left"></div>'
               f'{center}<div class="section__title-right"></div><div class="section__title-small"></div></div>'
               f'<div class="content-area">{note}<div class="wiki flex-sbs"><div class="wiki__nav">{"".join(n for n, _ in tabs)}</div>'
               f'<div class="wiki__box">{"".join(b for _, b in tabs)}</div></div></div></section>')
    out = f'{head}{section}{layout[end:]}'
    with open(os.path.join(SITE, filename), 'w', encoding='utf-8', newline='\n') as f:
        f.write(out)
    print(filename, {re.search(r'data-name-tab="(\w+)"', b).group(1): b.count('class="p4-card"') + b.count('class="p4-skill') for _, b in tabs})


if __name__ == '__main__':
    if not os.path.isdir(ITEMS):
        sys.exit(f'Server datapack not found: {SERVER}')
    client = clientdata.Client(SERVER)
    write('items.html', items_page(client))
    for name, page in gameplay_pages(client):
        write(name, page)
