# 🚀 Deploying to Streamlit Cloud

Streamlit Cloud is the easiest way to host this application for free. It connects directly to your GitHub repository.

## Prerequisites
1.  **GitHub Account**: You must have this code in a GitHub repository.
2.  **Anthropic API Key**: Your `sk-ant...` key.

## Step 1: Push to GitHub
If you haven't already, push this code to a new GitHub repository.
```bash
git add .
git commit -m "Prepare for Streamlit Cloud deployment"
git push
```

## Step 2: Create App on Streamlit Cloud
1.  Go to [share.streamlit.io](https://share.streamlit.io/).
2.  Click **"New app"**.
3.  Select your repository (`enterprisehub` or whatever you named it).
4.  **Main file path**: Enter this EXACT path:
    `ghl_real_estate_ai/streamlit_demo/app.py`
5.  Click **"Deploy!"**.

## Step 3: Configure Secrets (IMPORTANT)
The app needs your API key to run the AI features.

1.  Once the app is deploying (or if it errors out), click the **Settings** menu (three dots in the top right) > **Settings**.
2.  Go to the **Secrets** tab.
3.  Paste the following configuration:

```toml
[general]
ANTHROPIC_API_KEY = "sk-ant-api03-..."
```
*(Replace `sk-ant-api03-...` with your actual key)*

4.  Click **Save**.

## Step 4: Reboot
If the app showed an error before you added the secret, click **"Reboot app"** in the top-right menu.

---

## Troubleshooting

**Error: "ModuleNotFoundError"**
*   Ensure `ghl_real_estate_ai/streamlit_demo/requirements.txt` exists (it should!).
*   Streamlit looks for requirements in the same folder as `app.py`.

**Error: "sqlite3"**
*   If you see an error about `chromadb` or `sqlite3`, let us know. Streamlit Cloud is usually up to date.

**App is slow?**
*   The first load takes a minute to install dependencies. Be patient!
