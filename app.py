from flask import Flask, render_template, request, session, redirect
from flask_socketio import SocketIO, emit
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

socketio = SocketIO(app, async_mode='eventlet')
db = SQLAlchemy(app)

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

# Message Model
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Initialize database and create default admin account
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username="raven44").first():
        admin = User(username="raven44", password="1234", is_admin=True)
        db.session.add(admin)
        db.session.commit()

banned_users = set()
pinned_message = None

@app.route("/")
def index():
    if "username" in session:
        return render_template("index.html", username=session["username"], is_admin=session.get("is_admin", False))
    return redirect("/login")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username, password=password).first()
        if user and username not in banned_users:
            session["username"] = user.username
            session["is_admin"] = user.is_admin
            return redirect("/")
        return "Invalid credentials or banned user."
    return '''
    <h1>Sign Up or Log In</h1>
    <form method="POST">
        <input type="text" name="username" placeholder="Username" required>
        <input type="password" name="password" placeholder="Password" required>
        <button type="submit">Log In</button>
    </form>
    <p>Don't have an account? <a href="/register">Sign up here</a></p>
    '''

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if User.query.filter_by(username=username).first():
            return "Username already exists."
        new_user = User(username=username, password=password, is_admin=False)
        db.session.add(new_user)
        db.session.commit()
        return "Account created successfully. Please log in."
    return '''
    <h1>Create Account</h1>
    <form method="POST">
        <input type="text" name="username" placeholder="Username" required>
        <input type="password" name="password" placeholder="Password" required>
        <button type="submit">Sign Up</button>
    </form>
    <p>Already have an account? <a href="/login">Log in here</a></p>
    '''

@app.route("/logout")
def logout():
    session.pop("username", None)
    session.pop("is_admin", None)
    return redirect("/login")

@app.route("/shutdown", methods=["POST"])
def shutdown():
    if session.get("is_admin", False):
        func = request.environ.get('werkzeug.server.shutdown')
        if func is None:
            raise RuntimeError("Not running with the Werkzeug Server")
        func()
        return "Server is shutting down..."
    return "Unauthorized access."

@socketio.on('message')
def handle_message(data):
    if "username" in session:
        username = session["username"]
        message_text = data.get("message")
        new_message = Message(username=username, message=message_text)
        db.session.add(new_message)
        db.session.commit()
        timestamp = datetime.now().strftime('%H:%M:%S')
        full_message = f"[{timestamp}] {username}: {message_text}"
        emit('new_message', full_message, broadcast=True)

@socketio.on('ban_user')
def ban_user(data):
    if session.get("is_admin", False):
        banned_username = data.get("username")
        banned_users.add(banned_username)
        emit('system_message', f"{banned_username} has been banned by an admin.", broadcast=True)

@socketio.on('unban_user')
def unban_user(data):
    if session.get("is_admin", False):
        unbanned_username = data.get("username")
        banned_users.discard(unbanned_username)
        emit('system_message', f"{unbanned_username} has been unbanned by an admin.", broadcast=True)

@socketio.on('pin_message')
def pin_message(data):
    if session.get("is_admin", False):
        global pinned_message
        pinned_message = data.get("message")
        emit('pin_message', pinned_message, broadcast=True)

@socketio.on('promote_user')
def promote_user(data):
    if session.get("is_admin", False):
        username = data.get("username")
        user = User.query.filter_by(username=username).first()
        if user:
            user.is_admin = True
            db.session.commit()
            emit('system_message', f"{username} has been promoted to admin.", broadcast=True)
        else:
            emit('system_message', f"User {username} not found.", broadcast=True)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))