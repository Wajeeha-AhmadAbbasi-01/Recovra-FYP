def test_register_login_me(client, unique_email):
    reg = client.post(
        "/api/v1/auth/register",
        json={
            "business_name": "Test Traders",
            "full_name": "Test Owner",
            "email": unique_email,
            "password": "securepass123",
        },
    )
    assert reg.status_code == 201
    assert reg.json()["data"]["user"]["role"] == "owner"

    login = client.post("/api/v1/auth/login", json={"email": unique_email, "password": "securepass123"})
    assert login.status_code == 200
    assert client.cookies

    me = client.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert me.json()["data"]["user"]["email"] == unique_email


def test_duplicate_email_rejected(client, unique_email):
    payload = {
        "business_name": "Ab Co",
        "full_name": "Al Bo",
        "email": unique_email,
        "password": "securepass123",
    }
    assert client.post("/api/v1/auth/register", json=payload).status_code == 201
    assert client.post("/api/v1/auth/register", json={**payload, "business_name": "Other Co"}).status_code == 409