import cv2
from ultralytics import YOLO

# 1. Załadowanie modelu
print("Wczytywanie modelu...")
model = YOLO('yolov8n.pt') 

# 2. Wczytanie zdjęcia z dysku
image_path = "pustadroga.jpg"  # Upewnij się, że plik o tej nazwie jest w folderze!
img = cv2.imread(image_path)

if img is None:
    print(f"BŁĄD: Nie znaleziono pliku {image_path}. Sprawdź nazwę i folder.")
else:
    # 3. Wykonanie detekcji
    # conf=0.25 oznacza, że model pokaże wszystko, czego jest pewien w 25%
    results = model.predict(img, conf=0.25)

    # 4. Wyświetlenie wyników
    # model.plot() automatycznie rysuje ramki i napisy na obrazie
    annotated_frame = results[0].plot()

    # Wyświetlenie okna na Windowsie
    cv2.imshow("Test Detekcji AI", annotated_frame)
    
    print("\nWyniki detekcji:")
    for r in results:
        for box in r.boxes:
            class_id = int(box.cls[0])
            label = model.names[class_id]
            prob = box.conf[0]
            print(f"- Wykryto: {label} (Pewność: {prob:.2f})")

    print("\nNaciśnij dowolny klawisz w oknie obrazu, aby zamknąć.")
    cv2.waitKey(0)
    cv2.destroyAllWindows()