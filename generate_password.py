import bcrypt

password = "admin123"
salt = bcrypt.gensalt()
password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
print(f"Password hash for '{password}': {password_hash.decode('utf-8')}") 