# playwright-shell

`playwright-shell` is a `uv`-managed Python project for complex browser automation.
It combines:

- Playwright for stable browser/page/context control
- `connect_over_cdp()` support for taking over an already-open OpenClaw Chrome session
- PyAutoGUI for keyboard/mouse fallbacks when DOM automation is insufficient
- Workflow modules for business actions such as commenting, collection, and downloads

The architecture is designed so that browser control, desktop control, workflow logic,
and task configuration stay isolated.

Persistent login is treated as a first-class capability: login once per site profile,
then reuse the same browser identity across workflows.

## Project layout

```text
src/playwright_shell/
  cli.py                # CLI entrypoint
  config.py             # env and YAML task loading
  models.py             # task and workflow models
  runtime.py            # workflow execution orchestration
  services/
    auth.py             # persistent login profiles and provider logic
    browser.py          # Playwright adapter
    desktop.py          # PyAutoGUI adapter
  workflows/
    base.py             # workflow contract
    registry.py         # workflow registration
    browse.py           # generic open-page workflow for demos and inspection
    comment.py          # example auto-comment workflow
    collect.py          # example data collection workflow
    download.py         # example file download workflow
examples/
  auth_profiles.yaml    # reusable login profiles (Zhihu, Bilibili, etc.)
  tasks.yaml            # sample tasks
```

By default, the project connects to the Chrome instance already opened by OpenClaw,
using the shared profile directory `~/.chrome-custom` and the CDP endpoint
`http://127.0.0.1:9222`.

## Why this structure

- Adding a new automation scenario only requires a new workflow module and a task config.
- Playwright and PyAutoGUI are wrapped behind services, so future replacement is localized.
- Login persistence is independent from business workflows, so multiple scripts can share the same site session.
- The default browser mode attaches to the existing OpenClaw Chrome instead of launching a new one.
- YAML task files allow multiple scenarios without duplicating code.
- CLI execution keeps local debugging and future scheduler integration simple.

## Quick start

```bash
uv sync
uv run playwright install chromium
cp .env.example .env
uv run playwright-shell auth list
uv run playwright-shell auth login zhihu_default
uv run playwright-shell open https://www.zhihu.com --auth-profile zhihu_default
uv run playwright-shell list-tasks
uv run playwright-shell run geekbang_open_demo
uv run playwright-shell run comment_demo
```

After a profile is logged in once, subsequent task runs can reuse that profile via `auth_profile`.
The persistent browser data stays in `~/.chrome-custom`, and an exported storage snapshot
is written to `data/storage_states/`.

## Environment configuration

All settings use the `PS_` prefix.

Examples:

```env
PS_BROWSER_TYPE=chromium
PS_BROWSER_MODE=cdp
PS_HEADLESS=false
PS_BASE_URL=https://example.com
PS_TASK_FILE=examples/tasks.yaml
PS_AUTH_FILE=examples/auth_profiles.yaml
PS_DOWNLOADS_DIR=data/downloads
PS_SCREENSHOT_DIR=data/screenshots
PS_PAGE_ANALYSIS_DIR=data/page_analysis
PS_PROFILES_DIR=data/profiles
PS_STORAGE_STATES_DIR=data/storage_states
PS_CHROME_EXECUTABLE_PATH=/opt/google/chrome/chrome
PS_SHARED_USER_DATA_DIR=${HOME}/.chrome-custom
PS_CDP_URL=http://127.0.0.1:9222
PS_REMOTE_DEBUGGING_PORT=9222
PS_OPENCLAW_CONFIG_PATH=${HOME}/.openclaw/openclaw.json
```

## Persistent login workflow

Use `auth_profiles.yaml` to define reusable login identities per site.

Example flow:

1. Configure a profile such as `zhihu_default` or `bilibili_default`
2. Run `uv run playwright-shell auth login zhihu_default`
3. Complete the login manually in the opened browser
4. Reuse that profile in any task by setting `auth_profile: zhihu_default`

This keeps login logic independent from comment, collect, and download workflows.
Later scripts only need to reference the profile name.

Because the default connection mode is CDP takeover, login happens in the same OpenClaw Chrome
instance and reuses the existing `~/.chrome-custom` profile directory.

## Open Source Hygiene

Before publishing, keep `.env`, `.venv`, `.pytest_cache`, `.ruff_cache`, and `data/` out of version control.
This repository already ignores those paths in `.gitignore`, so generated screenshots, page analysis HTML,
and storage state files should not be committed.

## Open And Analyze A Page

Use the `open` command when you want to inspect a page and identify automation entry points.

```bash
uv run playwright-shell open https://xie.infoq.cn/write/article --auth-profile zhihu_default
```

This command:

1. Connects to the already-open OpenClaw Chrome via `http://127.0.0.1:9222`
2. Opens the target page in the same browser session and user data directory
3. Saves a JSON analysis report, HTML snapshot, and full-page screenshot under `data/page_analysis/`

The analysis report includes visible forms, inputs, buttons, links, and headings so you can
quickly identify selectors and interaction targets.

## Geekbang Demo

The project includes a ready-to-run demo task for opening Geekbang:

```bash
uv run playwright-shell run geekbang_open_demo
```

This task connects to the existing OpenClaw Chrome, opens `https://time.geekbang.org/`,
and saves page analysis artifacts under `data/page_analysis/`.

## VS Code Debug

The project includes ready-to-use VS Code debug configurations in `.vscode/launch.json`.

Available launch modes:

1. `Playwright Shell: Run Task`
2. `Playwright Shell: Open URL`
3. `Playwright Shell: Geekbang Demo`
4. `Playwright Shell: Auth Login`
5. `Playwright Shell: Auth Status`

The workspace also pins the interpreter to `.venv/bin/python` in `.vscode/settings.json`,
so VS Code debugging uses the same environment as `uv run`.

## Extension path

For future features such as automatic commenting, account login flows, scraping, and
audio/video downloads, the recommended pattern is:

1. Add a workflow in `src/playwright_shell/workflows/`
2. Register it in `registry.py`
3. Reuse an existing auth profile or add a new one in `examples/auth_profiles.yaml`
4. Define one or more tasks in `examples/tasks.yaml` or another YAML file
5. Set `auth_profile` on tasks that require an authenticated session
6. Keep selectors, URLs, and per-task parameters in config instead of hardcoding them

If media downloads become more specialized, add a dedicated adapter layer under
`services/` rather than bloating workflow modules.
