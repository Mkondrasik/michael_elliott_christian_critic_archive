#!/usr/bin/env python3
from pathlib import Path
import json, re, html as htmlmod, shutil, zipfile, sys

ROOT = Path(__file__).resolve().parent
if not (ROOT / "reviews").exists():
    candidates = [p for p in ROOT.iterdir() if p.is_dir() and (p/"reviews").exists() and (p/"data"/"reviews.json").exists()]
    if len(candidates) == 1:
        ROOT = candidates[0]
    else:
        print("ERROR: Could not find the archive repository.")
        print("Place this script in the top level of the downloaded repository folder.")
        input("Press Return to close...")
        sys.exit(1)

REVIEWS = ROOT / "reviews"
DATA = ROOT / "data" / "reviews.json"
SCRIPTURE = ROOT / "scripture.html"
THEMES = ROOT / "themes.html"

records = json.loads(DATA.read_text(encoding="utf-8"))
by_id = {r["id"]: r for r in records}

if len(records) != 1000:
    print(f"WARNING: expected 1000 records, found {len(records)}.")
    if input("Type YES to continue: ").strip().upper() != "YES":
        sys.exit(1)

updates = {
    "Elliott_0987": {
        "translation": None,
        "sermon_spiritual_topic": "Justice; Right; Integrity",
    },
    "Elliott_0890": {
        "translation": None,
    },
    "Elliott_0615": {
        "scripture_references": ["Hebrews 12:11", "Luke 9:62", "Ecclesiastes 7:14", "Philippians 3:13"],
        "translation": "NIV",
        "primary_scripture": "Philippians 3:13",
    },
    "Elliott_0800": {
        "scripture_references": ["1 Peter 5:2-3", "Isaiah 56:10-11", "Micah 3:11"],
    },
    "Elliott_0883": {
        "scripture_references": ["Mark 13:7", "Psalms 18:34", "Ecclesiastes 3:8"],
        "primary_scripture": "Mark 13:7",
    },
    "Elliott_0793": {
        "scripture_references": ["Proverbs 18:21", "James 3:1-5", "Proverbs 17:27-28", "Ephesians 6:16-17"],
    },
    "Elliott_0797": {
        "scripture_references": ["Acts 4:18-20", "Ezekiel 2:6-7", "Acts 4:29", "Ecclesiastes 7:5-6"],
    },
    "Elliott_0799": {
        "scripture_references": ["Job 12:9-10", "Genesis 2:7", "Job 33:4"],
    },

    # Author-confirmed standard star ratings.
    "Elliott_0325": {"rating": "1½ stars"},
    "Elliott_0518": {"rating": "3 stars"},
    "Elliott_0582": {"rating": "1½ stars"},
    "Elliott_0621": {"rating": "2 stars"},
    "Elliott_0648": {"rating": "2 stars"},
    "Elliott_0717": {"rating": "1 star"},
    "Elliott_0956": {"rating": "2½ stars"},
    "Elliott_0241": {"rating": "0 stars"},
    "Elliott_0285": {"rating": "0 stars"},
    "Elliott_0306": {"rating": "0 stars"},
    "Elliott_0434": {"rating": "3 stars"},
    "Elliott_0466": {"rating": "2 stars"},
    "Elliott_0999": {"rating": "4 stars"},

    # Missing derived archival topics.
    "Elliott_0512": {"sermon_spiritual_topic": "Love; Selflessness; Responsibility"},
    "Elliott_0513": {"sermon_spiritual_topic": "Friendship; Giving; Forgiveness; Cooperation"},
    "Elliott_0519": {"sermon_spiritual_topic": "Kindness; Salvation; Words"},
    "Elliott_0678": {"sermon_spiritual_topic": "Identity in Christ; God's Word; Obedience"},
    "Elliott_0741": {"sermon_spiritual_topic": "Maturity; Spiritual Growth; Responsibility"},
    "Elliott_0743": {"sermon_spiritual_topic": "Faith; Action; Courage; Conviction"},

    # Primary Scripture values recovered from the author-verified catalog.
    "Elliott_0012": {"primary_scripture": "2 Corinthians 11:13-15a"},
    "Elliott_0013": {
        "primary_scripture": "1 Timothy 4:14a",
        "scripture_references": ["2 Timothy 1:6", "1 Thessalonians 5:19", "Ephesians 2:8", "1 Timothy 4:14a"],
    },
    "Elliott_0014": {"primary_scripture": "Galatians 6:7"},
    "Elliott_0015": {"primary_scripture": "Matthew 18:4"},
    "Elliott_0016": {"primary_scripture": "John 6:35"},
    "Elliott_0017": {"primary_scripture": "Acts 20:30"},
    "Elliott_0018": {"primary_scripture": "Psalms 37:25"},
    "Elliott_0019": {
        "primary_scripture": "Matthew 19:4",
        "scripture_references": ["Matthew 19:14", "Psalms 139:14", "Deuteronomy 22:5", "Matthew 19:4"],
    },
    "Elliott_0020": {"primary_scripture": "Joshua 23:10"},
}

