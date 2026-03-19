from __future__ import annotations

import os
from typing import Any

from playwright_shell.config import AutomationSettings


class DesktopAutomationUnavailable(RuntimeError):
    pass


class DesktopController:
    def __init__(self, settings: AutomationSettings) -> None:
        self.settings = settings
        self._pyautogui: Any | None = None

    def _load_pyautogui(self) -> Any:
        if self._pyautogui is not None:
            return self._pyautogui

        if os.name != "nt" and not os.environ.get("DISPLAY"):
            raise DesktopAutomationUnavailable(
                "PyAutoGUI requires an active desktop session. DISPLAY is not set."
            )

        import pyautogui

        pyautogui.PAUSE = self.settings.pyautogui_pause
        pyautogui.FAILSAFE = True
        self._pyautogui = pyautogui
        return pyautogui

    def click(self, x: int | None = None, y: int | None = None) -> None:
        self._load_pyautogui().click(x=x, y=y)

    def press(self, key: str) -> None:
        self._load_pyautogui().press(key)

    def hotkey(self, *keys: str) -> None:
        self._load_pyautogui().hotkey(*keys)

    def typewrite(self, text: str, interval: float = 0.02) -> None:
        self._load_pyautogui().write(text, interval=interval)

    def locate_and_click(self, image_path: str, confidence: float = 0.9) -> None:
        pyautogui = self._load_pyautogui()
        location = pyautogui.locateCenterOnScreen(image_path, confidence=confidence)
        if location is None:
            raise DesktopAutomationUnavailable(
                f"Could not locate image on screen: {image_path}"
            )
        pyautogui.click(location.x, location.y)
