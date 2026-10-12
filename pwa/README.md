# FocusFlow PWA for Vercel

This is a separate, installable web edition of FocusFlow. It is plain HTML, CSS, and JavaScript: there is no paid API, database, account system, build step, or recurring hosting bill. Vercel serves the static files over HTTPS; the service worker caches the app shell for offline use.

## Local preview

From this folder, run:

```powershell
py -m http.server 8000
```

Open <http://localhost:8000>. Keep the terminal open. Service workers work on `localhost` for development; installing to phones requires the deployed HTTPS address.

## Deploy on Vercel

1. Create or sign in to a Vercel account and put this `pwa` folder in a Git repository you can connect to Vercel.
2. In Vercel, choose **Add New → Project** and import that repository.
3. Set **Root Directory** to `pwa` if this folder sits inside the larger FocusFlow repository.
4. Choose **Other** as the framework preset. Leave the build and output commands empty; this is a static site.
5. Deploy. Vercel gives the site an HTTPS address. Open that address on a phone and use the browser's **Install app** or **Add to Home Screen** action. Supported browsers also show FocusFlow's Install button.

The free Vercel Hobby plan is for personal, non-commercial use under Vercel's current terms. Check those terms if you plan to use the app commercially or monetize it.

## Task data and backups

The PWA stores tasks in the current browser's `localStorage`. Each visitor gets a separate private task list without registering. No task data is sent to Vercel. Data does not automatically sync to another browser or phone, and clearing browser data can remove it, so use **Export backup** regularly. Choose **Import backup** on the other device to restore it.

The first visit requires accepting the Terms of Use and acknowledging the Privacy Policy. Both pages are linked from the footer and the agreement dialog. Consent version and timestamp are stored in the browser. Review and complete the policy placeholders in `../TERMS_OF_USE.md` and `../PRIVACY_POLICY.md` before public release, then run `py build_legal_pages.py` from the parent project folder to regenerate `terms.html` and `privacy.html`. The policies must match the final deployment and hosting setup.

To migrate from the local Python/SQLite app, run `py export_focusflow.py` from the parent `FocusFlow` folder. Then open the deployed PWA and import the generated `focusflow-backup.json` file.

## Install behavior

- Android/Chromium browsers offer an Install button when the browser determines installation is available.
- On iPhone/iPad, open the HTTPS site in Safari, choose **Share**, then **Add to Home Screen**.
- The service worker caches the app shell. Task data remains on that device, so it is available offline after the first visit.
- Reminders are shown inside the open app. This static version does not send background push notifications.
