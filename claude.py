import sqlite3
import hashlib
import random
import time
import getpass
import re

# Database setup
def setup_database():
    """Create tables if they don't exist"""
    conn = sqlite3.connect('bank.db')
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            account_number TEXT UNIQUE NOT NULL,
            balance REAL NOT NULL
        )
    ''')
    
    # Transactions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            transaction_type TEXT NOT NULL,
            amount REAL NOT NULL,
            balance_after REAL NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            description TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Password hashing
def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

# Account number generator
def generate_account_number():
    """Generate unique 8-digit account number"""
    conn = sqlite3.connect('bank.db')
    cursor = conn.cursor()
    
    while True:
        account_num = str(random.randint(10000000, 99999999))
        cursor.execute('SELECT account_number FROM users WHERE account_number = ?', (account_num,))
        if not cursor.fetchone():
            conn.close()
            return account_num

# Validation functions
def validate_full_name(name):
    """Validate full name"""
    if not name or len(name.strip()) < 4 or len(name.strip()) > 255:
        return False, "Full name must be between 4 and 255 characters"
    if not re.match(r'^[A-Za-z\s]+$', name):
        return False, "Full name can only contain letters and spaces"
    return True, ""

def validate_username(username):
    """Validate username"""
    if not username or len(username) < 3 or len(username) > 20:
        return False, "Username must be between 3 and 20 characters"
    if not re.match(r'^[A-Za-z0-9_]+$', username):
        return False, "Username can only contain letters, numbers, and underscores"
    
    # Check if username already exists
    conn = sqlite3.connect('bank.db')
    cursor = conn.cursor()
    cursor.execute('SELECT username FROM users WHERE username = ?', (username,))
    if cursor.fetchone():
        conn.close()
        return False, "Username already exists"
    conn.close()
    return True, ""

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8 or len(password) > 30:
        return False, "Password must be between 8 and 30 characters"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    return True, ""

def validate_amount(amount_str, min_amount=0):
    """Validate amount input"""
    if not amount_str or amount_str.strip() == "":
        return False, "Amount cannot be empty"
    try:
        amount = float(amount_str)
        if amount <= min_amount:
            return False, f"Amount must be greater than {min_amount}"
        return True, amount
    except ValueError:
        return False, "Amount must be a valid number"

# User Registration
def register_user():
    """Register a new user"""
    print("\n=== USER REGISTRATION ===")
    
    # Full name
    while True:
        full_name = input("Enter your full name: ").strip()
        valid, msg = validate_full_name(full_name)
        if valid:
            break
        print(f"Error: {msg}")
    
    # Username
    while True:
        username = input("Enter username: ").strip()
        valid, msg = validate_username(username)
        if valid:
            break
        print(f"Error: {msg}")
    
    # Password
    while True:
        password = getpass.getpass("Enter password: ")
        valid, msg = validate_password(password)
        if valid:
            confirm_password = getpass.getpass("Confirm password: ")
            if password == confirm_password:
                break
            else:
                print("Error: Passwords do not match")
        else:
            print(f"Error: {msg}")
    
    # Initial deposit
    while True:
        deposit_str = input("Enter initial deposit (minimum 2000 naira): ")
        valid, result = validate_amount(deposit_str, min_amount=1999)
        if valid:
            initial_deposit = result
            break
        print(f"Error: {result}")
    
    # Generate account number
    account_number = generate_account_number()
    
    # Save to database
    conn = sqlite3.connect('bank.db')
    cursor = conn.cursor()
    hashed_pwd = hash_password(password)
    
    cursor.execute('''
        INSERT INTO users (full_name, username, password, account_number, balance)
        VALUES (?, ?, ?, ?, ?)
    ''', (full_name, username, hashed_pwd, account_number, initial_deposit))
    
    user_id = cursor.lastrowid
    
    # Record initial deposit transaction
    cursor.execute('''
        INSERT INTO transactions (user_id, transaction_type, amount, balance_after, description)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, 'DEPOSIT', initial_deposit, initial_deposit, 'Initial deposit'))
    
    conn.commit()
    conn.close()
    
    print("\n✓ Registration successful!")
    print(f"Your account number is: {account_number}")
    time.sleep(2)

