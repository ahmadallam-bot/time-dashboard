# Time Dashboard

A live, filterable dashboard for where your week goes. Reads your Google
Calendar, buckets each event into categories, and shows colored charts plus a
week-on-week trend. Runs as a hosted web app you open at a URL.

Three data sources, switchable in the sidebar:
1. **Google Calendar** - live (needs a one-time service-account setup, below)
2. **Upload CSV** - columns: `Week Start, Week End, Category, Hours`
3. **Sample week** - bundled data, works with zero setup (use this to test first)

---

## 1. Try it locally (5 min, no Google setup)

```bash
pip install -r requirements.txt
streamlit run app.py
```

A browser tab opens. In the sidebar pick **Sample week** - the full dashboard
renders immediately. This confirms everything works before wiring up Google.

---

## 2. Deploy to a live URL (Streamlit Community Cloud, free)

1. Push this folder to a **GitHub repo** (private is fine).
2. Go to <https://share.streamlit.io> and sign in with GitHub.
3. **New app** -> pick your repo, branch, and `app.py` -> Deploy.
4. You now have a public URL. It still defaults to Sample week until you add
   calendar secrets (next section).

---

## 3. Connect your Google Calendar (one-time)

The app reads your calendar through a **service account** - a robot Google
identity you grant read-only access to your calendar.

**a) Create the service account**
- Go to <https://console.cloud.google.com> -> create (or pick) a project.
- **APIs & Services -> Library -> Google Calendar API -> Enable.**
- **APIs & Services -> Credentials -> Create credentials -> Service account.**
- Give it a name (e.g. `time-dashboard`), create, then open it ->
  **Keys -> Add key -> JSON.** A `.json` file downloads. Keep it safe.

**b) Share your calendar with it**
- Copy the service account's email (looks like
  `time-dashboard@your-project.iam.gserviceaccount.com`).
- In Google Calendar -> your calendar -> **Settings and sharing ->
  Share with specific people -> Add** that email -> permission
  **"See all event details."**

**c) Give the app the credentials**
- Locally: copy `.streamlit/secrets.toml.example` to
  `.streamlit/secrets.toml` and paste the values from the JSON file.
- On Streamlit Cloud: **App -> Settings -> Secrets** and paste the same TOML.
- Set `default_calendar_id` to your calendar (your email).

Reload the app, choose **Google Calendar** in the sidebar, pick a date range,
and it reads live. `secrets.toml` is git-ignored - never commit it.

---

## 4. Refine the categories

All bucketing lives in **`categories.py`**:
- `RULES` - `(keyword, category)` pairs, first match wins (order matters).
- `COLORS` - one fixed color per category.
- `FALLBACK` - where unmatched events land (`Uncategorized`, so you can spot
  what needs a rule).

Edit, commit, and Streamlit Cloud redeploys automatically.

---

## Roadmap (things to add later)

- **Smarter categorization** - replace keyword rules with a call to the Claude
  API per refresh, so events are bucketed by judgment (handles vague titles
  like "Others" or "Deep work"). Drop-in inside `classify`.
- **More sources** - blend in the tracking Sheet, Fleetrunnr exports, or Jira
  so the dashboard reflects more than calendar time.
- **Sub-categories** - split the "Admin, Email & Misc" catch-all into Email /
  Planning / Reporting / Systems.
- **Auto weekly email** - pair with the Apps Script so a snapshot lands each
  Sunday.
