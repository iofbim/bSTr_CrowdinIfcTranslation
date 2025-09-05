# bSTr_CrowdinIfcTranslation

A small Python utility that interacts with the Crowdin Enterprise API to:

- List untranslated source strings (dry run)
- Optionally translate them using OpenAI and submit as unapproved translations
- Target either a specific source file (`.pot`) or the entire project

This repository is dedicated to the public domain under The Unlicense.

---

## How It Works

- Reads configuration (tokens, project, org) from a local `.env` file
- Uses `crowdin_api` to fetch source strings and post translations
- Uses `openai` to generate Turkish translations (current default target language in code)

Main entry point: `crowdinTranslator.py`

---

## Requirements

- Python 3.9+
- A Crowdin Enterprise account and an existing project
- Crowdin Personal Access Token with API access
- Crowdin organization subdomain (e.g., `yourorg` for `yourorg.crowdin.com`)
- Crowdin project ID (integer)
- OpenAI API key (for AI translation)
- Internet access

Python packages:

- `python-dotenv`
- `crowdin-api-client`
- `openai`
- `requests`

Install them with:

```bash
pip install python-dotenv crowdin-api-client openai requests
```

---

## Environment Configuration (.env)

Create a file named `.env` at the project root with the following keys:

```bash
# CROWDIN_PERSONAL_TOKEN=123asd123asd   # add your personal access token here with 
# ORGANIZATION=firstpart                # of the link to project. firstpart.crowdin.com
# CROWDIN_PROJECT_ID=123456             #change this to reflect the project number
# OPENAI_API_KEY=sk-........            #add your openAI API access token here generated at platform.openai.com
```

Notes:
- `ORGANIZATION` is the first part of your Crowdin domain (no protocol, no `.crowdin.com`).
- The script’s default target language is Turkish (`tr`). You can change it in `crowdinTranslator.py` if needed.

---

## Usage

Dry run (no AI, only list untranslated for a specific file):

```bash
python crowdinTranslator.py IfcRailDomain.pot --limit=20 --dry-run
```

Translate & upload using AI for a specific file (creates unapproved suggestions in Crowdin):

```bash
python crowdinTranslator.py IfcControlExtension.pot --limit=20
```

Process the entire project with AI (limit per file):

```bash
python crowdinTranslator.py --limit=50
```

Process the entire project in dry run:

```bash
python crowdinTranslator.py --dry-run
```

CLI flags implemented by `crowdinTranslator.py`:

- `--limit=NUM`: maximum number of strings to process per file
- `--dry-run`: do not call OpenAI or upload; just list untranslated source strings
- Positional `.pot` filename: target only that source file; otherwise the whole project is processed

---

If you use Git, add these entries to your `.gitignore`:

```
.env
```

---

## Troubleshooting

- 401/403 errors from Crowdin: verify `CROWDIN_PERSONAL_TOKEN`, `ORGANIZATION`, and `CROWDIN_PROJECT_ID` in `.env`.
- 404 file not found when targeting a `.pot` file: ensure the filename matches exactly what Crowdin reports.
- OpenAI errors or costs: you must have a valid `OPENAI_API_KEY` and an active billing setup.
- Language: the script currently targets Turkish (`tr`). Adjust `TARGET_LANG` in `crowdinTranslator.py` if needed.

## License

This project is free and unencumbered software released into the public domain.

Anyone is free to copy, modify, publish, use, compile, sell, or distribute this software, either in source code form or as a compiled binary, for any purpose, commercial or non-commercial, and by any means.

In jurisdictions that recognize copyright laws, the author or authors of this software dedicate any and all copyright interest in the software to the public domain. We make this dedication for the benefit of the public at large and to the detriment of our heirs and successors. We intend this dedication to be an overt act of relinquishment in perpetuity of all present and future rights to this software under copyright law.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

For more information, please refer to <https://unlicense.org>

