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

# Lista global para almacenar los stories
stories_list = []

# Función para generar un ID único alfanumérico de 6 caracteres
def generate_id():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=6))

# Función para guardar el story en Firebase
def save_story_to_firebase(story_id, story_data):
    url = f"{FIREBASE_URL}/{story_id}.json"
    response = requests.put(url, json=story_data)  # Usa PUT para guardar o actualizar el story
    return response.status_code

# Función para cargar todos los stories desde Firebase al iniciar la aplicación
def load_stories_from_firebase():
    global stories_list
    response = requests.get(f"{FIREBASE_URL}.json")
    if response.status_code == 200:
        data = response.json()
        # Convertimos el diccionario en una lista de stories
        stories_list = list(data.values()) if data else []
    else:
        stories_list = []

# Cargar los stories antes de la primera petición
@app.before_first_request
def initialize():
    load_stories_from_firebase()

@app.route('/')
def home():
    return """
        <html>
            <head><title>Story App</title></head>
            <body style="font-family: Quicksand, sans-serif;">
                <h1>Bienvenido a la Story App</h1>
                <p>Accede a los datos en formato crudo <a href="/get">aquí</a>.</p>
                <p><a href="/story/lx63">Ver Story</a></p>
            </body>
        </html>
    """

# Ruta para obtener los datos crudos de un story por su ID desde la lista
@app.route("/get/<story_id>")
def get_story_data(story_id):
    story = next((s for s in stories_list if s.get("id") == story_id), None)
    if not story:
        return "Story not found", 404
    return jsonify(story)

# Ruta para publicar un nuevo story
@app.route("/publish", methods=["POST"])
def publish_story():
    data = request.get_json(force=True)
    story_id = generate_id()

    # Se crea el objeto del story incluyendo el nuevo campo sound_url
    story = {
        "id": story_id,
        "text": data.get("text"),
        "bg_color": data.get("bg_color", "#000000"),
        "creator": data.get("creator", "anon"),
        "score": data.get("score", {}),
        "sound_url": data.get("sound_url")  # Nuevo campo sound_url
    }

    status_code = save_story_to_firebase(story_id, story)

    if status_code == 200:
        # Agregar el story a la lista en memoria
        stories_list.append(story)
        return jsonify({"message": "Story published", "id": story_id}), 200
    else:
        return jsonify({"message": "Error saving story to Firebase"}), 500

# Ruta para ver un story por su ID desde la lista
@app.route("/story/<story_id>")
def view_story(story_id):
    story = next((s for s in stories_list if s.get("id") == story_id), None)
    if not story:
        return "Story not found", 404

    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
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
        </style>
    </head>
    <body>
        <div>{{ text }}</div>
    </body>
    </html>
    """

    return render_template_string(
        html_template,
        story_id=story_id,
        bg_color=story["bg_color"],
        text=story["text"]
    )

# Ruta para recomendar stories según los intereses del usuario usando la lista en memoria
@app.route("/recommend", methods=["POST"])
def recommend_stories():
    request_data = request.get_json(force=True)
    user_interests = request_data.get("interests", {})
    viewed_ids = request_data.get("viewed_ids", [])
    recom_count = request.args.get("recom", default=5, type=int)

    # Filtrar stories que no han sido vistas
    filtered_stories = [
        story for story in stories_list if story.get("id") not in viewed_ids
    ]

    def calculate_relevance(story_score):
        relevance = 0
        for key, value in user_interests.items():
            relevance += value * story_score.get(key, 0)
        return relevance

    sorted_stories = sorted(
        filtered_stories,
        key=lambda story: calculate_relevance(story.get("score", {})),
        reverse=True
    )

    recommended_stories = sorted_stories[:recom_count]
    recommended_ids = [story.get("id") for story in recommended_stories]

    return jsonify({"recommended_ids": recommended_ids}), 200

if __name__ == "__main__":
    app.run(debug=True)
