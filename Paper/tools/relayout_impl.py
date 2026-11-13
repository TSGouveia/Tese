"""Paper version of Fig. 3 (Implementacao.drawio): larger fonts and a narrower Layer 1.
Reads figures/drawio/Implementacao.drawio (copy of the thesis diagram) and writes
figures/drawio/Implementacao_paper.drawio. The thesis files are never touched."""
import re, sys, xml.etree.ElementTree as ET
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / 'figures' / 'drawio' / 'Implementacao.drawio'
DST = SRC.with_name('Implementacao_paper.drawio')
F_BOX, F_LABEL, F_TITLE = 24, 20, 25
VSHIFT = 40      # extra room inside Layer 1 for the interface labels above the boxes

tree = ET.parse(SRC); root = tree.getroot()
cells = list(root.iter('mxCell'))
byid = {c.get('id'): c for c in cells}

# Layer 1 piecewise-linear x map: old box edges -> new box edges
old = [164, 344, 490, 670, 810, 990, 1130, 1310]
GAP = 77; x0 = 255
new = []
for i in range(4):
    new += [x0 + i * (180 + GAP), x0 + i * (180 + GAP) + 180]
def xmap(x):
    x = float(x)
    if x <= old[0]: return x + new[0] - old[0]
    if x >= old[-1]: return x + new[-1] - old[-1]
    for (a, b), (c, d) in zip(zip(old, old[1:]), zip(new, new[1:])):
        if a <= x <= b:
            return c + (x - a) * (d - c) / (b - a)

old0 = [334, 514, 654, 834, 979, 1159]
new0 = [255, 435, 640, 820, 1025, 1205]
def xmap0(x):
    x = float(x)
    if x <= old0[0]: return x + new0[0] - old0[0]
    if x >= old0[-1]: return x + new0[-1] - old0[-1]
    for (a, b), (c, d) in zip(zip(old0, old0[1:]), zip(new0, new0[1:])):
        if a <= x <= b:
            return c + (x - a) * (d - c) / (b - a)

def setf(el, k, v): el.set(k, f'{v:g}')
def style_set(c, key, val):
    s = c.get('style') or ''
    if re.search(rf'(^|;){key}=', s):
        s = re.sub(rf'(^|;){key}=[^;]*', rf'\g<1>{key}={val}', s)
    else:
        s = s.rstrip(';') + f';{key}={val};'
    c.set('style', s)

L1_BOXES = {'3D Viewer', 'GUI &amp; Event', 'Pin &amp; Logic', 'BaSyx Python'}
for c in cells:
    v = c.get('value') or ''
    s = c.get('style') or ''
    g = c.find('mxGeometry')
    if 'fontSize=' in s:
        size = F_TITLE if v.startswith('Layer') else (F_LABEL if s.startswith('text;') else F_BOX)
        style_set(c, 'fontSize', size)
    if g is None or (g.get('relative') == '1' and c.get('edge') != '1'):
        continue
    # ---- vertices -------------------------------------------------------
    if c.get('vertex') == '1' and g.get('relative') != '1':
        x, y = float(g.get('x', 0)), float(g.get('y', 0))
        w, h = float(g.get('width', 0)), float(g.get('height', 0))
        if v.startswith('Layer'):
            style_set(c, 'whiteSpace', 'nowrap'); setf(g, 'width', 700)
        if c.get('id') == 'R4p7xMKH7e2ikrvYrVqG-1':          # Layer 1 container
            setf(g, 'x', 230); setf(g, 'width', 1000); setf(g, 'height', h + VSHIFT)
            continue
        in_l1 = 230 <= y <= 420
        if in_l1 and not v.startswith('Layer 1'):
            nx = xmap(x); nw = xmap(x + w) - nx
            if s.startswith('text;'):          # interface label -> centred above the gap
                cx = xmap(x + w / 2); nw = 160; nx = cx - nw / 2
                setf(g, 'height', 50); setf(g, 'y', 270); y = 0; style_set(c, 'verticalAlign', 'bottom')
                style_set(c, 'align', 'center')
            setf(g, 'x', nx); setf(g, 'width', nw)
        elif v.startswith('Layer 1'):
            setf(g, 'x', 245)
        elif c.get('id') == 'R4p7xMKH7e2ikrvYrVqG-37':      # Layer 0 container
            setf(g, 'x', 230); setf(g, 'width', 1000); setf(g, 'y', -35); setf(g, 'height', 205)
        elif v.startswith('Layer 0'):
            setf(g, 'x', 245); setf(g, 'y', -25)
        elif y < 175:
            if s.startswith('text;'):
                cx = xmap0(x + w / 2); setf(g, 'x', cx - 90); setf(g, 'width', 180)
                setf(g, 'y', 16); setf(g, 'height', 50); style_set(c, 'verticalAlign', 'bottom')
            else:
                nx = xmap0(x); setf(g, 'x', nx); setf(g, 'width', xmap0(x + w) - nx)
        elif 175 <= y < 230 or (v == '3D Model File'):
            setf(g, 'x', xmap(x))
        if y >= 280:
            setf(g, 'y', y + VSHIFT)
        elif v.startswith('Layer') or c.get('id', '').endswith('-1'):
            pass
        if y >= 420 and c.get('id') in ('R4p7xMKH7e2ikrvYrVqG-1',):
            pass
    # ---- edges ----------------------------------------------------------
    if c.get('edge') == '1':
        src = byid.get(c.get('source')); srcv = (src.get('value') or '') if src is not None else ''
        for p in g.iter('mxPoint'):
            if p.get('x') is None or p.get('y') is None:
                continue
            x, y = float(p.get('x')), float(p.get('y'))
            if y < 175:
                setf(p, 'x', xmap0(x))
            elif 175 <= y < 185 and x > 1000:           # GLB riser waypoint
                setf(p, 'x', xmap0(x))
            elif 180 <= y <= 425 and x < 1130:          # Layer 1 internal + 3D Model File link
                setf(p, 'x', xmap(x))
            elif 180 <= y <= 460 and x >= 1130:        # risers under the BaSyx Python SDK
                setf(p, 'x', xmap(x))
            elif 175 <= y < 185 and 400 < x < 1000:     # GLB -> 3D Model File waypoint
                setf(p, 'x', xmap(x))
            if y >= 280:
                setf(p, 'y', y + VSHIFT)

