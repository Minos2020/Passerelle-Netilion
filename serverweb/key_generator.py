import base64, os

def generate_key():
    return base64.urlsafe_b64encode(os.urandom(32)).decode()

print(f'FLASK_SESSION_KEY ="{generate_key()}"')
print(f'CONFIG_ENCRYPTION_KEY ="{generate_key()}"')