from flask import Blueprint, jsonify, request
from app import db
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
    return jsonify({'success': 'item deleted'}), 200

#route to add user
@user_bp.route('/users_add', methods=['POST'])
def users_add():

    data = request.get_json()

    # check for all input parameters, and return error if missing any
    if not data or not all(k in data for k in ['username',
                                                'email',
                                                'password',
                                                'is_admin']):
        return jsonify({'error': 'Missing required fields'}), 400


    new_user = User(
        username = data['username'],
        email = data['email'],
        is_admin = data.get("is_admin", False)
    )

    new_user.set_password(data['password'])


    db.session.add(new_user)
    db.session.commit()
    return jsonify(data), 201 # return lik