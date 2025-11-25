import sqlite3
import time
import hashlib
from art import text2art
from utils import *


class BankingApplication:
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.current_user = None
        self.setup_database()

    def setup_database(self):
        try:
            self.conn = sqlite3.connect('banking_app.db')
            self.cursor = self.conn.cursor()

            # users table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_name TEXT NOT NULL,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    account_number TEXT UNIQUE NOT NULL,
                    balance REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # transactions table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    type TEXT NOT NULL,
                    amount REAL NOT NULL,
                    recipient_account TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')

            self.conn.commit()

        except sqlite3.Error as e:
            print(f" An error as occured in Database: {e}")

    def register_user(self):
        print("\n" + "="*10)
        print("CREATE A NEW ACCOUNT")
        print("="*10)

        # Get username and Validate
        while True:
            username = input("Enter username: ").strip()
            is_valid, message = validate_username(self.cursor, username)
            if is_valid:
                break
            print(message)

        # Get password and validation
        while True:
            password = getpass.getpass("Choose password: ").strip()
            is_valid, message = validate_password(password)
            if is_valid:
                break
            print(message)

        # Get full name and validation
        full_name = input("Enter your full name: ").strip()
        while len(full_name) < 4:
            print("Full name must be at least 4 characters")
            full_name = input("Enter your full name: ").strip()

        # initial deposit
        while True:
            try:
                deposit = float(input("Initial deposit (minimum ₦2000): ₦"))
                if deposit >= 2000:
                    break
                print("Minimum deposit is ₦2000")
            except ValueError:
                print("Please enter a valid number")

        # Account number Generation
        account_number = generate_account_number(self.cursor)
        hashed_password = hash_password(password)

        try:
            self.cursor.execute('''
                INSERT INTO users (full_name, username, password, account_number, balance)
                VALUES (?, ?, ?, ?, ?)
            ''', (full_name, username, hashed_password, account_number, deposit))

            self.conn.commit()

            print(f"\nAccount created successfully!")
            print(f"Your account number: {account_number}")
            print("You can now login")
            print("Thanks for choosen SQI Bank")
            time.sleep(3)

        except sqlite3.Error as e:
            print(f"Registration failed: {e}")
            self.conn.rollback()

    def login_user(self):
        print("\n" + "="*40)
        print("ACCOUNT LOGIN")
        print("="*40)

        username = input("Username: ").strip()
        password = getpass.getpass("Password: ").strip()

        if not username or not password:
            print("Username and password required")
            return False

        try:
            self.cursor.execute('''
                SELECT id, full_name, username, account_number, balance, password 
                FROM users WHERE username = ?
            ''', (username,))

            user = self.cursor.fetchone()

            if user and user[5] == hash_password(password):
                self.current_user = {
                    'id': user[0],
                    'full_name': user[1],
                    'username': user[2],
                    'account_number': user[3],
                    'balance': user[4]
                }
                print(f"\n Welcome back, {user[1]}!")
                time.sleep(1)
                return True
            else:
                print(" Invalid username or password")
                return False

        except sqlite3.Error as e:
            print(f"Login error: {e}")
            return False

    def deposit(self):
        print("\n" + "="*40)
        print("DEPOSIT MONEY")
        print("="*40)

        while True:
            amount_input = input("Enter amount to deposit: ₦").strip()

            if not amount_input:
                print("Amount cannot be empty")
                continue

            try:
                amount = float(amount_input)
                if amount <= 0:
                    print("Amount must be positive")
                    continue
                break
            except ValueError:
                print("Please enter a valid number")

        try:
            self.cursor.execute('''
                UPDATE users SET balance = balance + ? WHERE id = ?
            ''', (amount, self.current_user['id']))

            self.cursor.execute('''
                INSERT INTO transactions (user_id, type, amount) 
                VALUES (?, 'deposit', ?)
            ''', (self.current_user['id'], amount))

            self.conn.commit()
            self.current_user['balance'] += amount

            print(f"\nSuccessfully deposited ₦{amount:.2f}")
            print(f"New balance: ₦{self.current_user['balance']:.2f}")
            time.sleep(3)

        except sqlite3.Error as e:
            print(f"✗ Deposit failed: {e}")
            self.conn.rollback()

    def withdraw(self):
        print("\n" + "="*40)
        print("WITHDRAW MONEY")
        print("="*40)

        while True:
            amount_input = input("Enter amount to withdraw: ₦").strip()

            if not amount_input:
                print("Amount cannot be empty")
                continue

            try:
                amount = float(amount_input)
                if amount <= 0:
                    print("Amount must be positive")
                    continue

                if amount > self.current_user['balance']:
                    print("Insufficient funds!")
                    print(f"Your balance: ₦{self.current_user['balance']:.2f}")
                    continue

                break
            except ValueError:
                print("Please enter a valid number")

        try:
            self.cursor.execute('''
                UPDATE users SET balance = balance - ? WHERE id = ?
            ''', (amount, self.current_user['id']))

            self.cursor.execute('''
                INSERT INTO transactions (user_id, type, amount) 
                VALUES (?, 'withdrawal', ?)
            ''', (self.current_user['id'], amount))

            self.conn.commit()
            self.current_user['balance'] -= amount

            print(f"\n Successfully withdrew ₦{amount:.2f}")
            print(f" New balance: ₦{self.current_user['balance']:.2f}")
            time.sleep(3)

        except sqlite3.Error as e:
            print(f"Withdrawal failed: {e}")
            self.conn.rollback()

    def check_balance(self):
        print("\n" + "="*40)
        print("ACCOUNT BALANCE")
        print("="*40)
        print(f"Current balance: ₦{self.current_user['balance']:.2f}")
        time.sleep(2)

    def view_account_details(self):
        print("\n" + "="*40)
        print("ACCOUNT DETAILS")
        print("="*40)
        print(f"Full Name: {self.current_user['full_name']}")
        print(f"Username: {self.current_user['username']}")
        print(f"Account Number: {self.current_user['account_number']}")
        print(f"Balance: ₦{self.current_user['balance']:.2f}")
        time.sleep(5)

    def view_transaction_history(self):
        print("\n" + "="*40)
        print("TRANSACTION HISTORY")
        print("="*40)

        try:
            self.cursor.execute('''
                SELECT type, amount, recipient_account, timestamp 
                FROM transactions 
                WHERE user_id = ? 
                ORDER BY timestamp DESC
            ''', (self.current_user['id'],))

            transactions = self.cursor.fetchall()

            if not transactions:
                print("No transactions yet.")
            else:
                print(
                    f"{'Type':<12} {'Amount':<12} {'To/From':<12} {'Date/Time':<20}")
                print("-" * 60)

                for transaction in transactions:
                    trans_type, amount, recipient, timestamp = transaction
                    type_display = trans_type.replace('_', ' ').title()
                    amount_display = f"₦{amount:.2f}"
                    recipient_display = recipient if recipient else "Self"
                    print(
                        f"{type_display:<12} {amount_display:<12} {recipient_display:<12} {timestamp:<20}")

            time.sleep(5)

        except sqlite3.Error as e:
            print(f" Error loading transactions: {e}")

    def transfer_money(self):
        print("\n" + "="*40)
        print("TRANSFER MONEY")
        print("="*40)

        while True:
            recipient_account = input(
                "Enter recipient's 8-digit account number: ").strip()

            if not recipient_account:
                print("Account number cannot be empty")
                continue

            if recipient_account == self.current_user['account_number']:
                print("Self Transfer is not allowed")
                continue

            self.cursor.execute('''
                SELECT id, full_name FROM users WHERE account_number = ?
            ''', (recipient_account,))

            recipient = self.cursor.fetchone()

            if recipient:
                recipient_id, recipient_name = recipient
                print(f"Recipient Name: {recipient_name}")
                break
            else:
                print("Account number not found")

        while True:
            amount_input = input("Enter amount to transfer: ₦").strip()

            if not amount_input:
                print("Amount cannot be empty")
                continue

            try:
                amount = float(amount_input)
                if amount <= 0:
                    print("Amount must be positive")
                    continue

                if amount > self.current_user['balance']:
                    print("Insufficient funds!")
                    print(f"Your balance: ₦{self.current_user['balance']:.2f}")
                    continue

                break
            except ValueError:
                print("Please enter a valid number")

        try:
            self.cursor.execute('''
                UPDATE users SET balance = balance - ? WHERE id = ?
            ''', (amount, self.current_user['id']))

            self.cursor.execute('''
                UPDATE users SET balance = balance + ? WHERE account_number = ?
            ''', (amount, recipient_account))

            self.cursor.execute('''
                INSERT INTO transactions (user_id, type, amount, recipient_account) 
                VALUES (?, 'transfer_out', ?, ?)
            ''', (self.current_user['id'], amount, recipient_account))

            self.cursor.execute('''
                INSERT INTO transactions (user_id, type, amount, recipient_account) 
                VALUES (?, 'transfer_in', ?, ?)
            ''', (recipient_id, amount, self.current_user['account_number']))

            self.conn.commit()
            self.current_user['balance'] -= amount

            print(f"\n Transfer successful!")
            print(f" Sent ₦{amount:.2f} to account {recipient_account}")
            print(f"New balance: ₦{self.current_user['balance']:.2f}")
            time.sleep(2)

        except sqlite3.Error as e:
            print(f" Transfer failed: {e}")
            self.conn.rollback()

    def logout(self):
        print(f"\n Goodbye, {self.current_user['full_name']}!")
        print(" Thank you for banking with SQI Bank!")
        self.current_user = None
        time.sleep(2)

    def display_menu(self):
        while self.current_user:
            print("\n" + "="*50)
            print("BANKING APPLICATION - MAIN MENU")
            print("="*25)
            print(f"Welcome, {self.current_user['full_name']}!")
            print("="*25)
            print("1. Deposit Money")
            print("2. Withdraw Money")
            print("3. Check Balance")
            print("4. Transaction History")
            print("5. Transfer Money")
            print("6. Account Details")
            print("7. Logout")
            print("="*25)

            choice = input("Enter your choice (1-7): ")
            if choice == '1':
                self.deposit()
            elif choice == '2':
                self.withdraw()
            elif choice == '3':
                self.check_balance()
            elif choice == '4':
                self.view_transaction_history()
            elif choice == '5':
                self.transfer_money()
            elif choice == '6':
                self.view_account_details()
            elif choice == '7':
                self.logout()
            else:
                print("Invalid choice. Please enter 1-7.")
                time.sleep(1)

    def display_welcome_menu(self):
        while True:
            print("\n" + "="*25)
            print("WELCOME TO SQI BANK")
            print("="*25)
            print("1. Register New Account")
            print("2. Login")
            print("3. Exit")
            print("="*25)

            choice = input("Enter your choice (1-3): ")

            if choice == '1':
                self.register_user()
                print("\n Registration complete! Please login to continue.")
                self.login_user()
                if self.current_user:
                    self.display_menu()

            elif choice == '2':
                if self.login_user():
                    self.display_menu()

            elif choice == '3':
                print("\nThank you for banking with SQI Bank. Goodbye!")
                break
            else:
                print("Invalid choice. Please enter 1-3.")
                time.sleep(1)

    def run(self):
        print(text2art("SQI      Bank"))

        print("WELCOME TO SQI BANK...")
        time.sleep(1)

        self.display_welcome_menu()

        if self.conn:
            self.conn.close()


# if __name__ == "__main__":
app = BankingApplication()
app.run()

