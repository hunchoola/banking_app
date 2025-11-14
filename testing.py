        # Get full name
full_name = input("Enter your full name: ").strip()
while len(full_name) < 4:
    print("Full name must be at least 4 characters")
    full_name = input("Enter your full name: ").strip()