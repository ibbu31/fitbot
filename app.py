from flask import Flask, request, jsonify, render_template, session, redirect, url_for, send_file
from flask_bcrypt import Bcrypt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from flask_mail import Mail, Message
from groq import Groq
from dotenv import load_dotenv
from database import init_db, get_db
from auth import auth, bcrypt
import psycopg2
import psycopg2.extras
import google.generativeai as genai
import bleach
import os
import time
import secrets

load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY", "fitbot-secret-key")
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = 3600
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv("MAIL_EMAIL")
app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")
app.config['MAIL_DEFAULT_SENDER'] = os.getenv("MAIL_EMAIL")

mail = Mail(app)

Talisman(app, force_https=False, session_cookie_secure=False, content_security_policy=False)

limiter = Limiter(app=app, key_func=get_remote_address, default_limits=["200 per day", "50 per hour"])

bcrypt.init_app(app)
app.register_blueprint(auth)

try:
    from admin import admin
    app.register_blueprint(admin)
except:
    pass

with app.app_context():
    init_db()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
gemini_model = genai.GenerativeModel("gemini-1.5-flash")

SYSTEM_PROMPT = """You are FitBot, a professional gym trainer and nutritionist with 10 years of experience. You are smart, motivating, and highly knowledgeable.

PERSONALITY:
- Speak like a friendly, energetic personal trainer
- Use the user's name when possible
- Be encouraging and positive
- Give specific, actionable advice

RESPONSE FORMAT RULES (VERY IMPORTANT):
- NEVER write long paragraphs
- ALWAYS use bullet points and short lines
- Use emojis to make it visual and fun
- Structure every response like this:

For workout plans use this format:
💪 **[Workout Name]**
- Exercise 1 — sets x reps (rest time)
- Exercise 2 — sets x reps (rest time)

For diet advice use this format:
🥗 **[Meal Name]**
- Food item 1 — quantity
- Food item 2 — quantity

For general advice use this format:
✅ **Key Point 1**
Brief explanation in 1 line

SMART BEHAVIOR:
- Remember what the user told you earlier in the conversation
- Personalize every response based on their goal and level
- If user mentions pain or injury, immediately suggest safer alternatives
- Always ask follow-up questions to give better advice
- Give specific numbers (sets, reps, calories, protein grams)

ONBOARDING (first message only):
Ask these 4 questions in a fun way:
1. What is your fitness goal? (weight loss / muscle gain / endurance / general fitness)
2. What is your level? (beginner / intermediate / advanced)
3. What equipment do you have? (gym / home / no equipment)
4. Any injuries or pain areas? (or type none)

After getting answers, generate their first workout immediately!

Always recommend consulting a doctor for medical issues."""

ALLOWED_TAGS = ['b', 'i', 'em', 'strong']

def sanitize_input(text):
    if not text:
        return ""
    text = bleach.clean(str(text), tags=[], strip=True)
    return text[:1000].strip()

def call_gemini(messages, system_prompt):
    try:
        conversation = system_prompt + "\n\n"
        for msg in messages:
            if msg['role'] == 'user':
                conversation += f"User: {msg['content']}\n"
            else:
                conversation += f"FitBot: {msg['content']}\n"
        response = gemini_model.generate_content(conversation)
        return response.text
    except Exception as e:
        print(f"Gemini error: {e}")
        return None

def call_groq_with_retry(messages, system_prompt, retries=3):
    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": system_prompt}, *messages],
                max_tokens=1024
            )
            return response.choices[0].message.content
        except Exception as e:
            error_str = str(e)
            if 'rate_limit' in error_str.lower() or '429' in error_str:
                if attempt < retries - 1:
                    time.sleep((attempt + 1) * 3)
                    continue
                gemini_reply = call_gemini(messages, system_prompt)
                if gemini_reply:
                    return gemini_reply
                return "⚠️ FitBot is very busy! Please wait 30 seconds and try again. 💪"
            else:
                gemini_reply = call_gemini(messages, system_prompt)
                if gemini_reply:
                    return gemini_reply
                return "⚠️ Something went wrong. Please try again! 💪"
    return "⚠️ FitBot is very busy! Please try again in 1 minute. 💪"

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    return response

@app.route("/")
@login_required
def home():
    return render_template("index.html", username=session.get('username'))

