# playwright-shell

`playwright-shell` is a `uv`-managed Python project for complex browser automation.
`playwright-shell` 是一个使用 `uv` 管理的 Python 项目，用于处理复杂的浏览器自动化场景。

It combines:
它结合了：

- Playwright for stable browser/page/context control
- Playwright，用于稳定控制浏览器、上下文和页面
- `connect_over_cdp()` support for taking over an already-open OpenClaw Chrome session
- `connect_over_cdp()`，用于接管已经由 OpenClaw 打开的 Chrome 会话
- PyAutoGUI for keyboard/mouse fallbacks when DOM automation is insufficient
- PyAutoGUI，用于在 DOM 自动化不足时补充键盘和鼠标操作
- Workflow modules for business actions such as commenting, collection, and downloads
- 工作流模块，用于实现自动评论、信息采集、下载等业务动作
- InfoQ publishing workflow for opening the publish page and triggering article creation
- InfoQ 发布工作流，用于打开发布页并触发文章创建入口

The architecture is designed so that browser control, desktop control, workflow logic,
and task configuration stay isolated.
整个架构将浏览器控制、桌面控制、业务逻辑和任务配置解耦，便于维护和扩展。

Persistent login is treated as a first-class capability: login once per site profile,
then reuse the same browser identity across workflows.
持久化登录是这个项目的一等能力：每个站点档案只需登录一次，后续多个工作流都可以复用同一浏览器身份。

## Project layout

## 项目结构

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
默认情况下，项目会连接到已经由 OpenClaw 打开的 Chrome，复用共享用户目录 `~/.chrome-custom`，并通过 `http://127.0.0.1:9222` 这个 CDP 入口接管浏览器。

## Why this structure

## 为什么这样设计

- Adding a new automation scenario only requires a new workflow module and a task config.
- 新增自动化场景时，通常只需要新增一个 workflow 模块和一份任务配置。
- Playwright and PyAutoGUI are wrapped behind services, so future replacement is localized.
- Playwright 和 PyAutoGUI 都被封装在 service 层，后续替换成本更低。
- Login persistence is independent from business workflows, so multiple scripts can share the same site session.
- 登录持久化独立于业务工作流，多个脚本可以共享同一个站点会话。
- The default browser mode attaches to the existing OpenClaw Chrome instead of launching a new one.
- 默认浏览器模式会接管现有 OpenClaw Chrome，而不是再启动一个新浏览器。
- YAML task files allow multiple scenarios without duplicating code.
- YAML 任务文件可以承载多个场景，避免重复写代码。
- CLI execution keeps local debugging and future scheduler integration simple.
- CLI 方式运行，既方便本地调试，也便于后续接入调度系统。

## Quick start

## 快速开始

```bash
uv sync
uv run playwright install chromium
cp .env.example .env
uv run playwright-shell auth list
uv run playwright-shell auth login zhihu_default
uv run playwright-shell open https://www.zhihu.com --auth-profile zhihu_default
uv run playwright-shell list-tasks
uv run playwright-shell run geekbang_open_demo
uv run playwright-shell run infoq_publish_create_demo
uv run playwright-shell run comment_demo
```

After a profile is logged in once, subsequent task runs can reuse that profile via `auth_profile`.
The persistent browser data stays in `~/.chrome-custom`, and an exported storage snapshot
is written to `data/storage_states/`.
某个站点档案完成一次登录后，后续任务只要设置 `auth_profile` 就可以复用该登录态。
浏览器持久化数据保存在 `~/.chrome-custom`，导出的存储快照保存在 `data/storage_states/`。

## Environment configuration

## 环境配置

All settings use the `PS_` prefix.
所有环境变量统一使用 `PS_` 前缀。

Examples:
示例：

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

## 持久化登录流程

Use `auth_profiles.yaml` to define reusable login identities per site.
使用 `auth_profiles.yaml` 为不同站点定义可复用的登录身份。

Example flow:
示例流程：

1. Configure a profile such as `zhihu_default` or `bilibili_default`
1. 配置一个站点档案，例如 `zhihu_default` 或 `bilibili_default`
2. Run `uv run playwright-shell auth login zhihu_default`
2. 执行 `uv run playwright-shell auth login zhihu_default`
3. Complete the login manually in the opened browser
3. 在打开的浏览器中手动完成登录
4. Reuse that profile in any task by setting `auth_profile: zhihu_default`
4. 在任意任务中设置 `auth_profile: zhihu_default` 来复用这个档案

This keeps login logic independent from comment, collect, and download workflows.
Later scripts only need to reference the profile name.
这样登录逻辑就不会耦合进评论、采集、下载等业务工作流，后续脚本只需要引用档案名即可。

Because the default connection mode is CDP takeover, login happens in the same OpenClaw Chrome
instance and reuses the existing `~/.chrome-custom` profile directory.
由于默认连接模式是 CDP 接管，登录动作发生在同一个 OpenClaw Chrome 实例中，并复用现有的 `~/.chrome-custom` 用户目录。

## Open Source Hygiene

## 开源前清理建议

