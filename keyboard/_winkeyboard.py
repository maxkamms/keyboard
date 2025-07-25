# -*- coding: utf-8 -*-
"""
Patched version of keyboard._winkeyboard
Fixes the 'stuck Win/L key after Win+L' bug by reconciling cached key
state with the real hardware state.

© 2025  MIT‑licensed like the original.
"""
from __future__ import annotations
import threading
import time
from ctypes import wintypes, windll

########################################################################
#  ⬇  ORIGINAL _winkeyboard IMPORT ‑‑ everything else stays the same  ⬇
########################################################################
from importlib import import_module as _imp
_orig = _imp('keyboard._winkeyboard_original')         # renamed copy!
globals().update({k: v for k, v in _orig.__dict__.items()
                  if not (k.startswith('__') and k != '__all__')})
# `_pressed_events` is now the SAME object used by the original code.
_pressed_events = _orig._pressed_events                # type: ignore

########################################################################
#  ⬇  ***  ADDED CODE – stuck‑key watchdog  ***  ⬇
########################################################################
user32 = windll.user32
MapVirtualKey = user32.MapVirtualKeyW
GetAsyncKeyState = user32.GetAsyncKeyState
MAPVK_VSC_TO_VK_EX = 3  # scan‑code → virtual‑key (distinguish L/R)

def _scan_code_is_down(sc: int) -> bool:
    vk = MapVirtualKey(sc, MAPVK_VSC_TO_VK_EX)
    if vk == 0:
        return False
    return bool(GetAsyncKeyState(vk) & 0x8000)

def _flush_stale_keys() -> None:
    for sc in list(_pressed_events):          # copy → safe while mutating
        if not _scan_code_is_down(sc):
            _pressed_events.pop(sc, None)

def _start_watchdog(interval: float = .10) -> None:
    def _worker() -> None:
        while True:
            _flush_stale_keys()
            time.sleep(interval)

    threading.Thread(name='keyboard-stuck-key-fix',
                     target=_worker,
                     daemon=True).start()

_start_watchdog()
########################################################################
#  ⬆  ***  END   ADDED CODE ***  ⬆
########################################################################