def scripture_slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")

def transcription_section(text):
    m = re.search(r'(<section><h2>Author-verified transcription</h2>[\s\S]*?</section>)', text, re.I)
    return m.group(1) if m else None

def set_rating(text, value):
    return re.sub(
        r'(<div><b>Rating</b><br\s*/?>)(.*?)(</div>)',
        lambda m: m.group(1) + htmlmod.escape(value, quote=False) + m.group(3),
        text, count=1, flags=re.I|re.S
    )

def set_topic(text, value):
    return re.sub(
        r'(<b>Sermon / spiritual topic:</b>\s*)([^<]*)(</p>)',
        lambda m: m.group(1) + htmlmod.escape(value, quote=False) + m.group(3),
        text, count=1, flags=re.I
    )

def set_scripture_chips(text, refs):
    chips = ''.join(
        f'<a class="chip" href="../scripture.html#{scripture_slug(s)}">{htmlmod.escape(s, quote=False)}</a>'
        for s in refs
    )
    return re.sub(
        r'(<section><h2>Scripture references</h2><div class="chips">)[\s\S]*?(</div><p>)',
        lambda m: m.group(1) + chips + m.group(2),
        text, count=1, flags=re.I
    )

backup = ROOT / "metadata_cleanup_backup_final"
if backup.exists():
    shutil.rmtree(backup)
(backup / "reviews").mkdir(parents=True)
(backup / "data").mkdir(parents=True)

for p in [DATA, SCRIPTURE, THEMES]:
    if p.exists():
        target = backup / p.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, target)

changed_review_paths = []
integrity_failures = []

for rid, fields in updates.items():
    rec = by_id.get(rid)
    if not rec:
        print("Missing record:", rid)
        sys.exit(2)

    page = ROOT / rec["page"]
    original_html = page.read_text(encoding="utf-8")
    before_transcription = transcription_section(original_html)
    new_html = original_html

    shutil.copy2(page, backup / "reviews" / page.name)

    for key, value in fields.items():
        rec[key] = value

    if "rating" in fields:
        new_html = set_rating(new_html, fields["rating"])
    if "sermon_spiritual_topic" in fields:
        new_html = set_topic(new_html, fields["sermon_spiritual_topic"])
    if "scripture_references" in fields:
        new_html = set_scripture_chips(new_html, fields["scripture_references"])

    after_transcription = transcription_section(new_html)
    if before_transcription != after_transcription:
        integrity_failures.append(page.name)
        continue

    if new_html != original_html:
        page.write_text(new_html, encoding="utf-8")
        changed_review_paths.append(page)

if integrity_failures:
    print("STOPPED: transcription integrity check failed for:")
    for x in integrity_failures:
        print(" ", x)
    input("Press Return to close...")
    sys.exit(3)

DATA.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def generate_scripture_index(records):
    groups, titles = {}, {}
    for r in records:
        titles[r["page"]] = r["title"]
        for s in r.get("scripture_references") or []:
            groups.setdefault(s, []).append(r["page"])
    parts = ["<!doctype html><html><head><meta charset='utf-8'><link rel='stylesheet' href='assets/style.css'></head><body><main class='wrap'><h1>Scripture Index</h1>"]
    for key in sorted(groups, key=lambda x: x.casefold()):
        links = ", ".join(f'<a href="{p}">{htmlmod.escape(titles[p], quote=False)}</a>' for p in groups[key])
        parts.append(f'<div class="index-entry" id="{scripture_slug(key)}"><strong>{htmlmod.escape(key, quote=False)}</strong><br>{links}</div>')
    parts.append("</main></body></html>")
    return "".join(parts)

