# playwright-shell 项目指南

## 项目概述

`playwright-shell` 是一个使用 `uv` 管理的 Python 项目，用于处理复杂的浏览器自动化场景。它结合了 Playwright（稳定控制浏览器）、PyAutoGUI（DOM 自动化不足时的键盘/鼠标回退）和工作流模块（自动评论、采集、下载等业务动作）。

**核心特性**：
- CDP 连接模式：默认通过 `http://127.0.0.1:9222` 接管已打开的 OpenClaw Chrome
- 持久化登录：每个站点只需登录一次，多个工作流复用同一浏览器身份
- 模块化架构：浏览器控制、桌面控制、工作流逻辑和任务配置解耦

## 技术栈

- **Python 3.11+**
- **Playwright** - 浏览器自动化
- **PyAutoGUI** - 桌面级键盘/鼠标操作回退
- **Pydantic** - 数据验证和配置
- **Typer** - CLI 框架
- **PyYAML** - 配置文件解析
- **uv** - 依赖管理

## 项目结构

```
src/playwright_shell/
  cli.py                # CLI 入口 (typer app)
  config.py             # 环境变量和 YAML 任务加载 (PS_ 前缀)
  models.py             # TaskSpec, AuthProfileSpec 等数据模型
  runtime.py            # 工作流执行编排
  services/
    auth.py             # 持久化登录档案和认证逻辑
    browser.py          # Playwright 适配器
    desktop.py          # PyAutoGUI 适配器
    page_analyzer.py    # 页面分析工具
  workflows/
    base.py             # Workflow 抽象基类
    registry.py         # 工作流注册
    browse.py           # 通用打开页面工作流
    comment.py          # 自动评论工作流
    collect.py          # 数据采集工作流
    download.py         # 文件下载工作流
    infoq_publish.py    # InfoQ 发布工作流
    infoq_article_publish.py  # InfoQ 文章发布工作流

examples/
  auth_profiles.yaml    # 可复用的登录档案 (知乎、B站、InfoQ 等)
  tasks.yaml            # 示例任务配置
```

## 常用命令

```bash
# 安装依赖
uv sync
uv run playwright install chromium

# 认证管理
uv run playwright-shell auth list
uv run playwright-shell auth login zhihu_default
uv run playwright-shell auth status zhihu_default

# 任务运行
uv run playwright-shell list-tasks
uv run playwright-shell run geekbang_open_demo
uv run playwright-shell run infoq_publish_create_demo
uv run playwright-shell run infoq_publish_article_demo

# 打开并分析页面
uv run playwright-shell open https://www.zhihu.com --auth-profile zhihu_default
```

## 环境变量配置

所有环境变量使用 `PS_` 前缀：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `PS_BROWSER_TYPE` | chromium | 浏览器类型 |
| `PS_BROWSER_MODE` | cdp | 浏览器模式 (cdp/launch) |
| `PS_HEADLESS` | false | 无头模式 |
| `PS_TASK_FILE` | examples/tasks.yaml | 任务配置文件 |
| `PS_AUTH_FILE` | examples/auth_profiles.yaml | 认证档案文件 |
| `PS_CDP_URL` | http://127.0.0.1:9222 | CDP 连接地址 |
| `PS_SHARED_USER_DATA_DIR` | ~/.chrome-custom | 共享用户数据目录 |

## 添加新工作流

1. 在 `src/playwright_shell/workflows/` 中创建新的工作流模块
2. 继承 `Workflow` 基类并实现 `run()` 方法
3. 在 `registry.py` 的 `build_workflow_registry()` 中注册
4. 在 `examples/tasks.yaml` 或其他 YAML 文件中定义任务
5. 如需认证，在 `examples/auth_profiles.yaml` 中配置或复用已有档案

## 工作流基类

```python
from playwright_shell.workflows.base import Workflow, WorkflowContext

class MyWorkflow(Workflow):
    name = "my_workflow"

    def run(self, task: TaskSpec, context: WorkflowContext) -> None:
        # context.settings - AutomationSettings 实例
        # context.logger - Logger 实例
        # context.browser - BrowserSession 实例
        # context.desktop - DesktopController 实例
        pass
```

## 认证档案配置

在 `auth_profiles.yaml` 中定义可复用的登录身份：

```yaml
profiles:
  - name: site_name_default
    provider: site_name
    enabled: true
    base_url: https://example.com
    login_url: https://example.com/login
    description: Site description
    logged_in_selector: ".avatar, .user-profile"
    logged_out_selector: "text=登录, text=注册"
```

## 任务配置

在 `tasks.yaml` 中定义任务：

```yaml
tasks:
  - name: my_task
    workflow: my_workflow
    enabled: true
    auth_profile: site_name_default  # 可选
    description: Task description
    inputs:
      target_url: https://example.com
      # 其他工作流特定参数
```

## VS Code 调试

项目已配置 VS Code 调试，可用模式：
1. `Playwright Shell: Run Task`
2. `Playwright Shell: Open URL`
3. `Playwright Shell: Geekbang Demo`
4. `Playwright Shell: Auth Login`
5. `Playwright Shell: Auth Status`

解释器已固定为 `.venv/bin/python`。

## 测试

```bash
uv run pytest
```

## 代码风格

- 使用 Ruff 进行 linting
- 行宽限制：100 字符
- 目标版本：Python 3.11
- Lint 规则：E, F, I, B

## 注意事项

- 默认连接模式为 CDP，需要 OpenClaw Chrome 已在运行
- 浏览器持久化数据保存在 `~/.chrome-custom`
- 导出的存储快照保存在 `data/storage_states/`
- 截图、页面分析等生成文件保存在 `data/` 目录下
- `.env`、`data/` 等目录已在 `.gitignore` 中排除