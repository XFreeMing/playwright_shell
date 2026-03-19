from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import Page

from playwright_shell.config import AutomationSettings


@dataclass(slots=True)
class PageArtifacts:
    report_path: Path
    screenshot_path: Path
    html_path: Path


class PageAnalyzer:
    def __init__(self, settings: AutomationSettings) -> None:
        self.settings = settings

    def inspect(self, page: Page, *, label: str | None = None) -> PageArtifacts:
        analysis = page.evaluate(
            """
            () => {
              const limit = 25;
              const textValue = (element) => (
                element.innerText || element.textContent || ''
              ).trim();
              const buildSelector = (element) => {
                if (!element) return '';
                if (element.id) return `#${element.id}`;
                if (element.getAttribute('data-testid')) {
                  return `[data-testid="${element.getAttribute('data-testid')}"]`;
                }
                if (element.getAttribute('name')) {
                  return `${element.tagName.toLowerCase()}[name="${element.getAttribute('name')}"]`;
                }
                const classNames = [...element.classList].slice(0, 2).join('.');
                if (classNames) return `${element.tagName.toLowerCase()}.${classNames}`;
                return element.tagName.toLowerCase();
              };
              const visible = (element) => {
                const style = window.getComputedStyle(element);
                const rect = element.getBoundingClientRect();
                return (
                  style.visibility !== 'hidden' &&
                  style.display !== 'none' &&
                  rect.width > 0 &&
                  rect.height > 0
                );
              };
              const describe = (element) => ({
                tag: element.tagName.toLowerCase(),
                selector: buildSelector(element),
                text: textValue(element).slice(0, 160),
                href: element.getAttribute('href') || '',
                type: element.getAttribute('type') || '',
                role: element.getAttribute('role') || '',
                placeholder: element.getAttribute('placeholder') || '',
                ariaLabel: element.getAttribute('aria-label') || '',
              });
              const pick = (selector) => [...document.querySelectorAll(selector)]
                .filter(visible)
                .slice(0, limit)
                .map(describe);

              return {
                title: document.title,
                url: window.location.href,
                forms: pick('form'),
                inputs: pick('input, textarea, select'),
                buttons: pick(
                  'button, input[type="button"], input[type="submit"], [role="button"]'
                ),
                links: pick('a[href]'),
                headings: [...document.querySelectorAll('h1, h2, h3')]
                  .filter(visible)
                  .slice(0, limit)
                  .map((element) => ({
                    tag: element.tagName.toLowerCase(),
                    text: textValue(element).slice(0, 160),
                    selector: buildSelector(element),
                  })),
              };
            }
            """
        )

        artifacts = self._build_paths(page.url, label)
        artifacts.report_path.write_text(
            self._format_report(analysis),
            encoding="utf-8",
        )
        artifacts.html_path.write_text(page.content(), encoding="utf-8")
        page.screenshot(path=str(artifacts.screenshot_path), full_page=True)
        return artifacts

    def _build_paths(self, page_url: str, label: str | None) -> PageArtifacts:
        stem = label or self._slugify(page_url)
        report_path = self.settings.page_analysis_dir / f"{stem}.json"
        screenshot_path = self.settings.page_analysis_dir / f"{stem}.png"
        html_path = self.settings.page_analysis_dir / f"{stem}.html"
        return PageArtifacts(
            report_path=report_path,
            screenshot_path=screenshot_path,
            html_path=html_path,
        )

    def _slugify(self, page_url: str) -> str:
        parsed = urlparse(page_url)
        parts = [parsed.netloc or "page", parsed.path.strip("/").replace("/", "-")]
        slug = "-".join(part for part in parts if part)
        slug = slug.replace(".", "-").replace("_", "-")
        return slug[:120] or "page"

    def _format_report(self, payload: dict) -> str:
        import json

        return json.dumps(payload, ensure_ascii=False, indent=2)