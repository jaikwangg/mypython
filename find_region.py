"""
Region Selector Tool
====================
ใช้เลือกพื้นที่บนหน้าจอสำหรับ scan_region ใน BotConfig

วิธีใช้:
    python find_region.py

ขั้นตอน:
    1. หน้าต่างจะแสดงภาพหน้าจอเต็มจอ
    2. คลิกและลากเพื่อเลือกพื้นที่ conveyor
    3. กด ENTER เพื่อยืนยัน → จะพิมพ์ค่า scan_region ออกมา
    4. กด R เพื่อเลือกใหม่
    5. กด ESC เพื่อออก

Requirements:
    pip install mss opencv-python numpy
"""

import numpy as np
import sys

try:
    import mss
    import cv2
except ImportError as e:
    print(f"[ERROR] Missing: {e}")
    print("Run: pip install mss opencv-python numpy")
    sys.exit(1)

# ── State ─────────────────────────────────────────────────────────────────────
drawing = False
start_x, start_y = -1, -1
end_x,   end_y   = -1, -1
confirmed        = False

# ── Countdown ให้เวลาสลับไปหน้า Roblox ──────────────────────────────────────
DELAY = 4  # วินาที
print(f"\nสลับไปหน้า Roblox ได้เลย! จะจับภาพใน {DELAY} วินาที...")
for i in range(DELAY, 0, -1):
    print(f"  {i}...", end="\r", flush=True)
    import time; time.sleep(1)
print("📸 จับภาพแล้ว!           ")

# ── Capture full screen ───────────────────────────────────────────────────────
with mss.mss() as sct:
    monitor   = sct.monitors[1]          # จอหลัก
    mon_top   = monitor["top"]
    mon_left  = monitor["left"]
    screenshot = np.array(sct.grab(monitor))

# BGRA → BGR
frame_orig = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR)

# Scale ลงให้จอแสดงผลได้ (max 1280px wide)
MAX_W = 1280
scale = min(1.0, MAX_W / frame_orig.shape[1])
disp_w = int(frame_orig.shape[1] * scale)
disp_h = int(frame_orig.shape[0] * scale)
frame_disp = cv2.resize(frame_orig, (disp_w, disp_h))
frame_base = frame_disp.copy()   # ต้นฉบับสำหรับ redraw

# ── Mouse callback ────────────────────────────────────────────────────────────
def on_mouse(event, x, y, flags, param):
    global drawing, start_x, start_y, end_x, end_y, confirmed

    if event == cv2.EVENT_LBUTTONDOWN:
        drawing   = True
        confirmed = False
        start_x, start_y = x, y
        end_x,   end_y   = x, y

    elif event == cv2.EVENT_MOUSEMOVE and drawing:
        end_x, end_y = x, y

    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        end_x, end_y = x, y

# ── Helper: ปรับพิกัด display → พิกัด monitor จริง ──────────────────────────
def to_real(x, y):
    rx = int(x / scale) + mon_left
    ry = int(y / scale) + mon_top
    return rx, ry

def region_dict():
    x1, y1 = min(start_x, end_x), min(start_y, end_y)
    x2, y2 = max(start_x, end_x), max(start_y, end_y)
    rx1, ry1 = to_real(x1, y1)
    rx2, ry2 = to_real(x2, y2)
    return {
        "top":    ry1,
        "left":   rx1,
        "width":  rx2 - rx1,
        "height": ry2 - ry1,
    }

# ── Window setup ──────────────────────────────────────────────────────────────
WIN = "Region Selector  |  ลาก=เลือก  ENTER=ยืนยัน  R=ใหม่  ESC=ออก"
cv2.namedWindow(WIN, cv2.WINDOW_NORMAL)
cv2.resizeWindow(WIN, disp_w, disp_h)
cv2.setMouseCallback(WIN, on_mouse)

print("\nหน้าต่างเปิดแล้ว — ลากเลือกพื้นที่ conveyor แล้วกด ENTER")

# ── Main loop ─────────────────────────────────────────────────────────────────
while True:
    canvas = frame_base.copy()

    # วาด rectangle ขณะลาก
    if start_x != -1 and end_x != -1:
        x1 = min(start_x, end_x)
        y1 = min(start_y, end_y)
        x2 = max(start_x, end_x)
        y2 = max(start_y, end_y)

        color = (0, 255, 100) if confirmed else (0, 200, 255)

        # overlay โปร่งแสง
        overlay = canvas.copy()
        cv2.rectangle(overlay, (x1, y1), (x2, y2), color, -1)
        cv2.addWeighted(overlay, 0.25, canvas, 0.75, 0, canvas)

        # กรอบ
        cv2.rectangle(canvas, (x1, y1), (x2, y2), color, 2)

        # ขนาด (pixel จริง)
        r = region_dict()
        label = f"  {r['width']} x {r['height']} px  (top={r['top']}, left={r['left']})"
        cv2.putText(canvas, label, (x1, max(y1 - 8, 16)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 1, cv2.LINE_AA)

    # คำแนะนำ overlay
    hint = "ENTER=ยืนยัน   R=เลือกใหม่   ESC=ออก"
    cv2.putText(canvas, hint, (10, disp_h - 12),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1, cv2.LINE_AA)

    cv2.imshow(WIN, canvas)
    key = cv2.waitKey(16) & 0xFF

    if key == 27:            # ESC
        print("ออกจากโปรแกรม")
        break

    elif key == 13 or key == 10:   # ENTER
        if start_x != -1 and abs(end_x - start_x) > 5 and abs(end_y - start_y) > 5:
            confirmed = True
            r = region_dict()
            print("\n" + "="*55)
            print("✅ scan_region ที่เลือก:")
            print(f"   top    = {r['top']}")
            print(f"   left   = {r['left']}")
            print(f"   width  = {r['width']}")
            print(f"   height = {r['height']}")
            print("="*55)
            print("\nคัดลอกไปใส่ใน BotConfig:")
            print(f'   scan_region={{"top":{r["top"]},"left":{r["left"]},"width":{r["width"]},"height":{r["height"]}}},')
            print("="*55)
        else:
            print("[!] ลากให้ใหญ่กว่านี้ก่อนกด ENTER")

    elif key == ord('r') or key == ord('R'):
        start_x = start_y = end_x = end_y = -1
        confirmed = False
        print("เลือกใหม่ — ลากพื้นที่อีกครั้ง")

cv2.destroyAllWindows()