Before publishing, keep `.env`, `.venv`, `.pytest_cache`, `.ruff_cache`, and `data/` out of version control.
This repository already ignores those paths in `.gitignore`, so generated screenshots, page analysis HTML,
and storage state files should not be committed.
在发布前，务必不要将 `.env`、`.venv`、`.pytest_cache`、`.ruff_cache` 和 `data/` 纳入版本控制。
当前仓库已在 `.gitignore` 中忽略这些路径，因此截图、页面分析 HTML、存储状态等生成文件不应提交。

## Open And Analyze A Page

## 打开并分析页面

Use the `open` command when you want to inspect a page and identify automation entry points.
当你需要分析页面结构、定位自动化切入点时，可以使用 `open` 命令。

```bash
uv run playwright-shell open https://xie.infoq.cn/write/article --auth-profile zhihu_default
```

This command:
这个命令会：

1. Connects to the already-open OpenClaw Chrome via `http://127.0.0.1:9222`
1. 通过 `http://127.0.0.1:9222` 连接到已经打开的 OpenClaw Chrome
2. Opens the target page in the same browser session and user data directory
2. 在相同浏览器会话和相同用户数据目录中打开目标页面
3. Saves a JSON analysis report, HTML snapshot, and full-page screenshot under `data/page_analysis/`
3. 在 `data/page_analysis/` 下保存 JSON 分析报告、HTML 快照和整页截图

The analysis report includes visible forms, inputs, buttons, links, and headings so you can
quickly identify selectors and interaction targets.
分析报告会包含页面上可见的表单、输入框、按钮、链接和标题，方便快速定位选择器和交互目标。

## Geekbang Demo

## 极客时间 Demo

The project includes a ready-to-run demo task for opening Geekbang:
项目内置了一个可直接运行的极客时间打开示例：

```bash
uv run playwright-shell run geekbang_open_demo
```

This task connects to the existing OpenClaw Chrome, opens `https://time.geekbang.org/`,
and saves page analysis artifacts under `data/page_analysis/`.
这个任务会连接现有的 OpenClaw Chrome，打开 `https://time.geekbang.org/`，并把页面分析产物保存到 `data/page_analysis/`。

## InfoQ Demo

## InfoQ 示例

The project includes a demo task for opening the InfoQ publish page and clicking the `立即创作` button.
项目内置了一个 InfoQ 示例任务，用于打开发布页并点击 `立即创作` 按钮。

```bash
uv run playwright-shell run infoq_publish_create_demo
```

This task opens `https://www.infoq.cn/profile/C1552CBAA94214/publish`, waits for the SPA content,
finds the create button by role or text, clicks it, and saves analysis artifacts after the click.
这个任务会打开 `https://www.infoq.cn/profile/C1552CBAA94214/publish`，等待 SPA 页面渲染完成后，
通过角色或文本定位 `立即创作` 按钮，点击后再保存页面分析产物。

The repository also includes an article publish demo task:
仓库里还提供了一个完整的发文 demo 任务：

```bash
uv run playwright-shell run infoq_publish_article_demo
```

This task clicks the create button, captures the newly opened draft tab, fills the article title and body,
opens the publish settings dialog, writes the summary and tags, and clicks `确定`.
这个任务会点击创作按钮，捕获新打开的草稿页签，填写文章标题和正文，打开发布设置弹窗，
填写摘要和标签，最后点击 `确定`。

## VS Code Debug

## VS Code 调试

The project includes ready-to-use VS Code debug configurations in `.vscode/launch.json`.
项目已经提供了可直接使用的 VS Code 调试配置，位于 `.vscode/launch.json`。

Available launch modes:
可用的启动模式包括：

1. `Playwright Shell: Run Task`
2. `Playwright Shell: Open URL`
3. `Playwright Shell: Geekbang Demo`
4. `Playwright Shell: Auth Login`
5. `Playwright Shell: Auth Status`

The workspace also pins the interpreter to `.venv/bin/python` in `.vscode/settings.json`,
so VS Code debugging uses the same environment as `uv run`.
工作区还在 `.vscode/settings.json` 中将解释器固定为 `.venv/bin/python`，因此 VS Code 调试时使用的环境与 `uv run` 保持一致。

## Extension path

## 扩展建议

For future features such as automatic commenting, account login flows, scraping, and
audio/video downloads, the recommended pattern is:
对于后续的自动评论、账号登录流程、信息抓取、音视频下载等需求，推荐按以下方式扩展：

1. Add a workflow in `src/playwright_shell/workflows/`
1. 在 `src/playwright_shell/workflows/` 中新增一个 workflow
2. Register it in `registry.py`
2. 在 `registry.py` 中注册它
3. Reuse an existing auth profile or add a new one in `examples/auth_profiles.yaml`
3. 复用已有的 auth profile，或者在 `examples/auth_profiles.yaml` 中新增一个
4. Define one or more tasks in `examples/tasks.yaml` or another YAML file
4. 在 `examples/tasks.yaml` 或其他 YAML 文件中定义任务
5. Set `auth_profile` on tasks that require an authenticated session
5. 对需要登录态的任务设置 `auth_profile`
6. Keep selectors, URLs, and per-task parameters in config instead of hardcoding them
6. 将选择器、URL 和任务参数放在配置里，而不是硬编码在脚本中

If media downloads become more specialized, add a dedicated adapter layer under
`services/` rather than bloating workflow modules.
如果后续媒体下载逻辑变得更复杂，建议在 `services/` 下新增专用适配层，而不是把 workflow 模块继续堆大。
