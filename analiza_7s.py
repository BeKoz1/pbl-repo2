import cv2
import requests
import numpy as np
import time
from ultralytics import YOLO

# --- KONFIGURACJA ---
ESP_IP = "192.168.68.52"
URL_STREAM = f"http://{ESP_IP}/"
URL_ON = f"http://{ESP_IP}/control?power=on"
URL_OFF = f"http://{ESP_IP}/control?power=off"

TARGET_CLASSES = [16, 17, 18, 19, 21]

print("Inicjalizacja systemu (ESP32-S3)...")
model = YOLO('yolov8n.pt')
session = requests.Session()

# --- ZMIENNE STERUJĄCE ---
led_is_on = False
last_animal_seen_time = 0  # Tu będziemy zapisywać czas ostatniego wykrycia
OFF_DELAY_SECONDS = 7      # Twoje 7 sekund
RETRY_INTERVAL = 2         # Sygnał ON co 2 sekundy dla pewności
last_signal_time = 0

print(f"Monitorowanie rozpoczęte. Wyłączanie po {OFF_DELAY_SECONDS}s bez zwierząt.")

while True:
    try:
        # Otwieramy strumień (bez break, aby działał płynnie)
        response = session.get(URL_STREAM, stream=True, timeout=5)
        if response.status_code == 200:
            bytes_data = bytes()
            for chunk in response.iter_content(chunk_size=1024):
                bytes_data += chunk
                a = bytes_data.find(b'\xff\xd8')
                b = bytes_data.find(b'\xff\xd9')
                
                if a != -1 and b != -1:
                    jpg = bytes_data[a:b+2]
                    bytes_data = bytes_data[b+2:]
                    
                    if not jpg or len(jpg) < 100:
                        continue
                        
                    try:
                        frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                        if frame is not None:
                            # 1. Analiza AI
                            results = model.predict(frame, conf=0.3, classes=TARGET_CLASSES, verbose=False)
                            detected_now = len(results[0].boxes) > 0
                            current_time = time.time()
                            
                            if detected_now:
                                # Odświeżamy czas, w którym zwierzę było widoczne ostatni raz
                                last_animal_seen_time = current_time
                                
                                # Logika włączania (ON)
                                if not led_is_on or (current_time - last_signal_time > RETRY_INTERVAL):
                                    try:
                                        session.get(URL_ON, timeout=0.2)
                                        if not led_is_on:
                                            print(f"[{time.strftime('%H:%M:%S')}] WYKRYTO: Sygnał ON")
                                        led_is_on = True
                                        last_signal_time = current_time
                                    except:
                                        led_is_on = True 
                            else:
                                # Logika wyłączania (OFF) oparta na czasie
                                if led_is_on:
                                    # Sprawdzamy, czy od ostatniego razu gdy widzieliśmy zwierzę minęło 7 sekund
                                    time_since_last_seen = current_time - last_animal_seen_time
                                    
                                    if time_since_last_seen >= OFF_DELAY_SECONDS:
                                        try:
                                            print(f"[{time.strftime('%H:%M:%S')}] CZYSTO PRZEZ {OFF_DELAY_SECONDS}s: Sygnał OFF")
                                            session.get(URL_OFF, timeout=0.2)
                                            led_is_on = False
                                        except:
                                            led_is_on = False

                            # 3. Podgląd
                            annotated_frame = results[0].plot()
                            cv2.imshow("Monitor Dzikow", annotated_frame)
                            
                    except Exception:
                        continue
                        
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        cv2.destroyAllWindows()
                        exit()
                            
    except Exception as e:
        print(f"Błąd: {e}")
        time.sleep(2)