import requests
import random
import string
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import json

app = Flask(__name__)
CORS(app)

# URL de Firebase Realtime Database
FIREBASE_URL = "https://weberia-8dfa7-default-rtdb.europe-west1.firebasedatabase.app/story"

# Función para generar un ID único alfanumérico de 6 caracteres
def generate_id():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=6))

# Función para guardar el story en Firebase
def save_story_to_firebase(story_id, story_data):
    url = f"{FIREBASE_URL}/{story_id}.json"
    response = requests.put(url, json=story_data)  # Usa PUT para guardar o actualizar el story
    return response.status_code

# Ruta para publicar un nuevo story
@app.route("/publish", methods=["POST"])
def publish_story():
    data = request.get_json(force=True)  # Obtiene los datos JSON del request
    story_id = generate_id()  # Genera un ID único para el story

    # Crea un objeto de story
    story = {
        "id": story_id,
        "text": data.get("text"),
        "bg_color": data.get("bg_color", "#000000"),  # Fondo por defecto negro
        "creator": data.get("creator", "anon"),  # Creador por defecto "anon"
        "score": data.get("score", {})  # Puntuación vacía si no se proporciona
    }

    # Guarda el story en Firebase
    status_code = save_story_to_firebase(story_id, story)

    if status_code == 200:
        return jsonify({"message": "Story published", "id": story_id}), 200
    else:
        return jsonify({"message": "Error saving story to Firebase"}), 500

# Ruta para obtener todos los stories
@app.route("/get", methods=["GET"])
def get_stories():
    response = requests.get(FIREBASE_URL + ".json")  # Obtener todos los datos de Firebase
    if response.status_code == 200:
        return jsonify(response.json()), 200
    else:
        return jsonify({"message": "Error fetching stories from Firebase"}), 500

# Ruta para ver un story por su ID
@app.route("/story/<story_id>", methods=["GET"])
def view_story(story_id):
    # Realiza una petición GET a Firebase para obtener el story
    url = f"{FIREBASE_URL}/{story_id}.json"
    response = requests.get(url)

    if response.status_code != 200:
        return "Story not found", 404

    story = response.json()  # Extrae el contenido JSON del story

    # HTML para mostrar el story
    html_template = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{{ story_id }}</title>
        <link href="https://fonts.googleapis.com/css2?family=Quicksand:wght@600&display=swap" rel="stylesheet">
        <style>
            body {
                margin: 0;
                height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                background-color: {{ bg_color }};
                font-family: 'Quicksand', sans-serif;
                color: white;
                font-size: 2em;
                text-align: center;
                padding: 1em;
            }

            h1 {
                font-size: 3em;
            }

            p {
                font-size: 1.5em;
            }

            .creator-info {
                margin-top: 20px;
                font-size: 1em;
                font-weight: bold;
            }

            .score {
                margin-top: 10px;
                font-size: 1.2em;
            }
        </style>
    </head>
    <body>
        <div>
            <h1>{{ text }}</h1>
            <p class="creator-info">Creador: {{ creator }}</p>
            <p class="score">Puntuación: {{ score }}</p>
        </div>
    </body>
    </html>
    """

    return render_template_string(
        html_template,
        story_id=story_id,
        bg_color=story["bg_color"],
        text=story["text"],
        creator=story["creator"],
        score=json.dumps(story["score"])  # Convirtiendo la puntuación a un formato adecuado
    )

# Ruta raíz para confirmar que el servidor está funcionando
@app.route("/", methods=["GET"])
def index():
    return "Bienvenido al sistema de Stories. Usa /publish para publicar un nuevo story y /story/<id> para ver un story."

# Inicia el servidor Flask
if __name__ == "__main__":
    app.run(debug=True)