def generate_theme_index(records):
    groups, titles = {}, {}
    for r in records:
        titles[r["page"]] = r["title"]
        for t in [x.strip() for x in (r.get("sermon_spiritual_topic") or "").split(";") if x.strip()]:
            groups.setdefault(t, []).append(r["page"])
    parts = ["<!doctype html><html><head><meta charset='utf-8'><link rel='stylesheet' href='assets/style.css'></head><body><main class='wrap'><h1>Themes</h1>"]
    for key in sorted(groups, key=lambda x: x.casefold()):
        links = ", ".join(f'<a href="{p}">{htmlmod.escape(titles[p], quote=False)}</a>' for p in groups[key])
        parts.append(f'<div class="index-entry"><strong>{htmlmod.escape(key, quote=False)}</strong><br>{links}</div>')
    parts.append("</main></body></html>")
    return "".join(parts)

SCRIPTURE.write_text(generate_scripture_index(records), encoding="utf-8")
THEMES.write_text(generate_theme_index(records), encoding="utf-8")

# Verify changes.
records2 = json.loads(DATA.read_text(encoding="utf-8"))
by2 = {r["id"]: r for r in records2}
errors = []

for rid, fields in updates.items():
    r = by2[rid]
    for key, expected in fields.items():
        if r.get(key) != expected:
            errors.append(f"{rid}: {key} not updated")

# Confirm all review transcription sections still match their backups.
for p in changed_review_paths:
    before = transcription_section((backup/"reviews"/p.name).read_text(encoding="utf-8"))
    after = transcription_section(p.read_text(encoding="utf-8"))
    if before != after:
        errors.append(f"{p.name}: transcription changed")

if errors:
    print("STOPPED: verification errors")
    for e in errors[:50]:
        print(" ", e)
    input("Press Return to close...")
    sys.exit(4)

outdir = ROOT / "metadata_cleanup_upload_final"
if outdir.exists():
    shutil.rmtree(outdir)
(outdir / "reviews").mkdir(parents=True)
(outdir / "data").mkdir(parents=True)

for p in changed_review_paths:
    shutil.copy2(p, outdir / "reviews" / p.name)
shutil.copy2(DATA, outdir / "data" / "reviews.json")
shutil.copy2(SCRIPTURE, outdir / "scripture.html")
shutil.copy2(THEMES, outdir / "themes.html")

zip_path = ROOT / "metadata_cleanup_upload_final.zip"
if zip_path.exists():
    zip_path.unlink()
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
    for p in sorted(outdir.rglob("*")):
        if p.is_file():
            z.write(p, arcname=str(p.relative_to(outdir)))

report = ROOT / "METADATA_CLEANUP_FINAL_REPORT.txt"
report.write_text(
    "Michael Elliott / Christian Critic Archive — Final Metadata Cleanup\n\n"
    f"JSON records: {len(records2)}\n"
    f"Review HTML files changed: {len(changed_review_paths)}\n"
    "Review transcription integrity: PASSED\n"
    "Scripture index regeneration: PASSED\n"
    "Theme index regeneration: PASSED\n\n"
    "Author-confirmed ratings included:\n"
    "0325 Cousin Bette — 1½ stars\n"
    "0518 The Horse Whisperer — 3 stars\n"
    "0582 Love and Death on Long Island — 1½ stars\n"
    "0717 Out of Sight — 1 star\n"
    "0956 The X-Files — 2½ stars\n"
    "0241 The Aristocrats — 0 stars\n"
    "0285 Brokeback Mountain — 0 stars\n"
    "0306 Boys Don't Cry — 0 stars\n"
    "0434 Elizabeth — 3 stars\n"
    "0466 Godzilla — 2 stars\n"
    "0999 20 Feet From Stardom — 4 stars\n\n"
    "Author-confirmed Scripture clarification:\n"
    "0799 Stealth — Genesis 2:7\n",
    encoding="utf-8"
)

print("\nSUCCESS")
print("-------")
print(f"Review HTML files changed: {len(changed_review_paths)}")
print("Review transcription integrity: PASSED")
print("Scripture index regeneration: PASSED")
print("Theme index regeneration: PASSED")
print(f"\nCreated: {zip_path}")
print(f"Report:  {report}")
print(f"Backup:  {backup}")
input("\nPress Return to close...")
