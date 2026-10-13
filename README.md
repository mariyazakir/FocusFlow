# FocusFlow

A free, local-first task planner for college assignments, side-income work, BUD development, and personal life. FocusFlow uses Python, Streamlit, and SQLite. Your tasks are stored in `focusflow.db` on your computer. No account, API key, paid service, or cloud database is required.

## Features

- Overview dashboard with live task counts, completion progress, and category/status charts
- Dark and light appearance switch that styles Streamlit controls to match; hides Streamlit's competing theme/print menu
- Create, edit, update, search, filter, and delete tasks
- MCA, Side Income, BUD, and Personal categories
- Priority, deadline, estimated minutes, notes, repeat setting, and a task-only print button
- Optional permanent daily tasks: return to To do each new day, with previous statuses saved in the local database
- Three-column status board: To do, In progress, and Done
- Monthly calendar, local due/overdue reminders, and an offline day planner ranked by priority and deadline
- Local starter checklists for breaking tasks into steps (no AI account or paid API)
- Responsive layouts for desktop, tablet, and phone-sized screens
- First-use Terms of Use / Privacy Policy agreement; no age or guardian-verification gate

## Public installable web edition

For deployment to Vercel and phone installation, use the separate static PWA in [pwa/README.md](pwa/README.md). The PWA has device-local storage and backup/restore; it does not share data with the Python app automatically. Run `py export_focusflow.py` to create an importable JSON backup from the local SQLite app.

## Run it in VS Code on Windows

1. Install Python 3.10 or newer and VS Code. In VS Code, install the Microsoft Python extension.
2. Open the `FocusFlow` folder in VS Code (`File` → `Open Folder…`).
3. Open **Terminal** → **New Terminal** and create a virtual environment:

   ```powershell
   py -m venv .venv
   ```

4. Activate it in PowerShell:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

   If PowerShell blocks activation, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in that terminal, then activate again. This only changes the current terminal session.

5. Install the free Python packages:

   ```powershell
   py -m pip install -r requirements.txt
   ```

6. Start the app:

   ```powershell
   py -m streamlit run app.py
   ```

   Streamlit opens FocusFlow in your browser. Keep the terminal open while using it; press `Ctrl+C` there to stop the app.

## Run the basic tests

With the virtual environment active, run:

```powershell
py -m unittest discover -s tests -v
```

The PWA policy-consent helper can also be checked with Node.js:

```powershell
node --test pwa/test_legal_consent.cjs
```

## Your data

The app creates `focusflow.db` beside `app.py` the first time it runs. Back up this file to keep your tasks. Deleting it resets the local task list. FocusFlow uses system fonts and works without an internet connection after its Python packages are installed.

Reminders appear inside FocusFlow while the app is running; they are not Windows notifications and do not run in the background. Task breakdowns use free local templates rather than a cloud AI service, so your task details stay on your device.

Permanent daily tasks reset to **To do** when FocusFlow is opened on a new day. The previous date and status are saved locally in `permanent_task_history`. Ordinary deadline tasks are kept as-is, including overdue work, so a day change never silently deletes an assignment.

## Legal pages and first-use agreement

The Terms of Use and Privacy Policy are in `TERMS_OF_USE.md` and `PRIVACY_POLICY.md`. Both are shown in a required first-use dialog. Acceptance, its version and timestamp are stored locally in SQLite or browser storage. A new policy version requires acceptance again. FocusFlow does not ask age or verify a parent/guardian; see the policy for the data-storage details and legal-review note. No policy can guarantee immunity from legal responsibility. The Python/SQLite edition is designed for local, single-device use; Vercel serves only the separate static PWA.
