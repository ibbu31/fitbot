from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for
from flask_bcrypt import Bcrypt
from flask_mail import Message
import psycopg2
import psycopg2.extras
from database import get_db

bcrypt = Bcrypt()
auth = Blueprint('auth', __name__)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')

    data = request.json
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '').strip()

    if not username or not email or not password:
        return jsonify({'error': 'All fields are required'}), 400

    if len(username) < 3:
        return jsonify({'error': 'Username must be at least 3 characters'}), 400

    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400

    if '@' not in email:
        return jsonify({'error': 'Invalid email address'}), 400

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO users (username, email, password) VALUES (%s, %s, %s)',
            (username, email, hashed_password)
        )
        conn.commit()
        cursor.close()
        conn.close()

        # Send welcome email — wrapped in try/except so signup never fails
        # just because the email didn't go through
        try:
            from app import mail
            welcome_msg = Message(
                subject="Welcome to FitBot! 💪",
                recipients=[email],
                html=f"""
                <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;background:#000a1e;color:white;padding:30px;border-radius:16px;">
                    <h1 style="color:#0078ff;text-align:center;">🏋️ Welcome to FitBot, {username}!</h1>
                    <p style="color:rgba(255,255,255,0.7);text-align:center;">Your free AI fitness coach is ready. Get personalized workout plans, diet advice, and progress tracking — all in one place.</p>
                    <div style="text-align:center;margin:30px 0;">
                        <a href="https://fitbot-402357265699.asia-south1.run.app" style="background:#0078ff;color:white;padding:14px 32px;border-radius:25px;text-decoration:none;font-weight:bold;">Start Your First Workout 💪</a>
                    </div>
                    <p style="color:rgba(255,255,255,0.4);text-align:center;font-size:0.85rem;">Questions or feedback? Just reply to this email — a real person reads it.</p>
                </div>
                """
            )
            mail.send(welcome_msg)
        except Exception as e:
            print(f"Welcome email error: {e}")

        return jsonify({'success': True, 'message': 'Account created successfully!'})
    except Exception as e:
        return jsonify({'error': 'Username or email already exists'}), 400

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    data = request.json
    email = data.get('email', '').strip()
    password = data.get('password', '').strip()

    if not email or not password:
        return jsonify({'error': 'All fields are required'}), 400

    if '@' not in email:
        return jsonify({'error': 'Invalid email address'}), 400

    try:
        conn = get_db()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(
            'SELECT * FROM users WHERE email = %s', (email,)
        )
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if not user or not bcrypt.check_password_hash(user['password'], password):
            return jsonify({'error': 'Invalid email or password'}), 401

        session['user_id'] = user['id']
        session['username'] = user['username']
        session.permanent = True
        return jsonify({'success': True, 'username': user['username']})

    except Exception as e:
        return jsonify({'error': 'Database error. Please try again!'}), 500

@auth.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))