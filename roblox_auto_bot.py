"""
Popup Bot — ตรวจจับ popup "Reserve/Buy" แล้วกด E
=================================================
Logic:
  1. สแกนกลางจอทุก 0.1s หา popup box สีดำ
  2. ถ้าเจอ → OCR อ่านชื่อ item จาก popup
  3. ถ้าชื่อตรงกับ buy_list → กด E
  4. ถ้า buy_list ว่าง → กด E ทุก item

ไม่ต้อง delay, ไม่ต้อง calibrate, ใช้ได้ทันที

Requirements:
    pip install mss pillow pytesseract pyautogui keyboard numpy opencv-python
    + ติดตั้ง Tesseract: https://github.com/UB-Mannheim/tesseract/wiki
"""

import time, threading, logging, sys
from dataclasses import dataclass, field
from typing import Optional

try:
    import mss
    import cv2
    import numpy as np
    from PIL import Image
    import pytesseract
    import pyautogui
    import keyboard
except ImportError as e:
    print(f"[ERROR] {e}\nRun: pip install mss pillow pytesseract pyautogui keyboard numpy opencv-python")
    sys.exit(1)

# Windows: uncomment ถ้า tesseract ไม่อยู่ใน PATH
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s",
                    datefmt="%H:%M:%S")
log = logging.getLogger("PopupBot")


# ─────────────────────────────────────────────────────────────────────────────
# CONFIG — แก้ตรงนี้
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class Config:
    # ชื่อ item ที่ต้องการ buy (case-insensitive)
    # ว่าง [] = buy ทุก item ที่ popup ขึ้น
    buy_list: list[str] = field(default_factory=lambda: [
        "Gold", "Copper", "Fishbone"
    ])

    # ── Popup detection ───────────────────────────────────────────────────────
    # region กลางจอที่ popup โผล่ — None = คำนวณอัตโนมัติจากขนาดจอ
    popup_region: Optional[dict] = None

    # popup ต้องมี pixel สีเข้ม (dark bg) มากกว่า % นี้
    dark_threshold: int = 55       # pixel ที่ถือว่า "dark" (0-255)
    dark_ratio_min: float = 0.20   # ต้องมี dark pixel อย่างน้อย 20%

    # ── OCR ──────────────────────────────────────────────────────────────────
    # region สำหรับ OCR — ขยายจาก popup_region ขึ้นไปด้านบนเพื่อจับชื่อ item
    # None = ใช้ popup_region เดิม
    ocr_region: Optional[dict] = None
    ocr_scale: float = 2.5
    tesseract_config: str = "--psm 7 --oem 3"   # psm 7 = single line

    # ── Timing ────────────────────────────────────────────────────────────────
    scan_interval_sec: float = 0.1
    press_duration_sec: float = 0.15
    cooldown_sec: float = 1.5      # หลังกด E รอก่อนสแกนใหม่

    # ── Keys ─────────────────────────────────────────────────────────────────
    action_key: str = "e"
    toggle_key: str = "F8"
    quit_key: str = "F9"
    debug_key: str = "F7"          # บันทึกภาพปัจจุบันเพื่อ debug


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def get_monitor():
    with mss.mss() as sct:
        return sct.monitors[1]

def grab(region: dict) -> np.ndarray:
    with mss.mss() as sct:
        r = (region["left"], region["top"], region["width"], region["height"])
        return cv2.cvtColor(np.array(sct.grab(r)), cv2.COLOR_BGRA2BGR)

def make_popup_region(mon: dict) -> dict:
    """คำนวณ region กลางจอที่ popup น่าจะอยู่"""
    w, h = mon["width"], mon["height"]
    rw, rh = int(w * 0.28), int(h * 0.15)
    return {
        "left": mon["left"] + w // 2 - rw // 2,
        "top":  mon["top"]  + h // 2 - rh // 2,
        "width": rw,
        "height": rh,
    }

def make_ocr_region(popup: dict) -> dict:
    """ขยาย region ขึ้นไปด้านบนเพื่อจับชื่อ item เหนือ popup"""
    extra = int(popup["height"] * 1.5)
    return {
        "left":   popup["left"],
        "top":    popup["top"] - extra,
        "width":  popup["width"],
        "height": extra,
    }

def is_popup_visible(img: np.ndarray, threshold: int, min_ratio: float) -> bool:
    """ตรวจว่ามี popup box สีเข้มใน region หรือไม่"""
    dark = np.all(img < threshold, axis=2)
    return (dark.sum() / dark.size) > min_ratio

