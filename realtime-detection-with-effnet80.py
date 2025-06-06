import cv2
import tensorflow as tf
import numpy as np

# โหลดโมเดล
model = tf.keras.models.load_model("cifar10_efficient.keras")
class_names = ['airplane','automobile','bird','cat','deer','dog','frog','horse','ship','truck']  # ปรับตาม dataset

# เปิดกล้อง
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Cannot open camera")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        print("Can't receive frame. Exiting ...")
        break

    # เตรียมภาพ: resize, normalize
    input_img = cv2.resize(frame, (32, 32))  # ขนาดของ cifar10
    input_img = input_img / 255.0
    input_img = np.expand_dims(input_img, axis=0)

    # พยากรณ์
    predictions = model.predict(input_img)
    class_idx = np.argmax(predictions)
    confidence = np.max(predictions)
    label = f"{class_names[class_idx]} ({confidence*100:.2f}%)"

    # วาดกรอบและ label
    h, w, _ = frame.shape
    cv2.rectangle(frame, (10, 10), (w - 10, h - 10), (0, 255, 0), 2)
    cv2.putText(frame, label, (15, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    # แสดงภาพ
    cv2.imshow('Realtime Detection', frame)

    if cv2.waitKey(1) == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
