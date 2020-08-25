import secrets

with open("apikey", 'w') as f:
    f.write(secrets.token_urlsafe(32))
