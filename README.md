# BusXLaw 5-Year Financial Model (Streamlit)

Interactive version of our pro forma and unit economics for the Topic #21 add-on.
Same math as `BusXLaw_Financial_Model.xlsx`. The base case matches the Excel model exactly.

## Files
- `model.py` — every assumption and the 5-year model (revenue, costs, P&L, CAC, LTV, break-even)
- `app.py` — the Streamlit dashboard (sidebar sliders, KPI cards, four charts, P&L table, CSV download)
- `requirements.txt` — Python packages to install

## Run it in VS Code
1. Unzip this folder and open it in VS Code (File > Open Folder).
2. Open a terminal (Terminal > New Terminal).
3. Create a virtual environment:
   - Windows: `python -m venv .venv` then `.venv\Scripts\activate`
   - Mac: `python3 -m venv .venv` then `source .venv/bin/activate`
4. Install packages: `pip install -r requirements.txt`
5. Start the app: `streamlit run app.py`
6. Your browser opens at http://localhost:8501. Press Ctrl+C in the terminal to stop it.

## Share a live link (optional)
1. Push this folder to a public GitHub repo.
2. Go to share.streamlit.io, sign in with GitHub and choose **Create app**.
3. Pick the repo, set the main file to `app.py` and deploy.
4. Send the link with your add-ons.

## Changing an assumption
Edit the default values in the `Assumptions` class in `model.py`. The sliders cover the
levers we tested most: demo volume, conversion, churn, attorney members and pricing.
