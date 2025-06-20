import bcrypt

passwords = ["superadmin123", "admin123", "user123"]
salt = bcrypt.gensalt()

for password in passwords:
    password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
    print(f"Password hash for '{password}': {password_hash.decode('utf-8')}") 