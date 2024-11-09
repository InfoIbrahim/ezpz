from django.shortcuts import render, redirect
from django.contrib import messages
import json


# Hard-coded usernames, passwords, and client IDs
user_data = {
    "Willem Sytsma": {"password": "walkwalkwalk", "client_id": "000000000000000"},
    "Mariyeh Saeidi": {"password": "willsbaby", "client_id": "000000000000001"},
    "Norma Graham": {"password": "willsmom", "client_id": "000000000000002"},
    "Admin": {"password": "Spyagent3865", "client_id": "999999999999999"}  # Admin user added
}


# Load data from the JSON file
def load_data():
    try:
        with open('data.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"IHB_values": {}, "users": [], "transactions": []}


# Save data back to the JSON file
def save_data(data):
    with open('data.json', 'w') as f:
        json.dump(data, f, indent=4)


# User class handles user actions like logging in, checking balances, etc.
class User:
    def __init__(self, client_id, name, password, IHB_ownership, transaction_history):
        self.client_id = client_id
        self.name = name
        self.password = password
        self.IHB_ownership = IHB_ownership
        self.transaction_history = transaction_history
        self.active = False  # Tracks if the user is logged in


    def log_in(self):
        self.active = True


    def log_out(self):
        self.active = False


    def check_balance(self, IHB_number, IHB_values):
        """Check balance for a IHB."""
        IHB_value = IHB_values.get(f"IHB_{IHB_number}")
        if not IHB_value:
            return f"IHB {IHB_number} not found."
       
        total_percentage = 0
        for ownership in self.IHB_ownership:
            if ownership['IHB_number'] == IHB_number:
                total_percentage += ownership['percentage']
       
        total_balance = (total_percentage / 100) * IHB_value
        return f"User {self.client_id} owns {total_percentage}% of IHB {IHB_number}, which is worth ${total_balance:.2f}."


    def add_transaction(self, transaction):
        """Add a transaction to the user's history."""
        self.transaction_history.append(transaction)


# This function loads the data and initializes users and IHB values
def get_users_and_IHB_values():
    data = load_data()
    IHB_values = data['IHB_values']
    users_data = data['users']


    # Create User objects
    users = [
        User(
            user['client_id'],
            next((name for name, details in user_data.items() if details['client_id'] == user['client_id']), "Unknown"),
            user_data[next((name for name, details in user_data.items() if details['client_id'] == user['client_id']), "Unknown")]['password'],
            user['IHB_ownership'],
            user['transaction_history']
        ) for user in users_data
    ]
   
    return users, IHB_values


# Login view
def login(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')


        # Fetch the list of users and check if the entered credentials are valid
        users, _ = get_users_and_IHB_values()  # This fetches the list of users
        user = next((u for u in users if u.name == username), None)


        if user and user.password == password:  # If user exists and password matches
            user.log_in()  # Log the user in
            request.session['client_id'] = user.client_id  # Set session with client_id
            return redirect('dashboard')  # Redirect to the dashboard


        else:
            messages.error(request, "Invalid username or password.")  # Show error message if credentials are incorrect


    return render(request, 'login.html')  # Render the login page when GET request is made


#Start EDIT FOR November 8, 2024
# View for the dashboard (user actions after login)
def dashboard(request):
    # Check if the user is logged in by session
    client_id = request.session.get('client_id')
    if not client_id:
        return redirect('login')  # Redirect to the login page if not logged in

    # Load data and find the current user
    users, IHB_values = get_users_and_IHB_values()
    user = next((u for u in users if u.client_id == client_id), None)

    if user is None:
        # This should never happen if session management is correct, but we handle it just in case
        return redirect('login')  # If the user isn't found, redirect to login
    
    terminal_output = ""
    transfer_form_data = {
        'recipient': '',
        'IHB_number': '',
        'amount': ''
    }
    
    if request.method == "POST":
        command = request.POST.get('command', '').strip()

        if command == "logout":
            user.log_out()
            request.session.flush()
            terminal_output = "Logged out successfully."
            return redirect('login')

        elif command == "balance":
            # Ensure IHB_number is provided and valid
            try:
                IHB_number = int(request.POST.get('IHB_number', 1))  # Default to IHB 1 if not provided
                terminal_output = user.check_balance(IHB_number, IHB_values)
            except ValueError:
                terminal_output = "Invalid IHB number provided."

        elif command == "transfer":
            recipient_name = request.POST.get('recipient')
            IHB_number = request.POST.get('IHB_number')
            amount = request.POST.get('amount')

            # Validate that all fields are provided
            if not recipient_name or not IHB_number or not amount:
                terminal_output = "Please fill out all fields for the transfer."
                transfer_form_data = {
                    'recipient': recipient_name,
                    'IHB_number': IHB_number,
                    'amount': amount
                }
                return render(request, 'dashboard.html', {
                    'user': user,
                    'IHB_values': IHB_values,
                    'terminal_output': terminal_output,
                    'transfer_form_data': transfer_form_data
                })

            # Convert values to proper types
            try:
                IHB_number = int(IHB_number)
                amount = float(amount)
            except ValueError:
                terminal_output = "Invalid IHB number or amount."
                return render(request, 'dashboard.html', {
                    'user': user,
                    'IHB_values': IHB_values,
                    'terminal_output': terminal_output,
                    'transfer_form_data': transfer_form_data
                })

            # Find recipient user
            recipient = next((u for u in users if u.name == recipient_name), None)

            if recipient and recipient != user:  # Make sure the recipient exists and isn't the same user
                # Find sender's ownership and adjust percentage
                IHB_value = IHB_values.get(f"IHB_{IHB_number}")
                if not IHB_value:
                    terminal_output = "Invalid IHB number."
                    return render(request, 'dashboard.html', {
                        'user': user,
                        'IHB_values': IHB_values,
                        'terminal_output': terminal_output,
                        'transfer_form_data': transfer_form_data
                    })

                # Check if the user has 0% ownership of the specified IHB
                ownership_found = False
                for ownership in user.IHB_ownership:
                    if ownership['IHB_number'] == IHB_number:
                        ownership_found = True
                        if ownership['percentage'] == 0:
                            terminal_output = f"You cannot transfer IHB_{IHB_number} because you have 0% ownership."
                            return render(request, 'dashboard.html', {
                                'user': user,
                                'IHB_values': IHB_values,
                                'terminal_output': terminal_output,
                                'transfer_form_data': transfer_form_data
                            })
                        break

                if not ownership_found:
                    terminal_output = "You do not own the specified IHB."
                    return render(request, 'dashboard.html', {
                        'user': user,
                        'IHB_values': IHB_values,
                        'terminal_output': terminal_output,
                        'transfer_form_data': transfer_form_data
                    })

                # Check if the transfer amount exceeds the value the user owns
                user_owned_value = 0
                for ownership in user.IHB_ownership:
                    if ownership['IHB_number'] == IHB_number:
                        user_owned_value = (ownership['percentage'] / 100) * IHB_value
                        break

                if amount > user_owned_value:
                    terminal_output = f"You cannot transfer more than the value you own. You only own {user_owned_value:.2f} USD worth of IHB_{IHB_number}."
                    return render(request, 'dashboard.html', {
                        'user': user,
                        'IHB_values': IHB_values,
                        'terminal_output': terminal_output,
                        'transfer_form_data': transfer_form_data
                    })

                # Calculate the percentage to transfer based on the amount
                transfer_percentage = (amount / IHB_value) * 100

                # Deduct ownership from the sender (user)
                for ownership in user.IHB_ownership:
                    if ownership['IHB_number'] == IHB_number:
                        ownership['percentage'] -= transfer_percentage
                        break

                # Add ownership to the recipient
                recipient_ownership = next((o for o in recipient.IHB_ownership if o['IHB_number'] == IHB_number), None)
                if recipient_ownership:
                    recipient_ownership['percentage'] += transfer_percentage
                else:
                    recipient.IHB_ownership.append({'IHB_number': IHB_number, 'percentage': transfer_percentage})

                # Record the transaction
                transaction = {
                    'sender': user.client_id,
                    'recipient': recipient.client_id,
                    'amount': amount,
                    'IHB_number': IHB_number
                }
                user.add_transaction(transaction)
                recipient.add_transaction(transaction)

                # Save data
                save_data({
                    "IHB_values": IHB_values,
                    "users": [{
                        "client_id": u.client_id,
                        "IHB_ownership": u.IHB_ownership,
                        "transaction_history": u.transaction_history
                    } for u in users],
                    "transactions": []
                })

                terminal_output = f"Transferred {amount} USD to {recipient_name}."
            else:
                terminal_output = "Recipient not found or invalid transaction."

        else:
            terminal_output = f"Unknown command: {command}"

    return render(request, 'dashboard.html', {
        'user': user,
        'IHB_values': IHB_values,
        'terminal_output': terminal_output,
        'transfer_form_data': transfer_form_data  # Pass the form data back to template
    })
#STOP EDIT FOR NOVEMBER 8, 2024
from django.shortcuts import redirect


def logout_view(request):
    """Log the user out and redirect to the login page."""
    request.session.flush()  # Clear the session
    return redirect('login')  # Redirect to login page

# Admin Dashboard view
def admin_dashboard(request):
    # Only allow access to the admin user
    client_id = request.session.get('client_id')
    if not client_id:
        return redirect('login')  # Redirect to login if not logged in


    # Load data and find the admin user
    users, IHB_values = get_users_and_IHB_values()


    # Check if the logged-in user is the admin
    admin_user = next((u for u in users if u.client_id == "999999999999999"), None)
    if not admin_user or client_id != admin_user.client_id:
        return redirect('login')  # Redirect to login if not the admin


    # Prepare the data to display on the Admin Dashboard
    all_IHB_ownerships = []
    for user in users:
        for ownership in user.IHB_ownership:
            IHB_number = ownership['IHB_number']
            percentage = ownership['percentage']
            IHB_value = IHB_values.get(f"IHB_{IHB_number}", 0)
            total_value = (percentage / 100) * IHB_value
            all_IHB_ownerships.append({
                'user': user.name,
                'client_id': user.client_id,
                'IHB_number': IHB_number,
                'percentage': percentage,
                'value': total_value
            })


    return render(request, 'admin_dashboard.html', {
        'IHB_ownerships': all_IHB_ownerships,
        'IHB_values': IHB_values
    })
def login(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')


        # Fetch the list of users and check if the entered credentials are valid
        users, _ = get_users_and_IHB_values()  # This fetches the list of users
        user = next((u for u in users if u.name == username), None)


        if user and user.password == password:  # If user exists and password matches
            user.log_in()  # Log the user in
            request.session['client_id'] = user.client_id  # Set session with client_id
            if user.client_id == "999999999999999":  # If the user is admin
                return redirect('admin_dashboard')  # Redirect to the admin dashboard
            return redirect('dashboard')  # Redirect to the regular dashboard


        else:
            messages.error(request, "Invalid username or password.")  # Show error message if credentials are incorrect


    return render(request, 'login.html')  # Render the login page when GET request is made

#Added November 9, 2024 for Ledger View (nfc_data+.json to django)
from django.shortcuts import render
from django.http import HttpResponseNotFound
from django.contrib.auth.decorators import login_required
import json
import os

# Apply the login_required decorator to restrict access
@login_required
def ledger_view(request):
    # Define the path to your nfc_data+.json file
    json_file_path = 'my_django_project/nfc_data+.json'  # Update this path to the actual file location

    try:
        # Open and read the JSON file
        if os.path.exists(json_file_path):
            with open(json_file_path, 'r') as file:
                nfc_data = json.load(file)
        
            # Pass the data to the template for rendering
            return render(request, 'ledger/ledger_view.html', {'nfc_data': nfc_data})

        else:
            return HttpResponseNotFound("Error: The NFC data file was not found.")
    
    except FileNotFoundError:
        # Handle file not found exception (redundant, as we already check if the file exists)
        return HttpResponseNotFound("Error: The NFC data file was not found.")
    except json.JSONDecodeError:
        # Handle JSON decoding errors if the file content is invalid
        return HttpResponseNotFound("Error: The NFC data file is not a valid JSON file.")





#must be consolidated: USD to Gold Fluctuation, active data file(json)
#USD to Gold fluctuation:
# userbuys IHB at market price
# physical commodity asset is acquired
# exiting terms assuming one would exit when market gold volatility > 100% of client purchase price
# Ibrahim takes 5% as exit fee from 100% of the volatility increase
# Example:
# volatility increase is 2% from $100,000 USD purchase price, $2000USD capital gain - 10% Ibrahim Exit Fee = $1800.00 USD capital gain ++ $200.00 USD Ibrahim exit fee