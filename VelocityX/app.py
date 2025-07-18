from flask import Flask, render_template, request, jsonify
import cv2
import numpy as np
import os
from werkzeug.utils import secure_filename
from ultralytics import YOLO
from transformers import BlipProcessor, BlipForConditionalGeneration
from tensorflow.keras.models import load_model
from PIL import Image
import pyttsx3
import pytesseract

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg'}

# Initialize models
object_model = YOLO("yolov8n.pt")

# Load currency model and labels
try:
    currency_model = load_model("currency_model.h5")
    label_dict = np.load("label_dict.npy", allow_pickle=True).item()
    
    # Verify model can accept inputs
    test_input = np.random.rand(1, 33856)
    test_pred = currency_model.predict(test_input)
    print(f"Currency model loaded successfully. Test prediction shape: {test_pred.shape}")
except Exception as e:
    print(f"Error loading currency model: {str(e)}")
    currency_model = None
    label_dict = {}

processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
caption_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
tts_engine = pyttsx3.init()
tts_engine.setProperty("rate", 150)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def detect_objects(image):
    results = object_model(image)
    labels = []
    for result in results:
        for box in result.boxes:
            cls_id = int(box.cls[0])
            label = object_model.names[cls_id]
            labels.append(label)
    return list(set(labels))

def detect_currency(image):
    if currency_model is None:
        return ["Currency model not loaded"]

    try:
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Resize to match training input dimensions (184x184)
        resized = cv2.resize(gray, (184, 184))  # 184x184 = 33856

        # Normalize pixel values
        normalized = resized / 255.0

        # Flatten to 1D
        flattened = normalized.flatten().reshape(1, -1)  # Shape: (1, 33856)

        # Predict using model
        predictions = currency_model.predict(flattened)
        predicted_class = np.argmax(predictions[0])
        currency = label_dict.get(predicted_class, "Unknown currency")
        return [currency]
    except Exception as e:
        print(f"Currency detection error: {str(e)}")
        return [f"Detection error: {str(e)}"]

def generate_caption(image):
    pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    inputs = processor(pil_image, return_tensors="pt")
    out = caption_model.generate(**inputs)
    caption = processor.decode(out[0], skip_special_tokens=True)
    return caption

def read_text(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    text = pytesseract.image_to_string(gray)
    return text.strip()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        try:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            image = cv2.imread(filepath)
            if image is None:
                return jsonify({'error': 'Could not read image file'}), 400
            
            mode = request.form.get('mode', 'object')
            
            if mode == 'object':
                objects = detect_objects(image)
                caption = generate_caption(image)
                description = f"{caption}. I see: {', '.join(objects)}." if objects else caption
                return jsonify({'result': description})
            
            elif mode == 'currency':
                currencies = detect_currency(image)
                description = f"I see: {', '.join(currencies)}." if currencies else "No currency detected."
                return jsonify({'result': description})
            
            elif mode == 'text':
                text = read_text(image)
                return jsonify({'result': text if text else "No text detected."})
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'Invalid file'}), 400

@app.route('/speak', methods=['POST'])
def speak_text():
    text = request.json.get('text', '')
    if text:
        tts_engine.say(text)
        tts_engine.runAndWait()
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'No text provided'}), 400

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)