@app.route("/chat", methods=["POST"])
@login_required
@limiter.limit("20 per minute")
def chat():
    user_id = session['user_id']
    username = session.get('username', 'there')

    if not request.json:
        return jsonify({'error': 'Invalid request'}), 400

    user_message = sanitize_input(request.json.get("message", ""))
    user_language = request.json.get("language", "en-US")

    if user_language not in ["en-US", "hi-IN"]:
        user_language = "en-US"

    if not user_message:
        return jsonify({'error': 'Empty message'}), 400

    language_instruction = "Hindi" if user_language == "hi-IN" else "English"
    system_with_language = SYSTEM_PROMPT + f"\n\nIMPORTANT: Reply in {language_instruction} only. Address the user as {username}."

    try:
        conn = get_db()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(
            'SELECT role, message FROM chat_history WHERE user_id = %s ORDER BY created_at DESC LIMIT 20',
            (user_id,)
        )
        history = cursor.fetchall()
        messages = [{"role": row['role'], "content": row['message']} for row in reversed(history)]
        messages.append({"role": "user", "content": user_message})

        bot_reply = call_groq_with_retry(messages, system_with_language)
        bot_reply_clean = bleach.clean(bot_reply, tags=ALLOWED_TAGS, strip=True)

        cursor.execute(
            'INSERT INTO chat_history (user_id, role, message) VALUES (%s, %s, %s)',
            (user_id, 'user', user_message)
        )
        cursor.execute(
            'INSERT INTO chat_history (user_id, role, message) VALUES (%s, %s, %s)',
            (user_id, 'assistant', bot_reply_clean)
        )
        conn.commit()
        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Chat error: {e}")
        return jsonify({'error': 'Something went wrong. Please try again!'}), 500

    return jsonify({"reply": bot_reply_clean})

@app.route("/progress/add", methods=["POST"])
@login_required
def add_progress():
    user_id = session['user_id']
    data = request.json
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO progress (user_id, weight, body_fat, workout_completed, workout_name, sets_completed, reps_completed, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            user_id,
            data.get('weight'),
            data.get('body_fat'),
            data.get('workout_completed', False),
            data.get('workout_name', ''),
            data.get('sets_completed', 0),
            data.get('reps_completed', 0),
            data.get('notes', '')
        ))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/progress/history", methods=["GET"])
@login_required
def progress_history():
    user_id = session['user_id']
    try:
        conn = get_db()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(
            'SELECT * FROM progress WHERE user_id = %s ORDER BY created_at DESC LIMIT 30',
            (user_id,)
        )
        history = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify([dict(row) for row in history])
    except Exception as e:
        return jsonify({'error': str(e)}), 500
