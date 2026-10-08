# F1 Strategy Lab: ETL + EDA pipeline (OpenF1)

OpenF1 API -> Pydantic validation + pandas cleaning -> SQLite -> EDA -> static dashboard on Vercel.

    models.py   Pydantic rules      etl.py   Extract (throttled, cached) -> Transform -> Load (data/f1.db)
    eda.py      EDA + writes public/data.json     public/   dashboard (index.html + data.json)
    demo.py     writes SAMPLE data so you can preview the dashboard      tests/offline_test.py   runs everything on fake API data

## Run
    python -m venv .venv && .venv\Scripts\activate      # Mac/Linux: source .venv/bin/activate
    pip install -r requirements.txt
    python etl.py        # first run takes ~15 min (API rate limit); later runs use cache/
    python eda.py        # prints the data profile and writes public/data.json
    python -m http.server -d public 8000     # dashboard at http://127.0.0.1:8000

## Deploy
Push to GitHub, then Vercel -> Add New -> Project -> import the repo -> Framework "Other" -> Deploy.
Commit the real `public/data.json` (created by eda.py) before pushing. Do not commit `cache/` or `data/`.
