from flask import Blueprint, render_template, session, redirect, url_for, jsonify
from database import get_db
import psycopg2.extras
import os

admin = Blueprint('admin', __name__)

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "fitbot-admin-2024")

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('is_admin'):
            return redirect(url_for('admin.admin_login'))
        return f(*args, **kwargs)
    return decorated

@admin.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    from flask import request
    if request.method == 'POST':
        password = request.json.get('password', '')
        if password == ADMIN_PASSWORD:
            session['is_admin'] = True
            return jsonify({'success': True})
        return jsonify({'error': 'Wrong password'}), 401
    return render_template('admin_login.html')

@admin.route('/admin/logout')
def admin_logout():
    session.pop('is_admin', None)
    return redirect(url_for('admin.admin_login'))

@admin.route('/admin')
@admin_required
def dashboard():
    return render_template('admin_dashboard.html')

@admin.route('/admin/stats')
@admin_required
def stats():
    try:
        conn = get_db()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Total users
        cursor.execute('SELECT COUNT(*) as count FROM users')
        total_users = cursor.fetchone()['count']

        # Users today
        cursor.execute(
            "SELECT COUNT(*) as count FROM users WHERE created_at >= CURRENT_DATE"
        )
        users_today = cursor.fetchone()['count']

        # Total messages
        cursor.execute('SELECT COUNT(*) as count FROM chat_history')
        total_messages = cursor.fetchone()['count']

        # Messages today
        cursor.execute(
            "SELECT COUNT(*) as count FROM chat_history WHERE created_at >= CURRENT_DATE"
        )
        messages_today = cursor.fetchone()['count']

        # Most active users
        cursor.execute('''
            SELECT u.username, COUNT(c.id) as message_count
            FROM users u
            JOIN chat_history c ON u.id = c.user_id
            WHERE c.role = 'user'
            GROUP BY u.username
            ORDER BY message_count DESC
            LIMIT 10
        ''')
        top_users = cursor.fetchall()

        # Recent registrations
        cursor.execute('''
            SELECT username, email, created_at
            FROM users
            ORDER BY created_at DESC
            LIMIT 10
        ''')
        recent_users = cursor.fetchall()

        # Messages per day last 7 days
        cursor.execute('''
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM chat_history
            WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
            AND role = 'user'
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        ''')
        daily_messages = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify({
            "total_users": total_users,
            "users_today": users_today,
            "total_messages": total_messages,
            "messages_today": messages_today,
            "top_users": [dict(u) for u in top_users],
            "recent_users": [dict(u) for u in recent_users],
            "daily_messages": [dict(d) for d in daily_messages]
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500