@app.route("/generate-pdf", methods=["POST"])
@login_required
def generate_pdf():
    username = session.get('username', 'User')
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.units import mm
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        import io

        data = request.json
        workout_plan = data.get('workout_plan', [])
        plan_text = data.get('plan_text', '')
        plan_type = data.get('plan_type', 'Workout Plan')

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
            rightMargin=20*mm, leftMargin=20*mm,
            topMargin=20*mm, bottomMargin=20*mm)

        # Styles
        title_style = ParagraphStyle('Title', fontSize=24,
            textColor=colors.HexColor('#0078ff'),
            fontName='Helvetica-Bold', spaceAfter=4, alignment=TA_CENTER)
        subtitle_style = ParagraphStyle('Subtitle', fontSize=11,
            textColor=colors.HexColor('#888888'),
            fontName='Helvetica', spaceAfter=20, alignment=TA_CENTER)
        section_style = ParagraphStyle('Section', fontSize=14,
            textColor=colors.HexColor('#0078ff'),
            fontName='Helvetica-Bold', spaceAfter=8, spaceBefore=16)
        body_style = ParagraphStyle('Body', fontSize=10,
            textColor=colors.HexColor('#333333'),
            fontName='Helvetica', leading=16, spaceAfter=4)
        bullet_style = ParagraphStyle('Bullet', fontSize=10,
            textColor=colors.HexColor('#333333'),
            fontName='Helvetica', leading=16, spaceAfter=3,
            leftIndent=16, bulletIndent=6)

        BLUE = colors.HexColor('#0078ff')
        LIGHT = colors.HexColor('#f0f6ff')
        WHITE = colors.white

        story = []

        # Header
        story.append(Paragraph("🏋️ FitBot — Your AI Fitness Coach", title_style))
        story.append(Paragraph(f"Personal {plan_type} for {username}", subtitle_style))
        story.append(Spacer(1, 6*mm))

        # If we have parsed exercises — show them in table
        if workout_plan and len(workout_plan) > 0 and workout_plan[0].get('name') != 'See your FitBot chat for full plan':
            story.append(Paragraph(f"📋 {plan_type}", section_style))

            table_data = [['Exercise', 'Sets', 'Reps', 'Rest']]
            for ex in workout_plan:
                table_data.append([
                    ex.get('name', ''),
                    str(ex.get('sets', '3')),
                    str(ex.get('reps', '10-12')),
                    str(ex.get('rest', '60s'))
                ])

            table = Table(table_data, colWidths=[90*mm, 25*mm, 35*mm, 25*mm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), BLUE),
                ('TEXTCOLOR', (0,0), (-1,0), WHITE),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,-1), 10),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [LIGHT, WHITE]),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#d0e4ff')),
                ('ALIGN', (1,0), (-1,-1), 'CENTER'),
                ('ALIGN', (0,0), (0,-1), 'LEFT'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('TOPPADDING', (0,0), (-1,-1), 7),
                ('BOTTOMPADDING', (0,0), (-1,-1), 7),
                ('LEFTPADDING', (0,0), (0,-1), 10),
            ]))
            story.append(table)
            story.append(Spacer(1, 8*mm))

        # Always include the full chat text as plan details
        if plan_text and len(plan_text.strip()) > 10:
            story.append(Paragraph("📝 Your Complete Plan Details", section_style))

            # Split plan text into lines and add as paragraphs
            lines = plan_text.split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    story.append(Spacer(1, 3*mm))
                    continue

                # Clean line from HTML tags
                import re
                line = re.sub(r'<[^>]+>', '', line)
                line = line.replace('&nbsp;', ' ').replace('&amp;', '&')

                if not line.strip():
                    continue

                # Detect bullet points
                if line.startswith('•') or line.startswith('-') or line.startswith('*'):
                    clean = line.lstrip('•-* ').strip()
                    if clean:
                        story.append(Paragraph(f"• {clean}", bullet_style))
                # Detect headings (bold lines or lines with emojis at start)
                elif len(line) < 60 and (line.isupper() or any(ord(c) > 127 for c in line[:3])):
                    story.append(Paragraph(line, ParagraphStyle('h',
                        fontSize=11, textColor=colors.HexColor('#0078ff'),
                        fontName='Helvetica-Bold', spaceAfter=4, spaceBefore=8)))
                else:
                    story.append(Paragraph(line, body_style))

        story.append(Spacer(1, 10*mm))

        # Footer
        from reportlab.platypus import HRFlowable
        story.append(HRFlowable(width="100%", thickness=0.5,
            color=colors.HexColor('#cccccc'), spaceAfter=6))
        footer_style = ParagraphStyle('Footer', fontSize=8,
            textColor=colors.HexColor('#999999'),
            fontName='Helvetica', alignment=TA_CENTER)
        story.append(Paragraph("Generated by FitBot AI — Your Personal Fitness Coach", footer_style))
        story.append(Paragraph("Always consult a doctor before starting any fitness program.", footer_style))

        doc.build(story)
        buffer.seek(0)

        return send_file(
            buffer,
            as_attachment=True,
            download_name=f'fitbot_{plan_type.lower().replace(" ", "_")}_{username}.pdf',
            mimetype='application/pdf'
        )

    except Exception as e:
        print(f"PDF error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Could not generate PDF: {str(e)}'}), 500

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "GET":
        return render_template("forgot_password.html")

    email = sanitize_input(request.json.get("email", ""))
    if not email:
        return jsonify({'error': 'Email is required'}), 400

    try:
        conn = get_db()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        user = cursor.fetchone()

        if not user:
            return jsonify({'success': True, 'message': 'If this email exists, a reset link has been sent!'})

        token = secrets.token_urlsafe(32)
        cursor.execute('''
            INSERT INTO password_resets (user_id, token, created_at)
            VALUES (%s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (user_id) DO UPDATE SET token = %s, created_at = CURRENT_TIMESTAMP
        ''', (user['id'], token, token))
        conn.commit()
        cursor.close()
        conn.close()

        reset_url = f"{request.host_url}reset-password/{token}"
        msg = Message(
            subject="FitBot — Reset Your Password",
            recipients=[email],
            html=f"""
            <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;background:#0a0a0a;color:white;padding:30px;border-radius:16px;">
                <h1 style="color:#0078ff;text-align:center;">FitBot</h1>
                <h2 style="text-align:center;">Reset Your Password</h2>
                <p style="color:rgba(255,255,255,0.7);text-align:center;">Click the button below to reset your password. This link expires in 1 hour.</p>
                <div style="text-align:center;margin:30px 0;">
                    <a href="{reset_url}" style="background:#0078ff;color:white;padding:14px 32px;border-radius:25px;text-decoration:none;font-weight:bold;">Reset Password</a>
                </div>
                <p style="color:rgba(255,255,255,0.4);text-align:center;font-size:0.85rem;">If you did not request this, ignore this email.</p>
            </div>
            """
        )
        mail.send(msg)
        return jsonify({'success': True, 'message': 'Reset link sent to your email!'})

    except Exception as e:
        print(f"Forgot password error: {e}")
        return jsonify({'error': 'Something went wrong. Please try again!'}), 500
@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    if request.method == "GET":
        return render_template("reset_password.html", token=token)

    try:
        data = request.json
        if not data:
            return jsonify({'error': 'Invalid request'}), 400

        new_password = data.get("password", "").strip()

        if not new_password:
            return jsonify({'error': 'Password is required'}), 400

        if len(new_password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400

        conn = get_db()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Check token exists and not expired
        cursor.execute('''
            SELECT * FROM password_resets
            WHERE token = %s
            AND created_at > CURRENT_TIMESTAMP - INTERVAL '1 hour'
        ''', (token,))
        reset = cursor.fetchone()

        if not reset:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Reset link is invalid or expired! Please request a new one.'}), 400

        # Hash new password
        hashed = bcrypt.generate_password_hash(new_password).decode('utf-8')

        # Update password
        cursor.execute(
            'UPDATE users SET password = %s WHERE id = %s',
            (hashed, reset['user_id'])
        )

        # Delete used token
        cursor.execute(
            'DELETE FROM password_resets WHERE token = %s',
            (token,)
        )

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'success': True, 'message': 'Password reset successfully!'})

    except Exception as e:
        print(f"Reset password error: {e}")
        return jsonify({'error': f'Database error: {str(e)}'}), 500
