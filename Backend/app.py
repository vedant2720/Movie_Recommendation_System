from flask import Flask, request, jsonify, send_from_directory
import sqlite3
import pandas as pd
from config import occupation_map
import os
import pickle
from helpers import build_user_vector

app = Flask(__name__)

# --- Paths Configuration ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "recommender_system.db")

# --- Load Model ---
MODEL_PATH = os.path.join(BASE_DIR, "model", "cmfrec_model.pkl")
with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)
    U = pickle.load(f)  # User features table
    I = pickle.load(f)  # Item features table

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_poster_url(path_from_db):
    if path_from_db and str(path_from_db).lower() != 'none':
        filename = os.path.basename(path_from_db)
        return f"posters/{filename}"

# --- Routes ---

@app.route("/signup", methods=["POST"])
def signup():
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO users (username, email, password, gender, age, occupation)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (data['username'], data['email'], data['password'], data['gender'], data['age'], data['occupation']))
        conn.commit()
        return jsonify({"status": "success"}), 201
    except Exception as e:
        print(e)
        return jsonify({"status": "fail", "message": str(e)}), 400
    finally:
        conn.close()

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (data['username'], data['password']))
    user = cursor.fetchone()
    conn.close()
    if user:
        return jsonify({
            "status": "success",
            "user_id": user['user_id'],
            "username": user['username'],
            "gender": user['gender'],
            "age": user['age'],
            "occupation": user['occupation']
        })
    return jsonify({"status": "fail", "message": "Invalid credentials"}), 401

@app.route("/random_movies", methods=["GET"])
def random_movies():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT title, poster_path FROM complete_movie_poster ORDER BY RANDOM() LIMIT 10")
    movies = [{"title": r["title"], "poster_url": get_poster_url(r["poster_path"])} for r in cursor.fetchall()]
    conn.close()
    return jsonify(movies)

@app.route("/recommend/<int:user_id>", methods=["GET", "POST"])
def recommend(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = cursor.fetchone()
    cursor.execute("SELECT COUNT(*) FROM ratings WHERE user_id=?", (user_id,))
    rating_count = cursor.fetchone()[0]

    top_titles = []
    if user and rating_count > 0:
        top_titles = model.topN(user_id, n=10).tolist()
    elif user:
        u_vec = build_user_vector(user_id, user['gender'], user['age'], user['occupation'])
        top_titles = model.topN_cold(n=10,U=u_vec).tolist()
        print(top_titles)
    else:
        data = request.get_json(silent=True) or {}
        u_vec = build_user_vector(-1, data.get("gender", 0), data.get("age", 25), data.get("occupation", "other"))
        top_titles = model.topN_cold(U=u_vec, n=10).tolist()

    # --- THE FIXED SQL QUERY SECTION ---
    results = []
    if top_titles:
        # Create a string of placeholders: '?, ?, ?, ?, ?, ?, ?, ?, ?, ?'
        placeholders = ', '.join(['?'] * len(top_titles))

        # Use double quotes for the column with a space and placeholders for the values
        query = f'SELECT title, poster_path FROM complete_movie_poster WHERE "Movie ID" IN ({placeholders})'
        
        cursor.execute(query, top_titles)
        
        # Format the final JSON response
        results = [
            {
                "title": r["title"], 
                "poster_url": get_poster_url(r["poster_path"])
            } 
            for r in cursor.fetchall()
        ]

    conn.close()
    return jsonify({"movies": results})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)