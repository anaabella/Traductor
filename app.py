from flask import Flask, render_template, request, send_file, jsonify
from ebooklib import epub
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
import threading
import time
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['TRANSLATED_FOLDER'] = 'translated'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['TRANSLATED_FOLDER'], exist_ok=True)

# Variable global para simular progreso
progress = 0

def clean_text(text):
    return (
        text
        .replace('"', '—')
        .replace("'", '—')
        .replace('“', '—')
        .replace('”', '—')
        .replace('”.', '—')
        .replace('‘', '—')
        .replace('’', '—')
        .replace('’.', '—')
    )

def traducir_epub(ruta_entrada, ruta_salida):
    global progress
    progress = 0

    libro = epub.read_epub(ruta_entrada)
    traductor = GoogleTranslator(source='auto', target='es')

    items = [item for item in libro.get_items() if item.get_type() == epub.EpubHtml]
    total_items = len(items)
    for idx, item in enumerate(items):
        soup = BeautifulSoup(item.get_body_content(), 'html.parser')
        for tag in soup.find_all(text=True):
            if tag.strip():
                texto_original = tag.string
                try:
                    texto_traducido = traductor.translate(texto_original)
                    texto_traducido = clean_text(texto_traducido)
                    tag.string.replace_with(texto_traducido)
                except Exception as e:
                    print(f"Error traduciendo: {texto_original} -> {e}")
        item.set_content(str(soup).encode('utf-8'))

        # Actualizar progreso
        progress = int((idx + 1) / total_items * 100)
        time.sleep(0.1)  # Simula tiempo de traducción

    epub.write_epub(ruta_salida, libro)
    progress = 100

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    global progress
    file = request.files.get('epub_file')
    if not file or not file.filename.endswith('.epub'):
        return jsonify({'error': 'Por favor sube un archivo EPUB válido.'}), 400

    filename = file.filename
    ruta_entrada = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    ruta_salida = os.path.join(app.config['TRANSLATED_FOLDER'], filename.replace('.epub', '_traducido.epub'))
    file.save(ruta_entrada)

    # Traducción en un hilo separado para no bloquear la app
    thread = threading.Thread(target=traducir_epub, args=(ruta_entrada, ruta_salida))
    thread.start()

    return jsonify({'message': 'Archivo recibido. Traducción en proceso.', 'output_file': ruta_salida})

@app.route('/progress')
def get_progress():
    return jsonify({'progress': progress})

@app.route('/download')
def download():
    output_file = request.args.get('file')
    if output_file and os.path.exists(output_file):
        return send_file(output_file, as_attachment=True)
    return "Archivo no encontrado", 404

if __name__ == '__main__':
    app.run(debug=True)
