import cv2
import requests
import numpy as np
import time
from ultralytics import YOLO

# --- KONFIGURACJA ---
ESP_IP = "10.255.136.131"
URL_STREAM = f"http://{ESP_IP}/"
URL_ON = f"http://{ESP_IP}/control?power=on"
URL_OFF = f"http://{ESP_IP}/control?power=off"

# Klasy zwierząt: 16:pies, 17:koń, 18:owca, 19:krowa (dzik), 21:niedźwiedź
TARGET_CLASSES = [16, 17, 18, 19, 21]

print("Inicjalizacja systemu real-time...")
model = YOLO('yolov8n.pt')

# Zmienne sterujące
led_is_on = False
frames_without_animal = 0
OFF_DELAY = 10  # Czekaj ok. 5 sekund (przy 2 FPS) przed wyłączeniem diody

print("Monitorowanie rozpoczęte. Naciśnij 'q', aby przerwać.")

while True:
    try:
        # Pobieranie klatki ze strumienia
        response = requests.get(URL_STREAM, stream=True, timeout=5)
        if response.status_code == 200:
            bytes_data = bytes()
            for chunk in response.iter_content(chunk_size=1024):
                bytes_data += chunk
                a = bytes_data.find(b'\xff\xd8')
                b = bytes_data.find(b'\xff\xd9')
                
                if a != -1 and b != -1:
                    jpg = bytes_data[a:b+2]
                    bytes_data = bytes_data[b+2:] # Czyszczenie bufora
                    frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                    
                    if frame is not None:
                        # 1. Analiza AI
                        results = model.predict(frame, conf=0.3, classes=TARGET_CLASSES, verbose=False)
                        detected_now = len(results[0].boxes) > 0
                        
                        # 2. Logika "Klikania" przycisków
                        if detected_now:
                            frames_without_animal = 0
                            if not led_is_on:
                                print(f"[{time.strftime('%H:%M:%S')}] WYKRYTO: Wysyłam sygnał ON")
                                requests.get(URL_ON, timeout=1)
                                led_is_on = True
                        else:
                            if led_is_on:
                                frames_without_animal += 1
                                if frames_without_animal >= OFF_DELAY:
                                    #print(f"[{time.strftime('%H:%M:%S')}] CZYSTO: Wysyłam sygnał OFF")
                                    requests.get(URL_OFF, timeout=1)
                                    led_is_on = False

                        # 3. Podgląd z ramkami
                        annotated_frame = results[0].plot()
                        cv2.imshow("System Monitorowania", annotated_frame)
                        
                        if cv2.waitKey(1) & 0xFF == ord('q'):
                            break
                    break # Przejdź do kolejnej klatki
    except Exception as e:
        #print(f"Błąd połączenia: {e}")
        time.sleep(1)

cv2.destroyAllWindows()