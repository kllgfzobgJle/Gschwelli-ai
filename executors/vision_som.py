"""Selective Cloud Vision Set-of-Marks (SoM) capture & annotation (Tier 3)."""

from __future__ import annotations

import io
from typing import Any, Dict, List, Optional, Tuple

import mss
from PIL import Image, ImageDraw, ImageFont
import win32gui

from core.blackboard import blackboard
from core.safety import is_terminal_window
from executors.win32_uia import get_active_target_hwnd, uia_executor


def capture_window_som_jpeg(
    hwnd: Optional[int] = None,
    max_width: int = 1280,
    jpeg_quality: int = 85,
) -> Tuple[bytes, List[Dict[str, Any]], Tuple[int, int, int, int]]:
    """
    Capture ONLY the bounding box of the active target window using `mss` and `win32gui.GetWindowRect`,
    draw Set-of-Marks (SoM) numbering tags (`[1]`, `[2]`, ...) on detected interactive areas using Pillow,
    and compress to JPEG (max width 1280px, quality 85%).
    """
    target_hwnd = hwnd or get_active_target_hwnd(exclude_terminal=True)
    if not target_hwnd or not win32gui.IsWindow(target_hwnd) or is_terminal_window(target_hwnd):
        raise RuntimeError("No valid non-terminal target window available for Tier 3 Set-of-Marks capture.")

    left, top, right, bottom = win32gui.GetWindowRect(target_hwnd)
    width = max(1, right - left)
    height = max(1, bottom - top)

    bbox = {"left": int(left), "top": int(top), "width": int(width), "height": int(height)}
    with mss.mss() as sct:
        shot = sct.grab(bbox)
        img = Image.frombytes("RGB", shot.size, shot.rgb)

    # Detect interactive UIA regions inside the target window
    controls = uia_executor.inspect_window_controls(hwnd=target_hwnd, max_elements=35)
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None

    som_elements: List[Dict[str, Any]] = []
    for idx, ctrl in enumerate(controls, start=1):
        c_left, c_top, c_right, c_bottom = ctrl["rect"]
        # Convert screen coordinates to window-relative coordinates
        rel_l = max(0, min(width - 1, c_left - left))
        rel_t = max(0, min(height - 1, c_top - top))
        rel_r = max(rel_l + 2, min(width, c_right - left))
        rel_b = max(rel_t + 2, min(height, c_bottom - top))

        # Draw bounding box and Set-of-Marks tag [1], [2], ...
        draw.rectangle([rel_l, rel_t, rel_r, rel_b], outline=(255, 40, 40), width=2)
        tag = f"[{idx}]"
        tag_w = max(24, len(tag) * 7 + 4)
        tag_h = 14
        draw.rectangle([rel_l, rel_t, min(width, rel_l + tag_w), min(height, rel_t + tag_h)], fill=(255, 40, 40))
        draw.text((rel_l + 2, rel_t + 1), tag, fill=(255, 255, 255), font=font)

        som_elements.append(
            {
                "mark": idx,
                "tag": tag,
                "name": ctrl.get("name", ""),
                "control_type": ctrl.get("control_type", ""),
                "screen_center": ctrl["center"],
                "window_rel_rect": (rel_l, rel_t, rel_r, rel_b),
            }
        )

    # Resize if wider than max_width (1280px) while keeping aspect ratio
    if img.width > max_width:
        ratio = max_width / float(img.width)
        new_h = max(1, int(img.height * ratio))
        img = img.resize((max_width, new_h), Image.Resampling.BILINEAR)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=jpeg_quality, optimize=True)
    jpeg_bytes = buf.getvalue()
    blackboard.log(
        3,
        f"Captured window SoM JPEG ({len(jpeg_bytes)} bytes, {len(som_elements)} marks) for HWND {target_hwnd}",
    )
    return jpeg_bytes, som_elements, (left, top, right, bottom)
