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
# Ruta para obtener los datos crudos de un story por su ID
@app.route("/get/<story_id>")
def get_story_data(story_id):
    # Realiza una petición GET a Firebase para obtener el story
    url = f"{FIREBASE_URL}/{story_id}.json"
    response = requests.get(url)

    if response.status_code != 200:
        return "Story not found", 404

    # Devuelve los datos crudos del story en formato JSON
    return jsonify(response.json())


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

# Ruta para ver un story por su ID
@app.route("/story/<story_id>")
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

# Ruta para recomendar stories según los intereses del usuario
@app.route("/recommend", methods=["POST"])
def recommend_stories():
    # Obtener los intereses del usuario desde el body
    user_interests = request.get_json(force=True)
    # Obtener el parámetro "recom" desde la URL para saber cuántos stories recomendar
    recom_count = request.args.get("recom", default=5, type=int)  # Default a 5 si no se pasa el parámetro

    # Obtener todos los stories almacenados en Firebase
    response = requests.get(f"{FIREBASE_URL}.json")
    if response.status_code != 200:
        return jsonify({"message": "Error fetching stories from Firebase"}), 500

    all_stories = response.json()  # Todos los stories de Firebase

    # Aquí podrías usar los intereses del usuario para filtrar los stories más adecuados
    # Esto es solo un ejemplo básico: suponer que el score es un indicador de relevancia.
    # Podrías mejorar este filtrado según lo que necesites.
    
    # Ordenar los stories según su puntuación (puedes ajustar esta lógica según el score)
    sorted_stories = sorted(
        all_stories.values(),
        key=lambda story: sum(story.get("score", {}).get(interest, 0) for interest in user_interests),
        reverse=True
    )

    # Obtener los 'recom_count' stories más relevantes
    recommended_stories = sorted_stories[:recom_count]

    # Retornar los IDs de las historias recomendadas
    recommended_ids = [story["id"] for story in recommended_stories]

    return jsonify({"recommended_ids": recommended_ids}), 200

# Inicia el servidor Flask
if __name__ == "__main__":
    app.run(debug=True)
