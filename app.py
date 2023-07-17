from flask import Flask, render_template, request, redirect
import json
app = Flask(__name__)
app.debug = True

# File path for storing the account data
ACCOUNT_DATA_FILE = "account_data.json"

# Load the account data from the JSON file
def load_account_data():
    try:
        with open(ACCOUNT_DATA_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}
# Save the account data to the JSON file
def save_account_data():
    with open(ACCOUNT_DATA_FILE, "w") as file:
        json.dump(account_data, file)

# Load the account data when the server starts
account_data = load_account_data()

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/account', methods=['POST'])
def account():
    if request.method == 'POST':
        accno = request.form['accno']

        if len(accno) < 9 or len(accno) > 18:
            return render_template('error.html', message='Invalid account number. Account number should be between 9 and 18 digits.')

        if accno in account_data:
            return redirect('/options')
        else:
            # Account number is valid but not found in account_data
            # Add the new account to account_data and ask for further details
            return redirect(f'/save_account_details?accno={accno}')
    else:
        return render_template('error.html', message='Method Not Allowed')
    
@app.route('/save_account_details', methods=['GET', 'POST'])
def save_account_details():
    accno = request.args.get('accno')
    if request.method == 'POST':
        accno = request.form['accno']
        name = request.form['name']
        account_type = request.form['account_type']
        branch = request.form['branch']
        gmail = request.form['gmail']
        pin = request.form['pin']

        if len(accno) < 9 or len(accno) > 18 or not accno.isdigit():
            return render_template('error.html', message='Invalid account number')

        if accno in account_data:
            return render_template('error.html', message='Account already exists')

        # Add the new account to account_data dictionary
        account_data[accno] = {
            "name": name,
            "account_no": accno,
            "account_type": account_type,
            "total_balance": 10000,
            "branch": branch,
            "gmail": gmail,
            "pin": pin
        }
        save_account_data()
        return render_template('success.html', message='Account details saved successfully')

    return render_template('save_account_details.html',accno=accno)

@app.route('/options', methods=['GET'])
def options():
    return render_template('options.html')

@app.route('/withdraw', methods=['GET', 'POST'])
def withdraw():
    if request.method == 'POST':
        amount = int(request.form['amount'])
        accno = request.form['accno']
        pin = request.form['pin']  # Add the new PIN field
        if amount <= 0:
            return render_template('error.html', message='Invalid amount')
        if accno not in account_data:
            return render_template('error.html', message='Invalid account number')
        if pin != account_data[accno]['pin']:  # Check the PIN
            return render_template('error.html', message='Invalid PIN')
        if amount > account_data[accno]['total_balance']:
            return render_template('error.html', message='Insufficient balance')
        # Perform withdrawal logic here
        account_data[accno]['total_balance'] -= amount
        return render_template('success.html', message='Amount withdrawn successfully')
    return render_template('withdraw.html')

@app.route('/deposit', methods=['GET', 'POST'])
def deposit():
    if request.method == 'POST':
        amount = int(request.form['amount'])
        accno = request.form['accno']
        if amount <= 0:
            return render_template('error.html', message='Invalid amount')
        if accno not in account_data:
            return render_template('error.html', message='Invalid account number')
        # Perform deposit logic here
        account_data[accno]['total_balance'] += amount
        return render_template('success.html', message='Amount deposited successfully')
    return render_template('deposit.html')

@app.route('/transfer', methods=['GET', 'POST'])
def transfer():
    if request.method == 'POST':
        account_no = request.form['account_no']
        amount = int(request.form['amount'])
        accno = request.form['accno']
        if accno not in account_data:
            return render_template('error.html', message='Invalid account number')
        if account_no not in account_data:
            return render_template('error.html', message='Invalid destination account number')
        if amount <= 0:
            return render_template('error.html', message='Invalid amount')
        if amount > account_data[accno]['total_balance']:
            return render_template('error.html', message='Insufficient balance')
        # Perform transfer logic here
        account_data[accno]['total_balance'] -= amount
        account_data[account_no]['total_balance'] += amount
        return render_template('success.html', message='Amount transferred successfully')
    return render_template('transfer.html')

@app.route('/balance', methods=['GET', 'POST'])
def balance():
    if request.method == 'POST':
        accno = request.form['accno']
        if accno not in account_data:
            return render_template('error.html', message='Invalid account number')
        # Get account balance
        balance_amount = account_data[accno]['total_balance']
        return render_template('balance.html', accno=accno, balance=balance_amount)
    return render_template('balance.html')

@app.route('/pin_change', methods=['GET', 'POST'])
def pin_change():
    if request.method == 'POST':
        old_pin = request.form['old_pin']
        new_pin = request.form['new_pin']
        accno = request.form['accno']
        if accno not in account_data:
            return render_template('error.html', message='Invalid account number')
        if old_pin != account_data[accno]['pin']:
            return render_template('error.html', message='Incorrect old PIN')
        if old_pin == new_pin:
            return render_template('error.html', message='Old and new PINs cannot be the same')
        if len(new_pin) != 4 or not new_pin.isdigit():
            return render_template('error.html', message='Invalid new PIN')
        # Update PIN in account data
        account_data[accno]['pin'] = new_pin
        return render_template('success.html', message='PIN changed successfully')
    return render_template('pin_change.html')

@app.route('/account_info', methods=['GET', 'POST'])
def account_info():
    if request.method == 'POST':
        accno = request.form['accno']
        account_info = account_data.get(accno)
        
        if not account_info:
            return render_template('error.html', message='Invalid account number')
        return render_template('account_info.html', 
                               name=account_info['name'],
                               account_no=account_info['account_no'],
                               account_type=account_info['account_type'],
                               total_balance=account_info['total_balance'],
                               branch=account_info['branch'],
                               gmail=account_info['gmail'])
    return render_template('account_info.html')

@app.route('/exit', methods=['GET'])
def exit():
    return render_template('exit.html')

if __name__ == '__main__':
    app.run()
