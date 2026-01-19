def test_home(test_client):
    # check user log in button renders
    resp = test_client.get("/livequeue")
    html = resp.data.decode()
    assert '<a href="/index" style="color:#FFFFFF">Home</a>' in html

def test_home_load(test_client):
    # check user log in button route return successful
    resp = test_client.get("/index")
    assert resp.status_code == 200

def test_home(test_client):
    # check user log in button renders
    resp = test_client.get("/livequeue")
    html = resp.data.decode()
    assert '<a href="/livequeue" style="color:#FFFFFF">Live Queue</a>' in html

def test_home_load(test_client):
    # check user log in button route return successful
    resp = test_client.get("/livequeue")
    assert resp.status_code == 200

def test_user_log_in(test_client):
    # check user log in button renders
    resp = test_client.get("/livequeue")
    html = resp.data.decode()
    assert '<a href="/assistant-login" style="color:#FFFFFF">Log In</a>' in html

def test_user_log_in_load(test_client):
    # check user log in button route return successful
    resp = test_client.get("/assistant-login")
    assert resp.status_code == 200