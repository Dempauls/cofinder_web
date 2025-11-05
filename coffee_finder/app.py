from flask import Flask, jsonify, request, render_template, redirect, url_for
import sqlite3
import os
from datetime import datetime

app = Flask(__name__, static_folder="static", template_folder="templates")

DB_NAME = "coffee_finder.db"



def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    if not os.path.exists(DB_NAME):
        conn = get_db_connection()
        conn.execute('''
            CREATE TABLE coffee_shops (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                address TEXT NOT NULL,
                lat REAL,
                lon REAL,
                description TEXT,
                link TEXT
            )
        ''')
        conn.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL
            )
        ''')
        conn.execute('''
            CREATE TABLE favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                cafe_id INTEGER,
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(cafe_id) REFERENCES coffee_shops(id)
            )
        ''')
        conn.execute('''
            CREATE TABLE reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                cafe_id INTEGER,
                rating INTEGER,
                comment TEXT,
                created_at TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(cafe_id) REFERENCES coffee_shops(id)
            )
        ''')
        conn.commit()
        conn.close()
        print("Database created successfully!")
        seed_data()
        create_default_user()


def create_default_user():
    """Create a test login user if none exists."""
    conn = get_db_connection()
    conn.execute("INSERT INTO users (email, password) VALUES (?, ?)", ("admin@example.com", "admin123"))
    conn.commit()
    conn.close()
    print(" Default user created — Email: admin@example.com | Password: admin123")


def seed_data():
    shops = [
    ("Uncle's Brew", "Plaza Margarita, Minglanilla", 10.2442, 123.7995, "Trendy hangout spot with cold brew favorites", "https://www.google.com/maps?q=10.2442,123.7995"),
    ("Don Macchiato", "Minglanilla Highway, near Gaisano Grand", 10.2429, 123.8008, "Famous for strong brews and cozy setup", "https://www.google.com/maps?q=10.2429,123.8008"),
    ("Wander Cafe", "Minglanilla Town Proper", 10.2445, 123.7988, "Perfect for travelers and students, relaxing vibe", "https://www.google.com/maps?q=10.2445,123.7988"),
    ("Selah Cafe", "Minglanilla Plaza Area", 10.2438, 123.7975, "Chill place with artsy interior and nice coffee", "https://www.google.com/maps?q=10.2438,123.7975"),
    ("Links Cafe", "Lipata, Minglanilla", 10.2460, 123.8032, "Community-style cafe near schools", "https://www.google.com/maps?q=10.2460,123.8032"),
    ("Side Street Cafe", "Behind Minglanilla Plaza", 10.2450, 123.8000, "Quiet coffee corner with snacks", "https://www.google.com/maps?q=10.2450,123.8000"),
    ("Above Ground", "Upper Tunghaan, Minglanilla", 10.2490, 123.8045, "Hilltop cafe with overlooking view", "https://www.google.com/maps?q=10.2490,123.8045"),
    ("Teology", "Minglanilla Town Proper", 10.2432, 123.7999, "Creative tea and coffee blends in a relaxing atmosphere", "https://www.google.com/maps?q=10.2432,123.7999"),
    ("A Little Tea", "Minglanilla Highway", 10.2449, 123.8012, "Refreshing milk teas and cozy hangout place", "https://www.google.com/maps?q=10.2449,123.8012")
]

    conn = get_db_connection()
    conn.executemany('''
        INSERT INTO coffee_shops (name, address, lat, lon, description, link)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', shops)
    conn.commit()
    conn.close()
    print("☕ Initial coffee shops added!")



@app.route("/")
def home():
    return render_template("map.html")


@app.route("/api/shops")
def api_shops():
    q = request.args.get("q", "").lower()
    conn = get_db_connection()
    if q:
        query = "SELECT * FROM coffee_shops WHERE lower(name) LIKE ? OR lower(address) LIKE ?"
        shops = conn.execute(query, (f"%{q}%", f"%{q}%")).fetchall()
    else:
        shops = conn.execute("SELECT * FROM coffee_shops").fetchall()
    conn.close()
    return jsonify([dict(row) for row in shops])



