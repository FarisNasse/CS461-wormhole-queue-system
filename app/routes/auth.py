from flask import Blueprint, request, jsonify, session, render_template, flash, redirect, url_for
from werkzeug.security import check_password_hash
from app.models import User
from app import db, mail
from flask_mail import Message
from app.auth_utils import login_required
from app.forms import ResetPasswordRequestForm, ResetPasswordForm
from app import limiter  # Ensure Limiter is imported

auth_bp = Blueprint('auth', __name__)

def send_password_reset_email(user: User):
    token = user.get_reset_token()
    # Subject updated to match standard practices
    msg = Message('Reset Your Password', recipients=[user.email])

    link = url_for('auth.reset_password', token=token, _external=True)
    msg.body = f'''To reset your password, visit the following link:
{link}

If you did not make this request, simply ignore this email.'''
    mail.send(msg)

# -------------------------------
# POST /api/login
# -------------------------------
@auth_bp.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    user = User.query.filter_by(username=username).first()

    if user and check_password_hash(user.password_hash, password):
        session['user_id'] = user.id
        session['is_admin'] = user.is_admin
        return jsonify({
            'message': 'Login successful',
            'is_admin': user.is_admin
        }), 200

    return jsonify({'error': 'Invalid credentials'}), 401

# -------------------------------
# POST /api/logout
# -------------------------------
@auth_bp.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logged out successfully'}), 200

# -------------------------------
# GET /api/check-session
# -------------------------------
@auth_bp.route('/api/check-session', methods=['GET'])
def check_session():
    if 'user_id' in session:
        return jsonify({
            'logged_in': True,
            'is_admin': session.get('is_admin', False)
        }), 200

    return jsonify({'logged_in': False}), 200

# -------------------------------
# GET /reset_password_request
# -------------------------------
@auth_bp.route('/reset_password_request', methods=['GET', 'POST'])
@limiter.limit("5 per minute")  # Rate limiting applied here
def reset_password_request():
    if 'user_id' in session:
        return redirect(url_for('views.index'))

    form = ResetPasswordRequestForm()
    
    # LOGIC FIX: success code is now INSIDE the if block
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        # Only flash and redirect if the form submission was technically valid
        flash('If an account with that email exists, check your inbox for reset instructions.', 'info')
        return redirect(url_for('views.assistant_login'))
    
    # If validation fails (invalid email format), we fall through to here
    # This renders the template (Status 200), allowing the test to pass
    return render_template('reset_password_request.html', title='Reset Password', form=form)

# -------------------------------
# GET /reset_password/<token>
# -------------------------------
@auth_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if 'user_id' in session:
        return redirect(url_for('views.index'))

    user = User.verify_reset_token(token)
    if not user:
        flash('The reset link is invalid or has expired.', 'error')
        return redirect(url_for('auth.reset_password_request'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset. You may now sign in.', 'success')
        return redirect(url_for('views.assistant_login'))
        
    return render_template('reset_password.html', form=form)