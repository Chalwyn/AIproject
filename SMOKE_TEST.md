# Smoke Test – AIproject-hjkc (patched)

## What I patched automatically
- Switched **LLM wrapper**: `frontend/models/get_llm.py` now uses `llm_client.chat_completion` and reads `OPENAI_API_KEY` from env (no hard-coded keys).
- Fixed **package imports**:
  - `frontend/main.py`: changed `import pages.*` → `from frontend.pages import ...`; updated call sites.
  - `frontend/pages/record.py`: changed imports to `from frontend.utils/...`, `from frontend.database/...`, `from frontend.models...`.
- Ensured **package structure** with `__init__.py` in all relevant folders.

## Smoke import results (no network, mocked heavy deps)
All key modules import successfully:
- `frontend` ✅
- `frontend.main` ✅
- `frontend.models.get_llm` ✅
- `frontend.database.db_connector` ✅
- `frontend.pages.record` ✅
- `frontend.pages.plan` ✅
- `frontend.pages.soa` ✅

> Note: The smoke test stubs out `streamlit`, `pydub`, `speech_recognition`, and `mysql.connector` so we can verify imports without those binaries installed here.

## Next steps to run locally
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

export OPENAI_API_KEY="sk-..."        # required
export OPENAI_MODEL="gpt-4o-mini"     # optional

streamlit run frontend/main.py
```

If you use audio upload, install system ffmpeg and Python deps in `requirements.txt`. For MySQL, provide `DB_HOST/PORT/USER/PASSWORD/NAME` env vars if your DB connector expects them.