@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE email = ? AND password = ?", (email, password)).fetchone()
        conn.close()

        if user:
            
            return redirect(url_for("home"))
        else:
            return render_template("login.html", error="Invalid email or password!")

    return render_template("login.html")



@app.route("/favorite/<int:cafe_id>", methods=["POST"])
def favorite_cafe(cafe_id):
    
    user_id = 1
    conn = get_db_connection()
    conn.execute("INSERT INTO favorites (user_id, cafe_id) VALUES (?, ?)", (user_id, cafe_id))
    conn.commit()
    conn.close()
    print(f"❤️ Cafe {cafe_id} favorited by user {user_id}")
    return redirect(url_for("home"))



@app.route("/review/<int:cafe_id>", methods=["POST"])
def review_cafe(cafe_id):
    user_id = 1  
    rating = request.form.get("rating")
    comment = request.form.get("comment")

    conn = get_db_connection()
    conn.execute("""
        INSERT INTO reviews (user_id, cafe_id, rating, comment, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, cafe_id, rating, comment, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()
    print(f"📝 Review added for cafe {cafe_id} by user {user_id}")
    return redirect(url_for("home"))



@app.route("/api/reviews/<int:cafe_id>")
def get_reviews(cafe_id):
    conn = get_db_connection()
    reviews = conn.execute("""
        SELECT r.*, u.email AS user_email
        FROM reviews r
        JOIN users u ON r.user_id = u.id
        WHERE cafe_id = ?
        ORDER BY created_at DESC
    """, (cafe_id,)).fetchall()
    conn.close()
    return jsonify([dict(row) for row in reviews])



@app.route("/admin")
def admin_dashboard():
    """Display all cafes in the admin page."""
    conn = get_db_connection()
    cafes = conn.execute("SELECT * FROM coffee_shops").fetchall()
    conn.close()
    return render_template("admin.html", cafes=cafes)


@app.route("/admin/add", methods=["POST"])
def admin_add():
    """Add a new cafe from the admin form."""
    name = request.form["name"]
    address = request.form["address"]
    lat = request.form["lat"]
    lon = request.form["lon"]
    description = request.form.get("description", "")
    link = request.form.get("link", "")

    conn = get_db_connection()
    conn.execute("""
        INSERT INTO coffee_shops (name, address, lat, lon, description, link)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name, address, lat, lon, description, link))
    conn.commit()
    conn.close()
    print(f"☕ Added new cafe: {name}")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/edit/<int:cafe_id>", methods=["GET", "POST"])
def admin_edit(cafe_id):
    """Edit a cafe’s details."""
    conn = get_db_connection()
    cafe = conn.execute("SELECT * FROM coffee_shops WHERE id = ?", (cafe_id,)).fetchone()

    if not cafe:
        conn.close()
        return "Cafe not found", 404

    if request.method == "POST":
        name = request.form["name"]
        address = request.form["address"]
        lat = request.form["lat"]
        lon = request.form["lon"]
        description = request.form.get("description", "")
        link = request.form.get("link", "")

        conn.execute("""
            UPDATE coffee_shops
            SET name = ?, address = ?, lat = ?, lon = ?, description = ?, link = ?
            WHERE id = ?
        """, (name, address, lat, lon, description, link, cafe_id))
        conn.commit()
        conn.close()
        print(f" Updated cafe ID {cafe_id}")
        return redirect(url_for("admin_dashboard"))

    conn.close()
    return render_template("edit_cafe.html", cafe=cafe)


@app.route("/admin/delete/<int:cafe_id>", methods=["POST"])
def admin_delete(cafe_id):
    """Delete a cafe."""
    conn = get_db_connection()
    conn.execute("DELETE FROM coffee_shops WHERE id = ?", (cafe_id,))
    conn.commit()
    conn.close()
    print(f" Deleted cafe ID {cafe_id}")
    return redirect(url_for("admin_dashboard"))




if __name__ == "__main__":
    init_db()
    print(" Coffee Finder running at http://127.0.0.1:5000")
    app.run(debug=True)
