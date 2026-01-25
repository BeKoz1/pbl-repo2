import cv2
import requests
import numpy as np
from ultralytics import YOLO

# --- KONFIGURACJA ---
ESP_IP = "10.255.136.131"
URL_STREAM = f"http://{ESP_IP}/"

# Klasy zwierząt w modelu YOLOv8 (COCO):
# 16:pies, 17:koń, 18:owca, 19:krowa (często wykrywa tak dziki), 21:niedźwiedź
TARGET_CLASSES = [16, 17, 18, 19, 21]

print("1. Ładowanie modelu AI...")
model = YOLO('yolov8n.pt')

print(f"2. Próba pobrania obrazu z {URL_STREAM}...")

try:
    # Pobieramy klatkę ze strumienia
    response = requests.get(URL_STREAM, stream=True, timeout=10)
    if response.status_code == 200:
        bytes_data = bytes()
        for chunk in response.iter_content(chunk_size=1024):
            bytes_data += chunk
            a = bytes_data.find(b'\xff\xd8') # Start JPEG
            b = bytes_data.find(b'\xff\xd9') # Koniec JPEG
            
            if a != -1 and b != -1:
                jpg = bytes_data[a:b+2]
                frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                
                if frame is not None:
                    print("3. Klatka odebrana! Szukam zwierząt...")
                    
                    # Analiza AI - filtrujemy wyniki tylko dla wybranych klas zwierząt
                    results = model.predict(frame, conf=0.3, classes=TARGET_CLASSES, verbose=True)
                    
                    # Rysowanie wyników
                    annotated_frame = results[0].plot()
                    
                    # Sprawdzenie czy cokolwiek wykryto
                    if len(results[0].boxes) > 0:
                        print(f"SUKCES: Wykryto zwierzę!")
                    else:
                        print("INFO: Na tej klatce nie znaleziono żadnego ze wskazanych zwierząt.")
                    
                    print("4. Wyświetlanie wyniku. Naciśnij dowolny klawisz, aby zamknąć okno.")
                    cv2.imshow("Detekcja Zwierzecia - Jedna Klatka", annotated_frame)
                    cv2.waitKey(0)
                    cv2.destroyAllWindows()
                    break
    else:
        print(f"Błąd serwera: {response.status_code}")

except Exception as e:
    print(f"Błąd: {e}")