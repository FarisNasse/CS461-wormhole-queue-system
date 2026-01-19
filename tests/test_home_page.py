## inner nav stuff for the home page

def test_submit_help(test_client):
    # check that submit help button renders
    resp = test_client.get("/")
    html = resp.data.decode()
    assert '<a href="/createticket">Submit a Help Request</a>' in html

def test_submit_help_page_load(test_client):
    # check submit help button route return successful
    resp = test_client.get("/createticket")
    assert resp.status_code == 200

def test_wa_log_in(test_client):
    # check that wormhole assistants log in button renders
    resp = test_client.get("/")
    html = resp.data.decode()
    assert '<a href="/createticket">Submit a Help Request</a>' in html

def test_wa_log_in_load(test_client):
    # check wormhole assistants log in button route return successful
    resp = test_client.get("/createticket")
    assert resp.status_code == 200

def test_live_queue(test_client):
    # check that live queue button renders
    resp = test_client.get("/")
    html = resp.data.decode()
    assert '<a href="/livequeue" style="color:#FFFFFF">Live Queue</a>' in html

def test_live_queue_load(test_client):
    # check live queue button route return successful
    resp = test_client.get("/livequeue")
    assert resp.status_code == 200

def test_user_log_in(test_client):
    # check user log in button renders
    resp = test_client.get("/")
    html = resp.data.decode()
    assert '<a href="/assistant-login" style="color:#FFFFFF">Log In</a>' in html

def test_user_log_in_load(test_client):
    # check user log in button route return successful
    resp = test_client.get("/assistant-login")
    assert resp.status_code == 200

def test_home(test_client):
    # check user log in button renders
    resp = test_client.get("/")
    html = resp.data.decode()
    assert '<a href="/index" style="color:#FFFFFF">Home</a>' in html

def test_home_load(test_client):
    # check user log in button route return successful
    resp = test_client.get("/index")
    assert resp.status_code == 200