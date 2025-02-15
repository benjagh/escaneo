!apt-get install tesseract-ocr
!pip install opencv-python matplotlib pytesseract
!pip install flask flask-cors

from flask import Flask, request, jsonify
from flask_cors import CORS
import cv2
import pytesseract
import numpy as np
import re

app = Flask(__name__)
CORS(app)

@app.route("/ocr", methods=["POST"])
def ocr_endpoint():
    if 'image' not in request.files:
        return jsonify({"error": "No se proporcionó una imagen."}), 400

    file = request.files['image']
    file_bytes = np.frombuffer(file.read(), np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

    if img is None:
        return jsonify({"error": "No se pudo leer la imagen."}), 400

    # Procesamiento de la imagen completa
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    # Realizar OCR en la imagen procesada
    extracted_text = pytesseract.image_to_string(thresh, config='--psm 6')

    # Buscar el número de guía en el texto extraído
    guide_match = re.search(r'N\D*(\d+)', extracted_text, re.IGNORECASE)
    if guide_match:
        numero_guia = guide_match.group(1).lstrip('0')
    else:
        numero_guia = None

    # Buscar el RUT en el texto extraído, tomando solo el número que sigue a "R.U.T"
    rut_match = re.search(r'(?:R\.?\s*U\.?\s*T\.?\s*:?\s*)?(\d{1,2}(?:\.\d{3}){2}-[\dkK])', extracted_text)
    if rut_match:
        rut = rut_match.group(1)  # Se elimina la limpieza de puntos
    else:
        rut = None

    # Retornar los resultados
    return jsonify({
        "numero_guia": numero_guia,
        "rut": rut
    }), 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
