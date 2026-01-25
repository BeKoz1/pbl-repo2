import requests
import time

URL = "http://10.255.136.131/capture"

print("Próba pobrania obrazu...")
try:
    start = time.time()
    r = requests.get(URL, timeout=10)
    print(f"Status: {r.status_code}")
    print(f"Odebrano bajtów: {len(r.content)}")
    print(f"Czas odpowiedzi: {time.time() - start:.2f}s")
except Exception as e:
    print(f"Błąd krytyczny: {e}")