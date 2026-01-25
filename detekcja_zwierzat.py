import cv2
import requests
import time
from ultralytics import YOLO

# --- KONFIGURACJA ---
ESP_IP = "10.255.136.131" 
# Twój stream jest pod "/", a sterowanie pod "/control"
URL_STREAM = f"http://{ESP_IP}/"
URL_CONTROL_ON = f"http://{ESP_IP}/control?power=on"
URL_CONTROL_OFF = f"http://{ESP_IP}/control?power=off"

# Klasy zwierząt: pies, koń, owca, krowa, niedźwiedź
TARGET_CLASSES = [16, 17, 18, 19, 21]

print("Wczytywanie modelu YOLOv8...")
model = YOLO('yolov8n.pt') 

# Łączenie ze strumieniem MJPEG
print(f"Łączenie ze strumieniem: {URL_STREAM}")
cap = cv2.VideoCapture(URL_STREAM)

if not cap.isOpened():
    print("Błąd: Nie można otworzyć strumienia. Sprawdź czy nikt inny (przeglądarka) nie używa kamery!")
    exit()

last_alarm_time = 0

while True:
    ret, frame = cap.read()
    if not ret:
        print("Utrata klatek... Próbuję ponownie.")
        time.sleep(1)
        continue

    # 1. Analiza AI
    # Twoje ESP wysyła 2 FPS, więc Python ma dużo czasu na analizę
    results = model.predict(frame, conf=0.4, verbose=False)
    
    animal_detected = False
    for r in results:
        for box in r.boxes:
            class_id = int(box.cls[0])
            if class_id in TARGET_CLASSES:
                animal_detected = True
                # Rysowanie ramki
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 3)
                cv2.putText(frame, f"ALARM: {model.names[class_id]}", (x1, y1-10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    # 2. Sygnał zwrotny (Alarm)
    # Wyślij sygnał tylko raz na 3 sekundy, żeby nie zablokować ESP32
    current_time = time.time()
    if animal_detected and (current_time - last_alarm_time > 3):
        print(f"[{time.strftime('%H:%M:%S')}] WYKRYTO ZWIERZĘ! Zapalam LED.")
        try:
            requests.get(URL_CONTROL_ON, timeout=0.5)
            last_alarm_time = current_time
            # Opcjonalnie: po 1 sekundzie zgaś diodę (symulacja sygnału)
            # requests.get(URL_CONTROL_OFF, timeout=0.5) 
        except:
            pass

    # 3. Podgląd na żywo
    #cv2.imshow("Analiza Strumienia ESP32-CAM", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()