@app.route("/exercises")
@login_required
def exercises():
    try:
        return render_template("exercises.html", username=session.get('username'))
    except Exception as e:
        print(f"Exercises error: {e}")
        return f"<h1>Error loading exercises: {str(e)}</h1>", 500

@app.route("/progress")
@login_required
def progress_page():
    try:
        return render_template("progress.html", username=session.get('username'))
    except Exception as e:
        print(f"Progress error: {e}")
        return f"<h1>Error loading progress: {str(e)}</h1>", 500
    try:
        conn = get_db()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute('''
            SELECT * FROM password_resets
            WHERE token = %s
            AND created_at > CURRENT_TIMESTAMP - INTERVAL '1 hour'
        ''', (token,))
        reset = cursor.fetchone()

        if not reset:
            return jsonify({'error': 'Reset link is invalid or expired!'}), 400

        hashed = bcrypt.generate_password_hash(new_password).decode('utf-8')
        cursor.execute('UPDATE users SET password = %s WHERE id = %s', (hashed, reset['user_id']))
        cursor.execute('DELETE FROM password_resets WHERE token = %s', (token,))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'message': 'Password reset successfully!'})

    except Exception as e:
        print(f"Reset password error: {e}")
        return jsonify({'error': 'Something went wrong. Please try again!'}), 500

