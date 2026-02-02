from app.models import User
from app import db

def test_login_non_user(test_client):
    # send login data with form to login end point

    resp = test_client.post('/assistant-login',
        data={
            "username": "testuser",
            "password": "wrongpass"
        })

    # check page did not redirect
    assert 'Assistant Login' in resp.data.decode()

def test_failed_login(test_client):

    # send login data with incomplete form data
    resp = test_client.post(
    '/assistant-login',
    data={
        "username": "testuser",
        "password": ""
    },
    follow_redirects=True)

    html = resp.data.decode()

    fail_msg = '<span style="color: red;">[This field is required.]</span>'
    
    assert fail_msg in html

def test_login_existing_user(test_client):
    # create user with route
    u = User(
        username='testuser',
        email='uniquetestemail@oregonstate.edu',
        is_admin=False
    )

    u.set_password("testpassword")

    db.session.add(u)
    db.session.commit()


    # send login data with form to login end point
    resp = test_client.post('/assistant-login',
        data={
            "username": "testuser",
            "password": "testpassword"
        },
        follow_redirects=True)

    # verify success

    assert resp.status_code == 200

def test_login_homepage_change(test_client):
    # first check assistant link is not rendered
    assistant_link = '<a href="/user/assistant">Profile</a>'
    resp = test_client.get("/index")
    assert assistant_link not in resp.data.decode()

    # create user
    u = User(
        username='testuser',
        email='uniquetestemail@oregonstate.edu',
        is_admin=False
    )

    u.set_password("testpassword")

    db.session.add(u)
    db.session.commit()

    # login with valid user
    resp = test_client.post('/assistant-login',
        data={
            "username": "testuser",
            "password": "testpassword"
        },
        follow_redirects=True)

    # nav to home page, with assistant credentials this time
    resp = test_client.get("/index")

    # check that assistant link now renders
    assert assistant_link in resp.data.decode()

def test_password_change_missing_form(test_client):
    # create user
    u = User(
        username='testuser',
        email='uniquetestemail@oregonstate.edu',
        is_admin=False
    )

    u.set_password("testpassword")

    db.session.add(u)
    db.session.commit()

    # login with valid user
    resp = test_client.post('/assistant-login',
        data={
            "username": "testuser",
            "password": "testpassword"
        },
        follow_redirects=True)

    resp = test_client.get('/changepass')
    html_prefail = """<form action="" method="post" novalidate>
        <input id="csrf_token" name="csrf_token" type="hidden" value="ImM2M2IzZGVkOTRjMDE3YWRjYTBmOTdjYzNkZTJkYjUwY2IyNWJkN2Ei.aYAOkw.fKGG4g6rSRi8DH5fZ8PVHpx7sOg">
        <p>
            <label for="username">Username</label><br>
            <input id="username" name="username" required size="32" type="text" value=""><br>
            
        </p>
        <p>
            <label for="old_password">Old Password</label><br>
            <input id="old_password" name="old_password" required size="32" type="password" value=""><br>
            
        </p>
        <p>
            <label for="password">New Password</label><br>
            <input id="password" name="password" required size="32" type="password" value=""><br>
            
        </p>
        <p>
            <label for="password2">Re-enter New Password</label><br>
            <input id="password2" name="password2" required size="32" type="password" value=""><br>
            
        </p>
        <p>
            <input id="submit" name="submit" type="submit" value="Change Password">
        </p>
        </form>"""
    assert html_prefail in resp.data.decode()

    # route to password page and send incorrect data like wrong username
    resp = test_client.post('/changepass',
        data={
            "username": "",
            "old_password": "",
            "new_password": "",
            "password2": ""
        },
        follow_redirects=True)

    html_postfail = """<form action="" method="post" novalidate>
        <input id="csrf_token" name="csrf_token" type="hidden" value="ImM2M2IzZGVkOTRjMDE3YWRjYTBmOTdjYzNkZTJkYjUwY2IyNWJkN2Ei.aYATNA.CyUy8OMX22M6D-_AcuCzif2b4Xc">
        <p>
            <label for="username">Username</label><br>
            <input id="username" name="username" required size="32" type="text" value=""><br>
            
                <span style="color: red;">[This field is required.]</span>
            
        </p>
        <p>
            <label for="old_password">Old Password</label><br>
            <input id="old_password" name="old_password" required size="32" type="password" value=""><br>
            
                <span style="color: red;">[This field is required.]</span>
            
        </p>
        <p>
            <label for="password">New Password</label><br>
            <input id="password" name="password" required size="32" type="password" value=""><br>
            
                <span style="color: red;">[This field is required.]</span>
            
        </p>
        <p>
            <label for="password2">Re-enter New Password</label><br>
            <input id="password2" name="password2" required size="32" type="password" value=""><br>
            
                <span style="color: red;">[This field is required.]</span>
            
        </p>
        <p>
            <input id="submit" name="submit" type="submit" value="Change Password">
        </p>
        </form>"""
    assert html_postfail in resp.data.decode()

