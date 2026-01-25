import cv2
import requests
import numpy as np
from ultralytics import YOLO

# --- KONFIGURACJA ---
URL = "http://10.255.136.131/" 

print("1. Ładowanie modelu YOLOv8...")
model = YOLO('yolov8n.pt')

print(f"2. Pobieranie klatki z {URL}...")

try:
    # Otwieramy połączenie ze strumieniem
    response = requests.get(URL, stream=True, timeout=10)
    
    if response.status_code == 200:
        bytes_data = bytes()
        # Szukamy w strumieniu znaczników początku (FFD8) i końca (FFD9) obrazu JPEG
        for chunk in response.iter_content(chunk_size=1024):
            bytes_data += chunk
            a = bytes_data.find(b'\xff\xd8') # Początek JPEG
            b = bytes_data.find(b'\xff\xd9') # Koniec JPEG
            
            if a != -1 and b != -1:
                jpg = bytes_data[a:b+2]
                # Dekodujemy bajty na obraz OpenCV
                frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                
                if frame is not None:
                    print("3. Klatka odebrana! Analiza AI...")
                    # Uruchamiamy YOLO (tylko detekcja, bez wysyłania alarmu)
                    results = model.predict(frame, conf=0.3)
                    
                    # Rysujemy wyniki na obrazie
                    annotated_frame = results[0].plot()
                    
                    print("4. Gotowe! Wyświetlam wynik.")
                    cv2.imshow("Test AI - Pojedyncza Klatka", annotated_frame)
                    cv2.waitKey(0) # Czekaj na dowolny klawisz
                    cv2.destroyAllWindows()
                    break
    else:
        print(f"Błąd serwera: {response.status_code}")

except Exception as e:
    print(f"Błąd połączenia: {e}")