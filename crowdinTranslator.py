# To run this script run below commands
# Dry run (no AI, just list untranslated)
#   python crowdinTranslator.py IfcRailDomain.pot --limit=20 --dry-run
# Translate & upload with AI (imports as translations)
#   python crowdinTranslator.py IfcControlExtension.pot --limit=20
# Export PO file locally (no upload)
#   python crowdinTranslator.py IfcControlExtension.pot --limit=20 --export-po
# Whole project, AI-enabled
#   python crowdinTranslator.py --limit=50
# Whole project, dry-run
#   python crowdinTranslator.py --dry-run
#
# For enterprise crowdin project please use
# credentials to be stored at root of the python script in .env file with
# CROWDIN_PERSONAL_TOKEN=123asd123asd # add your personal access token here with 
# ORGANIZATION=firstpart # of the link to project. firstpart.crowdin.com
# CROWDIN_PROJECT_ID=123456 #change this to reflect the project number
# OPENAI_API_KEY=sk-........ #add your openAI API access token here generated at platform.openai.com

import os, sys, re, requests
from dotenv import load_dotenv
from crowdin_api import CrowdinClient
import openai

load_dotenv()
CROWDIN_TOKEN = os.getenv("CROWDIN_PERSONAL_TOKEN")
ORGANIZATION = os.getenv("ORGANIZATION", "buildingsmart")
PROJECT_ID = int(os.getenv("CROWDIN_PROJECT_ID", "123456"))
TARGET_LANG = "tr"
openai.api_key = os.getenv("OPENAI_API_KEY")

API_BASE = f"https://{ORGANIZATION}.api.crowdin.com/api/v2"
HEADERS = {"Authorization": f"Bearer {CROWDIN_TOKEN}"}

class MyClient(CrowdinClient):
    TOKEN = CROWDIN_TOKEN
    ORGANIZATION = ORGANIZATION

client = MyClient()

# Crowdin hard-caps page size at 500; keep requests <= 500 and paginate.
PAGE_SIZE = 500

# --- helper: keep [[IfcSomething]] tokens unchanged -----------------
TOKEN_PATTERN = re.compile(r"\[\[[^\]]+\]\]")

def protect_tokens(text: str):
    tokens = TOKEN_PATTERN.findall(text or "")
    return tokens

def ai_translate(source_text: str):
    tokens = protect_tokens(source_text)
    system_msg = (
        "You are a professional BIM/IFC translator. "
        "Translate the user text into Turkish with precise technical terminology. "
        "Do NOT modify tokens enclosed in double square brackets [[...]] or IFC class names; "
        "copy them exactly as-is. Preserve punctuation, capitalization, and placeholders."
    )
    resp = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": source_text}
        ]
    )
    tr = resp.choices[0].message.content.strip()
    # sanity: ensure tokens are preserved
    for t in tokens:
        if t not in tr:
            # crude fallback: re-insert token if accidentally dropped
            tr = tr.replace(t.replace("[[", "").replace("]]", ""), t)
    return tr

# --- call Crowdin: check if string has any tr translations -----------
def has_translation(string_id: int) -> bool:
    url = f"{API_BASE}/projects/{PROJECT_ID}/languages/{TARGET_LANG}/translations"
    r = requests.get(url, headers=HEADERS, params={"stringIds[]": string_id, "limit": 1})
    r.raise_for_status()
    return bool(r.json().get("data"))

# --- call Crowdin: add a translation (UNAPPROVED by default) --------
def add_translation(string_id: int, text: str) -> bool:
    # Try plain JSON first
    payload = {"stringId": string_id, "languageId": TARGET_LANG, "text": text}
    url = f"{API_BASE}/projects/{PROJECT_ID}/translations"
    r = requests.post(url, headers=HEADERS, json=payload)
    if r.status_code in (200, 201):
        print(f"   ✅ added (unapproved) → {text[:80]}")
        return True
    # Some Enterprise envs expect a 'data' wrapper; try fallback:
    payload2 = {"data": payload}
    r2 = requests.post(url, headers=HEADERS, json=payload2)
    if r2.status_code in (200, 201):
        print(f"   ✅ added (unapproved, alt body) → {text[:80]}")
        return True
    # common soft failures
    if r.status_code == 409 or r2.status_code == 409:
        print("   ⚠️ duplicate/exists, skipping")
        return False
    print(f"   ❌ add failed: {r.status_code} {r.text} | fallback {r2.status_code} {r2.text}")
    return False

# --- pagination helpers ---------------------------------------------
def iter_all_files():
    """Yield all files in the project via pagination."""
    offset = 0
    while True:
        batch = client.source_files.list_files(PROJECT_ID, limit=PAGE_SIZE, offset=offset)
        items = batch.get("data", [])
        if not items:
            break
        for f in items:
            yield f
        offset += PAGE_SIZE

def iter_strings_in_file(file_id: int):
    """Yield all source strings for a given file via pagination."""
    offset = 0
    while True:
        res = client.source_strings.list_strings(PROJECT_ID, fileId=file_id, limit=PAGE_SIZE, offset=offset)
        rows = res.get("data", [])
        if not rows:
            break
        for row in rows:
            yield row
        offset += PAGE_SIZE

# --- core: process a file -------------------------------------------
def process_file(file_id: int, file_name: str, max_to_process: int, dry_run: bool):
    print(f"🔍 {file_name} (target max={max_to_process}, page_size={PAGE_SIZE})")
    handled = 0
    for row in iter_strings_in_file(file_id):
        if handled >= max_to_process:
            break
        sid = row["data"]["id"]
        src = row["data"]["text"]
        # skip if already translated
        if has_translation(sid):
            continue
        if dry_run:
            print(f"[{file_name}:{sid}] {src}")
            handled += 1
            continue
        tr = ai_translate(src)
        print(f"[{file_name}:{sid}] {src} → {tr}")
        if add_translation(sid, tr):
            handled += 1
    print(f"✅ {file_name}: {handled} translations submitted (or listed in dry-run)\n")
    return handled

# --- CLI -------------------------------------------------------------
if __name__ == "__main__":
    target_file = None
    limit = 500  # Interpret as "max to process per file" across pages.
    dry_run = False

    for a in sys.argv[1:]:
        if a.endswith(".pot"):
            target_file = a
        elif a.startswith("--limit="):
            limit = int(a.split("=",1)[1])
        elif a == "--dry-run":
            dry_run = True

    if target_file:
        fid = None
        for f in iter_all_files():
            if f["data"]["name"] == target_file:
                fid = f["data"]["id"]
                break
        if not fid:
            raise RuntimeError(f"File not found: {target_file}")
        print(f"🎯 Targeting file: {target_file} (id={fid}), max={limit}, AI={'off' if dry_run else 'on'}")
        process_file(fid, target_file, limit, dry_run)
    else:
        print(f"🎯 Targeting entire project (max={limit} per file), AI={'off' if dry_run else 'on'}")
        total = 0
        for f in iter_all_files():
            fid = f["data"]["id"]; fname = f["data"]["name"]
            h = process_file(fid, fname, limit, dry_run)
            total += h
        print("📊 Summary")
        print(f"Submitted (or listed): {total}")