from app.models import User
from app import db

def test_login_non_user(test_client):
    # send login data with form to login end point

    resp = test_client.post('/assistant-login',
        data={
            "username": "testuser",
            "password": "wrongpass"
        })

    # check page did not redirect
    assert 'Assistant Login' in resp.data.decode()

def test_failed_login(test_client):

    # send login data with incomplete form data
    resp = test_client.post(
    '/assistant-login',
    data={
        "username": "testuser",
        "password": ""
    },
    follow_redirects=True)

    html = resp.data.decode()

    fail_msg = '<span style="color: red;">[This field is required.]</span>'
    
    assert fail_msg in html

def test_login_existing_user(test_client):
    # create user with route
    u = User(
        username='testuser',
        email='uniquetestemail@oregonstate.edu',
        is_admin=False
    )

    u.set_password("testpassword")

    db.session.add(u)
    db.session.commit()


    # send login data with form to login end point
    resp = test_client.post('/assistant-login',
        data={
            "username": "testuser",
            "password": "testpassword"
        },
        follow_redirects=True)

    # verify success

    assert resp.status_code == 200

def test_login_homepage_change(test_client):
    # first check assistant link is not rendered

    # format is '<a href="/user/username">Profile</a>' for specific username
    assistant_link = '<a href="/user/testuser">Profile</a>'
    resp = test_client.get("/index")
    assert assistant_link not in resp.data.decode()

    # create user
    u = User(
        username='testuser',
        email='uniquetestemail@oregonstate.edu',
        is_admin=False
    )

    u.set_password("testpassword")

    db.session.add(u)
    db.session.commit()

    # login with valid user

    resp = test_client.post('/assistant-login',
        data={
            "username": "testuser",
            "password": "testpassword"
        },
        follow_redirects=True)

    # nav to home page, with assistant credentials this time
    resp = test_client.get("/index")

    # check that assistant link now renders
    assert assistant_link in resp.data.decode()

def test_password_change_missing_form(test_client):
    # create user
    u = User(
        username='testuser',
        email='uniquetestemail@oregonstate.edu',
        is_admin=False
    )

    u.set_password("testpassword")

    db.session.add(u)
    db.session.commit()

    # login with valid user
    resp = test_client.post('/assistant-login',
        data={
            "username": "testuser",
            "password": "testpassword"
        },
        follow_redirects=True)

    resp = test_client.get('/changepass')


    # route to password page and send incorrect data like wrong username
    resp = test_client.post('/changepass',
        data={
            "username": "",
            "old_password": "",
            "new_password": "",
            "password2": ""
        },
        follow_redirects=True)

    html_postfail = resp.data.decode().count('<span style="color: red;">[This field is required.]</span>')
    
    # check all 4 fields return an error
    assert html_postfail == 4

def test_password_change_success(test_client):
    # create user
    u = User(
        username='testuser',
        email='uniquetestemail@oregonstate.edu',
        is_admin=False
    )

    u.set_password("testpassword")

    db.session.add(u)
    db.session.commit()

    # login with valid user
    resp = test_client.post('/assistant-login',
        data={
            "username": "testuser",
            "password": "testpassword"
        },
        follow_redirects=True)
    

    resp = test_client.post('/changepass',
        data={
            "username": "testuser",
            "old_password": "testpassword",
            "password": "password",
            "password2": "password"
        },
        follow_redirects=True)

    html_res = 'Password updated successfully.'
    
    assert html_res in resp.data.decode()

#def test_next_ticket(test_client):
    # add 2 tickets to db
    # show that they show up in html
    # interact with a ticket
    # show the change in html
    #interact with ticket
    # show that there are no more left?

#def test_hardware_view(test_client):
    # add two entries to db
    # show that they show up in html