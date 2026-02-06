from flask import Blueprint, flash, jsonify, redirect, request, url_for

from app import db
from app.forms import RegisterForm
from app.models import User

user_bp = Blueprint('users', __name__, url_prefix='/api')


#route to remove user
@user_bp.route('/users_remove', methods=['POST'])
def users_remove():

    data = request.get_json()

    # filler field for now, to be updated later
    if not data or not all(k in data for k in ['username']):
        return jsonify({'error': 'Missing required fields'}), 400

    user = User.query.filter_by(username=data['username']).first()

    if not user:
        return jsonify({'error': 'User not found'}), 400

    db.session.delete(user)
    db.session.commit()

    if user.is_admin:
        return jsonify({'success': 'admin removed'}), 200

    return jsonify({'success': 'user removed'}), 200

#route to add user
@user_bp.route('/users_add', methods=['POST'])
def users_add():
    form = RegisterForm()
    if form.validate_on_submit():
        u = User(
            username=form.username.data,
            email=form.email.data,
            is_admin=form.is_admin.data
        )

        u.set_password(form.password.data)

        db.session.add(u)
        db.session.commit()

        flash('User added successfully!', 'success')
        return redirect(url_for('views.user_list'))

    flash('Error adding user. Please check the form and try again.', 'error')
    return redirect(url_for('views.users_add'))

# New JSON API for testing
@user_bp.route('/users_add_json', methods=['POST'])
def api_users_add():
    data = request.get_json()

    if not data or not all(k in data for k in ['username', 'email', 'password']):
        return jsonify({'error': 'Missing required fields'}), 400

    # Check if user already exists
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 400
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 400

    u = User(
        username=data['username'],
        email=data['email'],
        is_admin=data.get('is_admin', False)
    )
    u.set_password(data['password'])

    db.session.add(u)
    db.session.commit()

    return jsonify({'success': 'User created', 'username': u.username}), 201
