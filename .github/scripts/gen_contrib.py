import re, sys, os, urllib.request

USER = "HaydenCash716"
OUT = sys.argv[1] if len(sys.argv) > 1 else "assets/contributions.svg"

# Pull the FULL per-day contribution data (includes private contributions while
# the profile setting is on). We use only the data-score/data-date values, then
# render our own clean dark + blue grid (GitHub dark look, but blue).
raw = urllib.request.urlopen(f"https://ghchart.rshah.org/00E5FF/{USER}", timeout=60).read().decode()

cells = [(int(x), int(y), int(s), d) for s, d, x, y in
         re.findall(r'data-score="(\d+)"\s+data-date="([\d-]+)"\s+x="(\d+)"\s+y="(\d+)"', raw)]
if not cells:
    raise SystemExit("no contribution cells parsed")

scores = sorted(s for _, _, s, _ in cells if s > 0)
mx = scores[-1] if scores else 0

def level(s):
    if s <= 0:
        return 0
    q = s / mx if mx else 0
    return 1 if q <= .25 else 2 if q <= .5 else 3 if q <= .75 else 4

EMPTY = "#161b22"
RAMP = {1: "#0b3a4d", 2: "#0e6f99", 3: "#16b3e0", 4: "#00E5FF"}

xs = [c[0] for c in cells]; ys = [c[1] for c in cells]
offx, offy, pad = min(xs) - 2, min(ys) - 2, 8
W = max(xs) - offx + 10 + pad
H = max(ys) - offy + 10 + pad

out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
       f'<rect width="{W}" height="{H}" rx="6" fill="#0d1117"/>']
for x, y, s, _ in cells:
    lv = level(s)
    fill = EMPTY if lv == 0 else RAMP[lv]
    out.append(f'<rect x="{x-offx+pad-4}" y="{y-offy+pad-4}" width="10" height="10" rx="2" fill="{fill}"/>')
out.append('</svg>')

os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
open(OUT, "w").write("".join(out))
print(f"wrote {OUT}: {len(scores)} active days, max/day {mx}")
