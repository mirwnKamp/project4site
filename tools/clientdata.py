"""Client data for the site generator: skill / item names, descriptions and icons as the players see them.

The retail .dat files (client/original/system/eu) are unpacked once with the server repo's packer
(client/tools/l2clientdat, needs Java) into tools/.cache/, and the server repo's client patches
(client/patches/*.txt) are applied on top, the same way client/build.sh does. Icons come from
SysTextures/Icon.utx with the custom icons of client/icons/Icon.txt, decoded to PNG (DXT1 only).
"""
import glob
import os
import re
import shutil
import struct
import subprocess
import sys
import zlib

CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.cache')
DATS = ['Skillgrp', 'SkillName-eu', 'Armorgrp', 'Weapongrp', 'EtcItemgrp', 'L2GameDataName']


class Client:
    def __init__(self, server):
        self.client = os.path.join(server, 'client')
        self.txt = os.path.join(CACHE, 'txt')
        self.utx = os.path.join(CACHE, 'Icon.utx')
        self._unpack()
        sys.path.insert(0, os.path.join(self.client, 'tools'))
        import iconpatch  # server repo: Icon.utx reader
        self.ip = iconpatch
        _, self.pkg = iconpatch.decrypt(self.utx)
        self.textures = iconpatch.exports(self.pkg)
        self.names = [re.search(r'name=\[(.*)\]\tname_end', l).group(1)
                      for l in open(os.path.join(self.txt, 'L2GameDataName.txt'), encoding='utf-8')]

    def _unpack(self):
        """Unpack the retail .dat files and build the patched Icon.utx, once (delete tools/.cache to redo)."""
        if all(os.path.exists(os.path.join(self.txt, d + '.txt')) for d in DATS) and os.path.exists(self.utx):
            return
        tool = os.path.join(self.client, 'tools', 'l2clientdat')
        work = os.path.join(CACHE, 'work')
        shutil.rmtree(work, ignore_errors=True)
        os.makedirs(os.path.join(work, 'bin'))
        os.makedirs(os.path.join(work, 'dat'))
        sources = [os.path.relpath(p, os.path.join(tool, 'java')) for p in glob.glob(os.path.join(tool, 'java', '**', '*.java'), recursive=True)]
        subprocess.run(['javac', '-nowarn', '-encoding', 'UTF-8', '-d', os.path.join(work, 'bin')] + sources,
                       cwd=os.path.join(tool, 'java'), check=True)
        for d in DATS:
            shutil.copy(os.path.join(self.client, 'original', 'system', 'eu', d + '.dat'), os.path.join(work, 'dat'))
        os.makedirs(os.path.join(tool, 'dist', 'log'), exist_ok=True)
        subprocess.run(['java', '-Xmx6g', '-cp', os.path.join(work, 'bin'), 'org.l2jmobius.Headless', 'unpack', 'Samurai Crow', self.txt]
                       + [os.path.join(work, 'dat', d + '.dat') for d in DATS], cwd=os.path.join(tool, 'dist'), check=True,
                       stdout=subprocess.DEVNULL)
        subprocess.run([sys.executable, '-I', os.path.join(self.client, 'tools', 'iconpatch.py'),
                        os.path.join(self.client, 'original', 'SysTextures', 'Icon.utx'), self.utx, 'Icon.txt'],
                       cwd=os.path.join(self.client, 'icons'), check=True, stdout=subprocess.DEVNULL)
        shutil.rmtree(work, ignore_errors=True)

    def _value(self, v):
        """[<StrID:N>] -> the string, [text] -> text."""
        v = v or ''
        m = re.fullmatch(r'\[<StrID:(\d+)>\]', v)
        if m:
            return self.names[int(m.group(1))]
        return v[1:-1] if len(v) >= 2 and v[0] == '[' else v

    def rows(self, name, key, fields):
        """Rows of a client table: retail rows, then the server repo's patch rows replace / add by key."""
        out = {}
        pat = {f: re.compile(r'(?:^|\t)%s=([^\t]*)' % re.escape(f)) for f in set(key) | set(fields)}
        for path in (os.path.join(self.txt, name + '.txt'), os.path.join(self.client, 'patches', name + '.txt')):
            if not os.path.exists(path):
                continue
            for line in open(path, encoding='utf-8'):
                vals = {}
                for f, p in pat.items():
                    m = p.search(line)
                    vals[f] = m.group(1) if m else ''
                if not vals[key[0]]:
                    continue
                out[tuple(vals[k] for k in key)] = vals
        return out

    def skill_icons(self):
        """(skill id, level) -> icon name."""
        rows = self.rows('Skillgrp', ('skill_id', 'skill_level', 'skill_sublevel'), ('icon', 'operate_type'))
        return {(k[0], k[1]): (self._value(r['icon']), r['operate_type']) for k, r in rows.items() if k[2] in ('0', '')}

    def item_icons(self):
        """item id -> icon name (first icon of armor / weapon / etc rows)."""
        out = {}
        for name in ('Armorgrp', 'Weapongrp', 'EtcItemgrp'):
            for k, r in self.rows(name, ('object_id',), ('icon',)).items():
                first = re.search(r'\[([^\]]+)\]', r['icon'])
                if first:
                    out[k[0]] = self._value('[' + first.group(1) + ']')
        return out

    def largest_mip(self, key):
        """(offset, size) of the biggest DXT1 mip of a texture. Older icons have one mip at the end of the export
        (what iconpatch.pixels reads); the Samurai Crow ones (s_*) carry mipmaps 64 -> 1, so look for each size's
        footer (USize, VSize, UBits, VBits) with its DXT1 data length in front of the data."""
        off, size = self.textures[key]
        for w in (128, 64, 32, 16):
            n = w * w // 2
            footer = struct.pack('<IIBB', w, w, w.bit_length() - 1, w.bit_length() - 1)
            at = self.pkg.find(footer, off, off + size)
            if at > 0 and self.pkg[at - n - 2:at - n] == bytes([0x40 | (n & 0x3F), n >> 6]):
                return at - n, w
        return None

    def icon_png(self, icon, folder):
        """Decode icon.<name> from Icon.utx to folder/<name>.png; returns the file name, or None (not in Icon.utx / not DXT1)."""
        if not icon or not icon.lower().startswith('icon.'):
            return None
        key = icon[5:].lower()
        fname = key + '.png'
        path = os.path.join(folder, fname)
        if os.path.exists(path):
            return fname
        if key not in self.textures:
            return None
        found = self.largest_mip(key)
        if not found:
            return None
        off, w = found
        os.makedirs(folder, exist_ok=True)
        with open(path, 'wb') as f:
            f.write(png(dxt1(self.pkg, off, w), w))
        return fname