def ocr_read(region: dict, scale: float, tess_cfg: str) -> str:
    img = grab(region)
    h, w = img.shape[:2]
    resized = cv2.resize(img, (int(w * scale), int(h * scale)),
                         interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    text = pytesseract.image_to_string(Image.fromarray(thresh), config=tess_cfg)
    return text.strip().upper()

def match(text: str, buy_list: list[str]) -> Optional[str]:
    if not buy_list:
        return "ANY"
    for item in buy_list:
        if item.upper() in text:
            return item
    return None


# ─────────────────────────────────────────────────────────────────────────────
# BOT
# ─────────────────────────────────────────────────────────────────────────────
class PopupBot:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self._running = False
        self._enabled = False
        self._presses = 0

        mon = get_monitor()
        if not cfg.popup_region:
            cfg.popup_region = make_popup_region(mon)
        if not cfg.ocr_region:
            cfg.ocr_region = make_ocr_region(cfg.popup_region)

    def _scan_loop(self):
        while self._running:
            if not self._enabled:
                time.sleep(0.2)
                continue
            try:
                self._tick()
            except Exception as e:
                log.error(f"Error: {e}")
                time.sleep(0.5)

    def _tick(self):
        assert self.cfg.popup_region is not None
        assert self.cfg.ocr_region is not None

        # Step 1: ตรวจ popup box สีดำก่อน (เร็ว ไม่ต้อง OCR)
        popup_img = grab(self.cfg.popup_region)
        if not is_popup_visible(popup_img,
                                self.cfg.dark_threshold,
                                self.cfg.dark_ratio_min):
            time.sleep(self.cfg.scan_interval_sec)
            return

        # Step 2: popup เจอแล้ว — ถ้า buy_list ว่างกด E เลย
        if not self.cfg.buy_list:
            log.info("🎯 Popup detected → กด E (buy all mode)")
            self._press_e()
            return

        # Step 3: OCR อ่านชื่อ item จาก region เหนือ popup
        text = ocr_read(self.cfg.ocr_region,
                        self.cfg.ocr_scale,
                        self.cfg.tesseract_config)
        log.info(f"OCR: {repr(text[:50])}")

        found = match(text, self.cfg.buy_list)
        if found:
            log.info(f"✅ [{found}] อยู่ใน buy_list → กด E")
            self._press_e()
        else:
            log.info("⏭  ไม่ใช่ item ที่ต้องการ — ข้าม")
            time.sleep(self.cfg.scan_interval_sec)

    def _press_e(self):
        pyautogui.keyDown(self.cfg.action_key)
        time.sleep(self.cfg.press_duration_sec)
        pyautogui.keyUp(self.cfg.action_key)
        self._presses += 1
        log.info(f"⌨️  Pressed [E]  (#{self._presses})")
        time.sleep(self.cfg.cooldown_sec)

    def _save_debug(self):
        """F7: บันทึกภาพ popup_region และ ocr_region เพื่อ debug"""
        assert self.cfg.popup_region is not None
        assert self.cfg.ocr_region is not None
        cv2.imwrite("debug_popup.png", grab(self.cfg.popup_region))
        cv2.imwrite("debug_ocr.png",   grab(self.cfg.ocr_region))
        log.info("💾 บันทึก debug_popup.png และ debug_ocr.png แล้ว")
        log.info(f"   popup_region = {self.cfg.popup_region}")
        log.info(f"   ocr_region   = {self.cfg.ocr_region}")

    def start(self):
        log.info("=" * 55)
        log.info("  Popup Bot")
        log.info(f"  Buy list     : {self.cfg.buy_list or ['ทุก item']}")
        log.info(f"  Popup region : {self.cfg.popup_region}")
        log.info(f"  OCR region   : {self.cfg.ocr_region}")
        log.info(f"  {self.cfg.debug_key}=debug  {self.cfg.toggle_key}=เปิด/ปิด  {self.cfg.quit_key}=ออก")
        log.info("=" * 55)

        self._running = True
        keyboard.add_hotkey(self.cfg.debug_key,  lambda: self._save_debug())
        keyboard.add_hotkey(self.cfg.toggle_key, self._on_toggle)
        keyboard.add_hotkey(self.cfg.quit_key,   self._on_quit)

        threading.Thread(target=self._scan_loop, daemon=True).start()
        log.info(f"กด [{self.cfg.toggle_key}] เพื่อเปิด bot")

        try:
            while self._running:
                time.sleep(0.5)
        except KeyboardInterrupt:
            pass

        keyboard.unhook_all()
        log.info(f"จบ — กด E ทั้งหมด {self._presses} ครั้ง")

    def _on_toggle(self):
        self._enabled = not self._enabled
        log.info("▶ ENABLED" if self._enabled else "⏸ PAUSED")

    def _on_quit(self):
        self._running = False


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    cfg = Config(
        # ใส่ชื่อ item ที่อยากซื้อ (ตามที่ขึ้นบน popup)
        # ว่าง [] = ซื้อทุกอย่าง
        buy_list=["Gold", "Copper", "Fishbone"],
    )
    PopupBot(cfg).start()