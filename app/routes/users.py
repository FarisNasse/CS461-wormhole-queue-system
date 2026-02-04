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
        return jsonify({'error': 'Missing required fields'}), 404

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

    # data = request.get_json()

    # # initial post request inputs. pass, email, and is_admin r currently used
    # # email and pass can be empty
    # # can be figured out after UI is figured out
    # if not data or not all(k in data for k in ['username',
    #                                             'is_admin']):
    #     flash(f'Missing required fields', 'error')
    #     return redirect(url_for('views.users_add'))

    # # default email if email is missing
    # email = ''
    # if not data['email']:
    #     email = 'ONID@oregonstate.edu'
    # else:
    #     email = data['email']

    # new_user = User(
    #     username = data['username'],
    #     email = email,
    #     is_admin = data.get("is_admin", False)
    # )

    # # set default password if no password provided
    # if not data['password']:
    #     new_user.set_password("Wormhole")

    # new_user.set_password(data['password'])


    # db.session.add(new_user)
    # db.session.commit()
    # return redirect(url_for('views.user_list'))
