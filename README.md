# Sales and Profit Optimization and Mathematical Modeling

## Run ONLINE without installing Python
1. Open https://github.com and sign in or create your account.
2. Click + > New repository; name it `sales-profit-optimizer`; click Create repository.
3. Click `uploading an existing file` (or Add file > Upload files). Upload `app.py`, `products.csv`, and `requirements.txt` directly into the repository root; click Commit changes.
4. Open https://share.streamlit.io, sign in with GitHub, and click Create app.
5. Select your GitHub repository, branch `main`, and main file `app.py`. Click Deploy.
6. Open your `streamlit.app` URL. Test Dashboard > Edit Products > Optimization.

## What's included
- 49 products imported from the user's Excel Raw_Data sheet.
- Revenue, cost, profit, profit-margin analysis and charts.
- Editable prices, costs, quantities, resources, demand; save edits to CSV.
- MILP optimization with budget, production target, maximum demand, optional time/raw material constraints.
- Exports analysis and optimization output to CSV.

## Important limitations
- Browser edits stay only during the current user session: export a CSV to save them.
- The app is a working Python source project, not a live hosted site until deployed from your GitHub account.
- This app is for educational demonstration. Revenue and profit estimates assume all produced units sell at listed prices.
