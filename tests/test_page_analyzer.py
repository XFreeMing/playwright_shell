from playwright_shell.config import AutomationSettings
from playwright_shell.services.page_analyzer import PageAnalyzer


def test_slugify_builds_stable_report_name() -> None:
    analyzer = PageAnalyzer(AutomationSettings())

    slug = analyzer._slugify("https://xie.infoq.cn/write/article")

    assert slug == "xie-infoq-cn-write-article"


def test_build_paths_uses_page_analysis_dir() -> None:
    analyzer = PageAnalyzer(AutomationSettings())

    artifacts = analyzer._build_paths("https://www.zhihu.com/question/1", None)

    assert artifacts.report_path.as_posix().endswith(
        "data/page_analysis/www-zhihu-com-question-1.json"
    )