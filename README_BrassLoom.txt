
BrassLoom — HBCU/MSI Grants Radar
=================================

What you have
-------------
1) brassloom_harvest.py
   - Uses public APIs and RSS to pull live opportunities (Grants.gov Search2, NIH Guide RSS, NSF funding RSS).
   - Filters using HBCU/MSI related keywords.
   - Computes a priority score and writes opportunities.json.

2) brassloom.html
   - Offline dashboard. Open it in a browser.
   - Click "Load sample data" or upload a JSON file exported by the harvester.
   - Filter by keywords and minimum score, sort by score or date.

3) opportunities_sample.json
   - Seed dataset to test the dashboard immediately.

How to harvest live data
------------------------
1) Ensure Python 3.9+ and install deps:
   pip install requests feedparser

2) Run the harvester to fetch last 60 days and emphasize HBCU/MSI terms:
   python brassloom_harvest.py --out opportunities.json --days 60 --keywords "HBCU,MSI,minority serving,HSI,Tribal,TCU,Black,broadening participation,EPSCoR"

3) Open brassloom.html and upload opportunities.json, or place opportunities.json in the same folder as the HTML and it will load automatically.

Priority scoring
----------------
- +20 if "HBCU" appears
- +15 if "MSI" appears
- +10 per other keyword match
- +10 if the close date is within 30 days, +5 if within 60 days

Next steps
----------
- Add source-specific eligibility parsing and track-specific scores.
- Persist starred items and push email alerts.
- Add campus routing export to your GSU Cayuse‑Lite workbook.
- Add cron on a VM to refresh opportunities.json daily.
