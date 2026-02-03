import random
import hashlib
import getpass


def validate_password(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters"

    has_upper = any(char.isupper() for char in password)
    has_lower = any(char.islower() for char in password)
    has_digit = any(char.isdigit() for char in password)

    if not (has_upper and has_lower and has_digit):
        return False, "Password must have atleast 1 Capital, lower and number"

    return True, "Strong password"


def generate_account_number(cursor):
    while True:
        account_number = "2" + str(random.randint(0000000, 9999999)).zfill(7)
        cursor.execute(
            "SELECT id FROM users WHERE account_number = ?", (account_number,))
        if not cursor.fetchone():
            return account_number


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def validate_username(cursor, username):
    if len(username) < 3 or len(username) > 20:
        return False, "Username must be 3-20 characters"

    if not username.replace("_", "").isalnum():
        return False, "Username can only contain letters, numbers, and underscores"

    cursor.execute(
        "SELECT id FROM users WHERE username = ?", (username,))
    if cursor.fetchone():
        return False, "Username already taken"

    return True, "Valid username"
