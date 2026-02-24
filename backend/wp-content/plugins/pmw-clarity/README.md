# PMW Clarity

WordPress admin helper for Microsoft Clarity. **Does not inject the Clarity script** — tracking is handled by the frontend (React) with cookie consent.

## What it does

- Adds **Settings → Clarity** in the WordPress admin.
- Lets you set your Clarity **project ID** (default: `vmezs6szy4`).
- Provides an **“Open Clarity dashboard”** link to view heatmaps and session recordings at clarity.microsoft.com.

## What it does not do

- Does **not** load the Clarity script on any WordPress-rendered or admin pages.
- Does **not** track wp-admin; the frontend app is the only place where the tag runs (after user consent).

## Tracking

The Clarity tag is loaded only in the React frontend when the user accepts analytics cookies (`VITE_CLARITY_PROJECT_ID` in frontend `.env`). This plugin is for viewing the dashboard from WordPress only.
