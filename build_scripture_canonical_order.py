#!/usr/bin/env python3
from pathlib import Path
import json, re, html, shutil, zipfile, sys

ROOT = Path(__file__).resolve().parent
HTML = ROOT / "scripture.html"
JSON = ROOT / "data" / "scripture-index.json"

if not HTML.exists() or not JSON.exists():
    print("ERROR: Could not find scripture.html and data/scripture-index.json.")
    print("Put these files in the TOP LEVEL of your local archive repository.")
    input("\nPress Return to close...")
    raise SystemExit(1)

BOOKS = [
    "Genesis","Exodus","Leviticus","Numbers","Deuteronomy","Joshua","Judges","Ruth",
    "1 Samuel","2 Samuel","1 Kings","2 Kings","1 Chronicles","2 Chronicles","Ezra",
    "Nehemiah","Esther","Job","Psalms","Proverbs","Ecclesiastes","Song of Solomon",
    "Isaiah","Jeremiah","Lamentations","Ezekiel","Daniel","Hosea","Joel","Amos",
    "Obadiah","Jonah","Micah","Nahum","Habakkuk","Zephaniah","Haggai","Zechariah",
    "Malachi","Matthew","Mark","Luke","John","Acts","Romans","1 Corinthians",
    "2 Corinthians","Galatians","Ephesians","Philippians","Colossians",
    "1 Thessalonians","2 Thessalonians","1 Timothy","2 Timothy","Titus","Philemon",
    "Hebrews","James","1 Peter","2 Peter","1 John","2 John","3 John","Jude","Revelation"
]
ORDER = {b:i for i,b in enumerate(BOOKS)}
ALIASES = {"Psalm":"Psalms","Song of Songs":"Song of Solomon","Canticles":"Song of Solomon","Revelations":"Revelation"}
MATCH_BOOKS = sorted(set(BOOKS) | set(ALIASES), key=len, reverse=True)

def split_ref(ref):
    for b in MATCH_BOOKS:
        if ref == b or ref.startswith(b + " "):
            return ALIASES.get(b,b), ref[len(b):].strip()
    return None, ref

def num_start(s, default=0):
    m = re.search(r"\d+", s or "")
    return int(m.group()) if m else default

def ref_key(ref):
    book, rest = split_ref(ref)
    if book is None:
        return (999,999,999,ref.lower())
    chapter = num_start(rest,0)
    verse = num_start(rest.split(":",1)[1],0) if ":" in rest else 0
    return (ORDER[book], chapter, verse, rest.lower(), ref.lower())

data = json.loads(JSON.read_text(encoding="utf-8"))
unknown = sorted(ref for ref in data if split_ref(ref)[0] is None)
if unknown:
    print("STOPPED: Unrecognized Bible book names:")
    for ref in unknown[:100]:
        print(" -", ref)
    print("\nNo files were changed.")
    input("\nPress Return to close...")
    raise SystemExit(2)

ordered_refs = sorted(data.keys(), key=ref_key)
ordered = {ref:data[ref] for ref in ordered_refs}

backup = ROOT / "scripture_canonical_order_backup"
if backup.exists():
    shutil.rmtree(backup)
(backup/"data").mkdir(parents=True)
shutil.copy2(HTML, backup/"scripture.html")
shutil.copy2(JSON, backup/"data"/"scripture-index.json")

page = HTML.read_text(encoding="utf-8")
m = re.search(r'(<nav class="alpha-nav"[\s\S]*?</nav>)(<section id="index-list">)([\s\S]*?)(</section>)', page)
if not m:
    print("ERROR: Could not identify Scripture index section.")
    input("\nPress Return to close...")
    raise SystemExit(3)

body = m.group(3)
blocks = re.findall(r'<div class="index-entry"[\s\S]*?</div>', body)
by_ref = {}
for block in blocks:
    sm = re.search(r'<strong>([\s\S]*?)</strong>', block)
    if sm:
        ref = html.unescape(re.sub(r'<[^>]+>', '', sm.group(1))).strip()
        by_ref[ref] = block