# User Login
def login_user():
    """Login existing user"""
    print("\n=== USER LOGIN ===")
    
    username = input("Enter username: ").strip()
    if not re.match(r'^[A-Za-z0-9_]+$', username):
        print("Error: Invalid username format")
        time.sleep(1)
        return None
    
    password = getpass.getpass("Enter password: ")
    if not password or password.strip() == "":
        print("Error: Password cannot be empty")
        time.sleep(1)
        return None
    
    conn = sqlite3.connect('bank.db')
    cursor = conn.cursor()
    hashed_pwd = hash_password(password)
    
    cursor.execute('''
        SELECT id, full_name, account_number, balance 
        FROM users 
        WHERE username = ? AND password = ?
    ''', (username, hashed_pwd))
    
    user = cursor.fetchone()
    conn.close()
    
    if user:
        print("\n✓ Login successful!")
        time.sleep(1)
        return {
            'id': user[0],
            'name': user[1],
            'account_number': user[2],
            'balance': user[3]
        }
    else:
        print("Error: Invalid username or password")
        time.sleep(1)
        return None

# Deposit money
def deposit_money(user):
    """Deposit money into account"""
    print("\n=== DEPOSIT ===")
    
    amount_str = input("Enter amount to deposit: ")
    valid, result = validate_amount(amount_str)
    
    if not valid:
        print(f"Error: {result}")
        time.sleep(1)
        return
    
    amount = result
    
    conn = sqlite3.connect('bank.db')
    cursor = conn.cursor()
    
    # Update balance
    new_balance = user['balance'] + amount
    cursor.execute('UPDATE users SET balance = ? WHERE id = ?', (new_balance, user['id']))
    
    # Record transaction
    cursor.execute('''
        INSERT INTO transactions (user_id, transaction_type, amount, balance_after, description)
        VALUES (?, ?, ?, ?, ?)
    ''', (user['id'], 'DEPOSIT', amount, new_balance, 'Cash deposit'))
    
    conn.commit()
    conn.close()
    
    user['balance'] = new_balance
    print(f"\n✓ Deposit successful! New balance: ₦{new_balance:,.2f}")
    time.sleep(2)

# Withdraw money
def withdraw_money(user):
    """Withdraw money from account"""
    print("\n=== WITHDRAWAL ===")
    print(f"Available balance: ₦{user['balance']:,.2f}")
    
    amount_str = input("Enter amount to withdraw: ")
    valid, result = validate_amount(amount_str)
    
    if not valid:
        print(f"Error: {result}")
        time.sleep(1)
        return
    
    amount = result
    
    if amount > user['balance']:
        print("Error: Insufficient balance")
        time.sleep(1)
        return
    
    conn = sqlite3.connect('bank.db')
    cursor = conn.cursor()
    
    # Update balance
    new_balance = user['balance'] - amount
    cursor.execute('UPDATE users SET balance = ? WHERE id = ?', (new_balance, user['id']))
    
    # Record transaction
    cursor.execute('''
        INSERT INTO transactions (user_id, transaction_type, amount, balance_after, description)
        VALUES (?, ?, ?, ?, ?)
    ''', (user['id'], 'WITHDRAWAL', amount, new_balance, 'Cash withdrawal'))
    
    conn.commit()
    conn.close()
    
    user['balance'] = new_balance
    print(f"\n✓ Withdrawal successful! New balance: ₦{new_balance:,.2f}")
    time.sleep(2)

# Check balance
def check_balance(user):
    """Display current balance"""
    print("\n=== BALANCE INQUIRY ===")
    print(f"Current balance: ₦{user['balance']:,.2f}")
    time.sleep(2)

