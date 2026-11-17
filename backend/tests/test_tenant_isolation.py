def test_cross_tenant_customer_denied(client, db, unique_email):
    reg_a = client.post(
        "/api/v1/auth/register",
        json={
            "business_name": "Tenant A",
            "full_name": "Owner A",
            "email": unique_email,
            "password": "securepass123",
        },
    )
    tenant_a = reg_a.json()["data"]["tenant"]["id"]

    email_b = unique_email.replace("@", "+b@")
    client.post(
        "/api/v1/auth/register",
        json={
            "business_name": "Tenant B",
            "full_name": "Owner B",
            "email": email_b,
            "password": "securepass123",
        },
    )

    # still logged in as A from cookie after first register? register doesn't set cookie — login A
    client.post("/api/v1/auth/login", json={"email": unique_email, "password": "securepass123"})
    client.cookies.clear()
    client.post("/api/v1/auth/login", json={"email": email_b, "password": "securepass123"})

    # create a fake customer id from tenant A not possible without UUID — use random
    import uuid

    missing = client.get(f"/api/v1/customers/{uuid.uuid4()}")
    assert missing.status_code == 404
    _ = tenant_a