missing = [r for r in ordered_refs if r not in by_ref]
extra = [r for r in by_ref if r not in data]
if missing or extra:
    print("ERROR: HTML and JSON Scripture indexes do not match.")
    print("Missing:", missing[:20])
    print("Extra:", extra[:20])
    input("\nPress Return to close...")
    raise SystemExit(4)

groups = {}
for ref in ordered_refs:
    book,_ = split_ref(ref)
    groups.setdefault(book, []).append(ref)
represented = [b for b in BOOKS if b in groups]

def slug(s):
    return re.sub(r'[^a-z0-9]+','-',s.lower()).strip('-')

nav = '<nav class="alpha-nav" aria-label="Jump by Bible book">' + ''.join(
    f'<a href="#book-{slug(b)}">{html.escape(b)}</a>' for b in represented
) + '</nav>'

parts = []
for b in represented:
    parts.append(f'<h2 class="index-letter" id="book-{slug(b)}">{html.escape(b)}</h2>')
    parts.extend(by_ref[r] for r in groups[b])
new_section = nav + '<section id="index-list">' + ''.join(parts) + '</section>'
page = page[:m.start()] + new_section + page[m.end():]

HTML.write_text(page, encoding="utf-8")
JSON.write_text(json.dumps(ordered, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

reloaded_keys = list(json.loads(JSON.read_text(encoding="utf-8")).keys())
html_refs = []
for block in re.findall(r'<div class="index-entry"[\s\S]*?</div>', HTML.read_text(encoding="utf-8")):
    sm = re.search(r'<strong>([\s\S]*?)</strong>', block)
    if sm:
        html_refs.append(html.unescape(re.sub(r'<[^>]+>','',sm.group(1))).strip())

checks = {
    "Scripture JSON entries preserved": len(reloaded_keys) == len(data),
    "Scripture HTML entries preserved": len(html_refs) == len(data),
    "JSON order is canonical": reloaded_keys == ordered_refs,
    "HTML order matches JSON": html_refs == ordered_refs,
}
failed = [k for k,v in checks.items() if not v]
if failed:
    print("ERROR: Verification failed:", ", ".join(failed))
    input("\nPress Return to close...")
    raise SystemExit(5)

out = ROOT / "github_upload_scripture_canonical_order"
if out.exists():
    shutil.rmtree(out)
(out/"data").mkdir(parents=True)
shutil.copy2(HTML, out/"scripture.html")
shutil.copy2(JSON, out/"data"/"scripture-index.json")

zip_path = ROOT / "github_upload_scripture_canonical_order.zip"
if zip_path.exists():
    zip_path.unlink()
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
    z.write(out/"scripture.html", arcname="scripture.html")
    z.write(out/"data"/"scripture-index.json", arcname="data/scripture-index.json")

report = ROOT / "SCRIPTURE_CANONICAL_ORDER_REPORT.txt"
report.write_text(
    "Michael Elliott Archive — Scripture Canonical Order Fix\n\n"
    f"Scripture references: {len(data)}\n"
    f"Bible books represented: {len(represented)}\n"
    "Order: Genesis to Revelation; chapter/verse order within each book\n"
    "Scripture wording changed: 0\n"
    "Linked reviews changed: 0\n"
    "Themes index changed: 0\n"
    "Review files changed: 0\n"
    "Review metadata changed: 0\n\n"
    "GitHub files to upload:\n"
    "  scripture.html\n"
    "  data/scripture-index.json\n",
    encoding="utf-8"
)

print("\nSUCCESS")
print("-------")
for k in checks:
    print(k + ": PASSED")
print(f"Scripture references: {len(data)}")
print(f"Bible books represented: {len(represented)}")
print("Themes index changed: 0")
print("Review files changed: 0")
print("Review metadata changed: 0")
print(f"\nCreated: {zip_path}")
print(f"Report:  {report}")
print("\nSend this Terminal result to ChatGPT BEFORE uploading to GitHub.")
input("\nPress Return to close...")