# Transaction history
def transaction_history(user):
    """Display transaction history"""
    print("\n=== TRANSACTION HISTORY ===")
    
    conn = sqlite3.connect('bank.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT transaction_type, amount, balance_after, timestamp, description
        FROM transactions
        WHERE user_id = ?
        ORDER BY timestamp DESC
    ''', (user['id'],))
    
    transactions = cursor.fetchall()
    conn.close()
    
    if not transactions:
        print("No transactions found")
    else:
        print(f"\n{'Type':<12} {'Amount':<15} {'Balance':<15} {'Date':<20} {'Description'}")
        print("-" * 80)
        for trans in transactions:
            trans_type, amount, balance, timestamp, desc = trans
            print(f"{trans_type:<12} ₦{amount:<14,.2f} ₦{balance:<14,.2f} {timestamp:<20} {desc}")
    
    time.sleep(3)

# Transfer money
def transfer_money(user):
    """Transfer money to another account"""
    print("\n=== TRANSFER ===")
    
    # Get recipient account number
    recipient_acc = input("Enter recipient account number: ").strip()
    
    if not recipient_acc.isdigit() or len(recipient_acc) != 8:
        print("Error: Invalid account number format")
        time.sleep(1)
        return
    
    if recipient_acc == user['account_number']:
        print("Error: Cannot transfer to your own account")
        time.sleep(1)
        return
    
    # Check if recipient exists
    conn = sqlite3.connect('bank.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, full_name FROM users WHERE account_number = ?', (recipient_acc,))
    recipient = cursor.fetchone()
    
    if not recipient:
        print("Error: Recipient account not found")
        conn.close()
        time.sleep(1)
        return
    
    recipient_id, recipient_name = recipient
    print(f"Recipient: {recipient_name}")
    
    # Get transfer amount
    amount_str = input("Enter amount to transfer: ")
    valid, result = validate_amount(amount_str)
    
    if not valid:
        print(f"Error: {result}")
        conn.close()
        time.sleep(1)
        return
    
    amount = result
    
    if amount > user['balance']:
        print("Error: Insufficient balance")
        conn.close()
        time.sleep(1)
        return
    
    # Perform transfer
    new_sender_balance = user['balance'] - amount
    cursor.execute('UPDATE users SET balance = ? WHERE id = ?', (new_sender_balance, user['id']))
    
    cursor.execute('UPDATE users SET balance = balance + ? WHERE id = ?', (amount, recipient_id))
    
    # Record transactions
    cursor.execute('''
        INSERT INTO transactions (user_id, transaction_type, amount, balance_after, description)
        VALUES (?, ?, ?, ?, ?)
    ''', (user['id'], 'TRANSFER OUT', amount, new_sender_balance, f'Transfer to {recipient_acc}'))
    
    cursor.execute('SELECT balance FROM users WHERE id = ?', (recipient_id,))
    recipient_balance = cursor.fetchone()[0]
    
    cursor.execute('''
        INSERT INTO transactions (user_id, transaction_type, amount, balance_after, description)
        VALUES (?, ?, ?, ?, ?)
    ''', (recipient_id, 'TRANSFER IN', amount, recipient_balance, f'Transfer from {user["account_number"]}'))
    
    conn.commit()
    conn.close()
    
    user['balance'] = new_sender_balance
    print(f"\n✓ Transfer successful! New balance: ₦{new_sender_balance:,.2f}")
    time.sleep(2)

# Account details
def account_details(user):
    """Display account details"""
    print("\n=== ACCOUNT DETAILS ===")
    print(f"Full Name: {user['name']}")
    print(f"Account Number: {user['account_number']}")
    print(f"Current Balance: ₦{user['balance']:,.2f}")
    time.sleep(2)

# Banking menu
def banking_menu(user):
    """Display banking operations menu"""
    while True:
        print("\n" + "="*40)
        print(f"Welcome, {user['name']}!")
        print("="*40)
        print("1. Deposit")
        print("2. Withdraw")
        print("3. Check Balance")
        print("4. Transaction History")
        print("5. Transfer Money")
        print("6. Account Details")
        print("7. Logout")
        print("="*40)
        
        choice = input("Enter your choice (1-7): ").strip()
        
        if choice == '1':
            deposit_money(user)
        elif choice == '2':
            withdraw_money(user)
        elif choice == '3':
            check_balance(user)
        elif choice == '4':
            transaction_history(user)
        elif choice == '5':
            transfer_money(user)
        elif choice == '6':
            account_details(user)
        elif choice == '7':
            print("\nLogging out...")
            time.sleep(1)
            break
        else:
            print("Error: Invalid choice. Please try again.")
            time.sleep(1)

# Main menu
def main_menu():
    """Display main menu"""
    while True:
        print("\n" + "="*40)
        print("   WELCOME TO SIMPLE BANK")
        print("="*40)
        print("1. Register")
        print("2. Login")
        print("3. Exit")
        print("="*40)
        
        choice = input("Enter your choice (1-3): ").strip()
        
        if choice == '1':
            register_user()
            # After registration, go to login
            user = login_user()
            if user:
                banking_menu(user)
        elif choice == '2':
            user = login_user()
            if user:
                banking_menu(user)
        elif choice == '3':
            print("\nThank you for using Simple Bank!")
            break
        else:
            print("Error: Invalid choice. Please try again.")
            time.sleep(1)

# Run the application
if __name__ == "__main__":
    setup_database()
    main_menu()