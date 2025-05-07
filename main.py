import pygetwindow as gw
import easyocr
from PIL import Image
import mss
import numpy as np
import time
import requests

reader = easyocr.Reader(['en'], gpu=True)
ultimo_texto = ""

# URL a la que hacer la petición GET
URL = "https://pokeapi.co/api/v2/pokemon/"  # ← cambia esto
avisado = False

with mss.mss() as sct:
    while True:
        windows = gw.getWindowsWithTitle("Pokemon Iberia")
        if not windows:
            print("Ventana no encontrada.")
            time.sleep(1)
            continue

        window = windows[0]

        if window.isMinimized or not window.isActive:
            if not avisado:
                print("Ventana no encontrada.")
                avisado = True
            time.sleep(1)
            continue
        else:
            avisado = False

        x, y = window.left, window.top

        region_inside_window = {
            "top": y + 260,
            "left": x + 150,
            "width": 260,
            "height": 60
        }

        screenshot = sct.grab(region_inside_window)
        img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
        img_np = np.array(img)

        results = reader.readtext(img_np)

        textos_detectados = [text for _, text, conf in results if conf > 0.5]
        texto_completo = " ".join(textos_detectados).strip()

        # Si hay texto y es distinto al anterior, hacemos la petición
        if texto_completo and texto_completo != ultimo_texto:
            print(f"Texto nuevo detectado: {texto_completo}")
            payload = {"nombre": texto_completo}

            try:
                response = requests.post("http://localhost:5000/update", json=payload)
                print(f"Petición POST enviada. Estado: {response.status_code}")
            except Exception as e:
                print(f"Error al enviar al servidor: {e}")

            ultimo_texto = texto_completo

        time.sleep(1)