# ---- hand-placed labels (final coordinates) -----------------------------------
OVR = {  # text -> (x, y, w, h, align, valign)
    '3D Model File': (430, 188, 160, 30, 'right', 'middle'),
    'AASX Package': (424, 478, 200, 50, 'left', 'middle'),
    'Submodel Browse': (344, 690, 170, 50, 'right', 'top'),
    'AAS Catalog': (608, 690, 108, 50, 'left', 'top'),
    'Scene Builder': (572, 1132, 140, 50, 'right', 'middle'),
    'Model Storage': (810, 556, 150, 40, 'center', 'bottom'),
    'Submodel Read': (414, 890, 180, 30, 'left', 'middle'),
    'AAS Discovery': (730, 890, 180, 30, 'left', 'middle'),
    'Submodel Lookup': (1063, 890, 180, 30, 'left', 'middle'),
    'Sensor Event Trigger': (795, 1172, 140, 50, 'center', 'bottom'),
    'Physical Skill Execution': (805, 1322, 155, 50, 'center', 'bottom'),
    'Sensor Telemetry': (498, 1320, 140, 50, 'center', 'bottom'),
    'Actuator Drive': (490, 1460, 175, 30, 'right', 'middle'),
    'Sensor Signal': (785, 1460, 175, 30, 'left', 'middle'),
}
def plain(v):
    return re.sub(r'<[^>]+>', ' ', v.replace('&lt;', '<').replace('&gt;', '>')).split()
for c in cells:
    if c.get('vertex') != '1':
        continue
    words = plain(c.get('value') or '')
    for key, (x, y, w, h, al, va) in OVR.items():
        if words[:len(key.split())] == key.split():
            g = c.find('mxGeometry')
            for k, val in zip(('x', 'y', 'width', 'height'), (x, y, w, h)):
                setf(g, k, val)
            style_set(c, 'align', al); style_set(c, 'verticalAlign', va)

# Operation Mode Manager: 30 units to the right so its interface label fits
for c in cells:
    if (c.get('value') or '') == 'Operation Mode Manager':
        g = c.find('mxGeometry'); setf(g, 'x', float(g.get('x')) + 30)
        opm = c.get('id')
for c in cells:
    if c.get('edge') == '1' and c.get('source') == opm:
        for p in c.find('mxGeometry').iter('mxPoint'):
            if p.get('x') and abs(float(p.get('x')) - 1020.03) < 1:
                setf(p, 'x', 1050.03)
# component boxes: push the name below the module icon
for c in cells:
    st = c.get('style') or ''
    if c.get('vertex') == '1' and st.startswith('html=1;dropTarget=0') and True:
        style_set(c, 'spacingTop', 0); style_set(c, 'spacingLeft', 6); style_set(c, 'spacingRight', 6)

# everything below Layer 1 that sat at y in [420,500) (riser waypoints, interface labels) is
# handled by the y>=280 shift above; Layer 0 is untouched.
tree.write(DST, encoding='utf-8', xml_declaration=False)
print('wrote', DST)
