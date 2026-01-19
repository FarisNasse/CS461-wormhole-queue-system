def test_help_request_form(test_client):
    resp = test_client.get('/createticket')
    html = resp.data.decode()
    assert '<span style="color: red;">[This field is required.]</span>' not in html



    # test for error message displayed after post request with missing form data
    resp = test_client.post(
    '/createticket',
    data={
        "name": ""
    },
    follow_redirects=True)

    html = resp.data.decode()

    assert '<span style="color: red;">[This field is required.]</span>' in html