def dxt1(data, off, w):
    """DXT1 blocks -> rows of RGBA pixels (index 3 of a 3-colour block is transparent)."""
    c565 = lambda c: ((c >> 11 & 31) * 255 // 31, (c >> 5 & 63) * 255 // 63, (c & 31) * 255 // 31)
    img = [[(0, 0, 0, 0)] * w for _ in range(w)]
    bw = w // 4
    for b in range(bw * bw):
        c0, c1, idx = struct.unpack_from('<HHI', data, off + b * 8)
        a, bb = c565(c0), c565(c1)
        if c0 > c1:
            pal = [a + (255,), bb + (255,), tuple((2 * x + y) // 3 for x, y in zip(a, bb)) + (255,), tuple((x + 2 * y) // 3 for x, y in zip(a, bb)) + (255,)]
        else:
            pal = [a + (255,), bb + (255,), tuple((x + y) // 2 for x, y in zip(a, bb)) + (255,), (0, 0, 0, 0)]
        for i in range(16):
            img[(b // bw) * 4 + i // 4][(b % bw) * 4 + i % 4] = pal[idx >> (2 * i) & 3]
    return img


def png(img, w):
    raw = b''.join(b'\0' + bytes(c for px in row for c in px) for row in img)
    ch = lambda tag, d: struct.pack('>I', len(d)) + tag + d + struct.pack('>I', zlib.crc32(tag + d) & 0xffffffff)
    return (b'\x89PNG\r\n\x1a\n' + ch(b'IHDR', struct.pack('>IIBBBBB', w, w, 8, 6, 0, 0, 0))
            + ch(b'IDAT', zlib.compress(raw, 9)) + ch(b'IEND', b''))


if __name__ == '__main__':  # self-check: decode one known icon
    c = Client(os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(CACHE), '..', '..', 'L2J_Mobius_14.1_SamuraiCrow')))
    icons = c.skill_icons()
    assert icons[('1', '1')][0] == 'icon.skill0001', icons[('1', '1')]
    print('skills', len(icons), 'items', len(c.item_icons()), 'png', c.icon_png('icon.skill0001', os.path.join(CACHE, 'test')))
