#!/usr/bin/env python3
"""Generate a self-hosted streak card SVG from the real GitHub contribution
calendar. Unlike streak-stats.demolab.com, this breaks the streak on ANY day
with zero contributions (a missed day should not count) — see gh issue history
for demolab's timezone/off-by-one miscount.

Usage: gen_streak.py [out.svg]
Requires a token in $GITHUB_TOKEN (or $GH_TOKEN) with read access to the
contribution calendar (the Actions default GITHUB_TOKEN is sufficient for the
public graph).
"""
import json, os, sys, urllib.request, datetime

USER = "HaydenCash716"
OUT = sys.argv[1] if len(sys.argv) > 1 else "assets/streak.svg"
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
if not TOKEN:
    raise SystemExit("GITHUB_TOKEN / GH_TOKEN required")

QUERY = """
{ user(login: "%s") { contributionsCollection { contributionCalendar {
  totalContributions weeks { contributionDays { date contributionCount } } } } } }
""" % USER

req = urllib.request.Request(
    "https://api.github.com/graphql",
    data=json.dumps({"query": QUERY}).encode(),
    headers={"Authorization": f"bearer {TOKEN}",
             "User-Agent": USER, "Content-Type": "application/json"})
data = json.loads(urllib.request.urlopen(req, timeout=60).read())
cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
days = sorted((d["date"], d["contributionCount"])
              for w in cal["weeks"] for d in w["contributionDays"])
total = cal["totalContributions"]

# --- streak math: a zero day breaks the streak; today-with-zero is not yet a
# miss (you can still contribute), so it's skipped rather than counted/broken.
seq = list(reversed(days))
i = 1 if seq and seq[0][1] == 0 else 0
cur = 0; cur_start = None
for date, count in seq[i:]:
    if count > 0:
        cur += 1; cur_start = date
    else:
        break
cur_end = days[-1][0]

run = 0; best = 0; run_start = None
best_start = best_end = None
for date, count in days:
    if count > 0:
        run += 1; run_start = run_start or date
        if run > best:
            best, best_start, best_end = run, run_start, date
    else:
        run = 0; run_start = None
first_active = next((d for d, c in days if c > 0), days[0][0])


def fmt(d):
    dt = datetime.date.fromisoformat(d)
    return dt.strftime("%b ") + str(dt.day)


def fmt_y(d):
    dt = datetime.date.fromisoformat(d)
    return dt.strftime("%b ") + f"{dt.day}, {dt.year}"


total_range = f"{fmt_y(first_active)} - Present"
cur_range = f"{fmt(cur_start)} - {fmt(cur_end)}" if cur else "—"
best_range = f"{fmt(best_start)} - {fmt(best_end)}" if best else "—"

# --- theme (matches profile README) ---
BG, RING, FIRE = "#0B0E14", "#00E5FF", "#FF2E63"
NUM, LABEL, DATE = "#C9D1D9", "#00E5FF", "#8B949E"
W, H = 495, 195
cx = [W * 1 / 6, W / 2, W * 5 / 6]


def col(x, big, big_color, label, sub):
    return f"""
  <g text-anchor="middle" font-family="'Segoe UI',Ubuntu,sans-serif">
    <text x="{x:.0f}" y="82" font-size="28" font-weight="700" fill="{big_color}">{big}</text>
    <text x="{x:.0f}" y="114" font-size="14" font-weight="600" fill="{LABEL}">{label}</text>
    <text x="{x:.0f}" y="138" font-size="12" fill="{DATE}">{sub}</text>
  </g>"""

# center streak sits inside a ring with a flame on top
center = f"""
  <g text-anchor="middle" font-family="'Segoe UI',Ubuntu,sans-serif">
    <circle cx="{W/2:.0f}" cy="60" r="40" fill="none" stroke="{RING}" stroke-width="5"/>
    <rect x="{W/2-14:.0f}" y="14" width="28" height="24" fill="{BG}"/>
    <path transform="translate({W/2:.0f},24) scale(1.1)" fill="{FIRE}"
      d="M0,-9 C5,-4 8,-1 4,4 C7,2 8,-1 8,3 C8,9 4,12 0,12 C-4,12 -8,9 -8,3 C-8,0 -6,-2 -4,-1 C-6,-5 -2,-6 0,-9 Z"/>
    <text x="{W/2:.0f}" y="72" font-size="34" font-weight="700" fill="{NUM}">{cur}</text>
    <text x="{W/2:.0f}" y="118" font-size="14" font-weight="600" fill="{LABEL}">Current Streak</text>
    <text x="{W/2:.0f}" y="142" font-size="12" fill="{DATE}">{cur_range}</text>
  </g>"""

svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <rect width="{W}" height="{H}" rx="6" fill="{BG}"/>
  <line x1="165" y1="30" x2="165" y2="165" stroke="{RING}" stroke-width="1" opacity="0.6"/>
  <line x1="330" y1="30" x2="330" y2="165" stroke="{RING}" stroke-width="1" opacity="0.6"/>
  {col(cx[0], total, NUM, "Total Contributions", total_range)}
  {center}
  {col(cx[2], best, NUM, "Longest Streak", best_range)}
</svg>"""

os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
open(OUT, "w").write(svg)
print(f"wrote {OUT}: total={total} current={cur} ({cur_range}) longest={best}")
