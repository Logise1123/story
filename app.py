from flask import Flask, request, jsonify
from flask_cors import CORS
from pyngrok import ngrok
import random
import string
import json
import os

app = Flask(__name__)
CORS(app)

STORY_FILE = "stories.txt"
stories = {}

# --- Función para generar IDs de 6 caracteres alfanuméricos ---
def generate_id():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=6))

# --- Cargar stories desde archivo al iniciar ---
def load_stories():
    global stories
    if os.path.exists(STORY_FILE):
        with open(STORY_FILE, "r", encoding="utf-8") as f:
            try:
                stories = json.load(f)
            except json.JSONDecodeError:
                stories = {}

# --- Guardar stories en archivo ---
def save_stories():
    with open(STORY_FILE, "w", encoding="utf-8") as f:
        json.dump(stories, f, indent=2)

# --- Publicar un nuevo story ---
@app.route("/publish", methods=["POST"])
def publish_story():
    data = request.get_json(force=True)
    story_id = generate_id()

    story = {
        "id": story_id,
        "text": data.get("text"),
        "bg_color": data.get("bg_color", "#000000"),
        "creator": data.get("creator", "anon"),
        "score": data.get("score", {})
    }

    stories[story_id] = story
    save_stories()

    return jsonify({"message": "Story published", "id": story_id})

# --- Obtener un story por ID ---
@app.route("/get/<story_id>", methods=["GET"])
def get_story(story_id):
    story = stories.get(story_id)
    if story:
        return jsonify(story)
    return jsonify({"error": "Story not found"}), 404

# --- Recomendar stories ---
@app.route("/recommend", methods=["POST"])
def recommend():
    user_interests = request.json.get("interests", {})

    def relevance(story):
        score = story["score"]
        return sum(user_interests.get(k, 0) * score.get(k, 0) for k in user_interests)

    sorted_stories = sorted(stories.values(), key=relevance, reverse=True)
    top_ids = [s["id"] for s in sorted_stories[:25]]
    return jsonify({"top_ids": top_ids})
from flask import render_template_string

@app.route("/story/<story_id>")
def view_story(story_id):
    story = stories.get(story_id)
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

# --- Iniciar ngrok y servidor ---
if __name__ == "__main__":
    load_stories()
    public_url = ngrok.connect(5000)
    print(f" * ngrok URL: {public_url}")
    app.run()