@app.route("/recovery-score", methods=["POST"])
@login_required
def recovery_score():
    data = request.json
    if not data:
        return jsonify({'error': 'Invalid request'}), 400
    try:
        from recovery import calculate_recovery_score
        result = calculate_recovery_score(
            sleep_hours=float(data.get("sleep_hours", 7)),
            soreness=int(data.get("soreness", 3)),
            readiness=int(data.get("readiness", 7)),
            recent_training_load=int(data.get("recent_training_load", 3)),
            hrv=data.get("hrv"),
            resting_hr=data.get("resting_hr")
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/generate-workout", methods=["POST"])
@login_required
def workout_api():
    data = request.json
    if not data:
        return jsonify({'error': 'Invalid request'}), 400
    try:
        from workout_engine import generate_workout
        result = generate_workout(
            goal=data.get("goal", "general_fitness"),
            level=data.get("level", "beginner"),
            equipment=data.get("equipment", []),
            injury_flags=data.get("injury_flags", []),
            sleep_hours=float(data.get("sleep_hours", 7)),
            soreness=int(data.get("soreness", 3)),
            readiness=int(data.get("readiness", 7)),
            recent_training_load=int(data.get("recent_training_load", 3))
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    # ==================
# STREAK & JOURNEY API
# ==================
@app.route("/api/user-stats", methods=["GET"])
@login_required
def user_stats():
    user_id = session['user_id']
    try:
        conn = get_db()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Get all progress ordered by date
        cursor.execute('''
            SELECT date, workout_completed
            FROM progress
            WHERE user_id = %s
            ORDER BY date DESC
        ''', (user_id,))
        logs = cursor.fetchall()

        # Calculate streak
        streak = 0
        from datetime import date, timedelta
        today = date.today()
        check_date = today

        for log in logs:
            log_date = log['date']
            if isinstance(log_date, str):
                from datetime import datetime
                log_date = datetime.strptime(log_date, '%Y-%m-%d').date()
            if log_date == check_date and log['workout_completed']:
                streak += 1
                check_date -= timedelta(days=1)
            elif log_date < check_date:
                break

        # Total days since joined
        cursor.execute('SELECT created_at FROM users WHERE id = %s', (user_id,))
        user = cursor.fetchone()
        days_since_joined = (today - user['created_at'].date()).days + 1

        # Total workouts completed
        cursor.execute('''
            SELECT COUNT(*) as total FROM progress
            WHERE user_id = %s AND workout_completed = TRUE
        ''', (user_id,))
        total_workouts = cursor.fetchone()['total']

        cursor.close()
        conn.close()

        return jsonify({
            'streak': streak,
            'day_number': days_since_joined,
            'total_workouts': total_workouts,
            'username': session.get('username')
        })
    except Exception as e:
        print(f"User stats error: {e}")
        return jsonify({'streak': 0, 'day_number': 1, 'total_workouts': 0})

# ==================
# DAILY REMINDER EMAIL
# ==================
@app.route("/api/send-reminders", methods=["POST"])
def send_reminders():
    # This endpoint can be called by a cron job
    secret = request.json.get('secret', '')
    if secret != os.getenv('ADMIN_PASSWORD', 'fitbot-admin-2024'):
        return jsonify({'error': 'Unauthorized'}), 401

    try:
        from datetime import date
        conn = get_db()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Find users who have NOT logged progress today
        cursor.execute('''
            SELECT u.id, u.username, u.email
            FROM users u
            WHERE u.id NOT IN (
                SELECT DISTINCT user_id FROM progress
                WHERE date = CURRENT_DATE
            )
            AND u.created_at < CURRENT_TIMESTAMP - INTERVAL '1 day'
        ''')
        inactive_users = cursor.fetchall()
        cursor.close()
        conn.close()

        sent = 0
        for user in inactive_users:
            try:
                msg = Message(
                    subject="💪 Your FitBot workout is waiting!",
                    recipients=[user['email']],
                    html=f"""
                    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;background:#000a1e;color:white;padding:30px;border-radius:16px;">
                        <h1 style="color:#0078ff;text-align:center;">🏋️ FitBot</h1>
                        <h2 style="text-align:center;">Hey {user['username']}! Don't break your streak! 🔥</h2>
                        <p style="color:rgba(255,255,255,0.7);text-align:center;">You haven't logged your workout today. Your fitness journey is waiting!</p>
                        <div style="text-align:center;margin:30px 0;">
                            <a href="https://fitbot-402357265699.us-central1.run.app" style="background:#0078ff;color:white;padding:14px 32px;border-radius:25px;text-decoration:none;font-weight:bold;">Start Today's Workout 💪</a>
                        </div>
                        <p style="color:rgba(255,255,255,0.4);text-align:center;font-size:0.85rem;">Small steps every day lead to big results!</p>
                    </div>
                    """
                )
                mail.send(msg)
                sent += 1
            except Exception as e:
                print(f"Email error for {user['email']}: {e}")

        return jsonify({'success': True, 'reminders_sent': sent})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.errorhandler(429)
def rate_limit_exceeded(e):
    return jsonify({'error': '⚠️ Too many messages! Please slow down. 💪'}), 429

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Page not found'}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Server error. Please try again!'}), 500

@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'File too large!'}), 413

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host='0.0.0.0', port=port)