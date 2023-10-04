from flask import Flask, render_template, request, redirect
import os
from dotenv import load_dotenv
import hashlib
import psycopg2
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
app = Flask(__name__)
app.debug = True

# Load environment variables from .env file
load_dotenv()
# Email configuration (SMTP server details)
email_sender = "selvaganesh2608@outlook.com"
email_password = "123456S@"
smtp_server = "smtp-mail.outlook.com"
smtp_port = 587  # Use the appropriate SMTP port for your email provider

# Initialize SMTP server
server = smtplib.SMTP(smtp_server, smtp_port)
server.starttls()
server.login(email_sender, email_password)

# Helper function to send email
def send_email(recipient_email, subject, body):
    # Initialize SMTP server
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(email_sender, email_password)
    msg = MIMEMultipart()
    msg['From'] = email_sender
    msg['To'] = recipient_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html'))

    try:
        server.sendmail(email_sender, recipient_email, msg.as_string())
        print("Email sent successfully!")
    except Exception as e:
        print(f"An error occurred while sending the email: {str(e)}")

# Database configuration
db_host = os.getenv('DB_HOST')
db_name = os.getenv('DB_NAME')
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_port = os.getenv('DB_PORT')

# Connect to the PostgreSQL database
conn = psycopg2.connect(host=db_host, database=db_name, user=db_user, password=db_password, port=db_port)
cursor = conn.cursor()
# Define the table name
table_name = os.getenv('TABLE_NAME')

def check_account_exist_in_db(accno):
    cursor.execute("SELECT * FROM banking_app.{} WHERE account_no = %s".format(table_name), (accno,))
    account_info = cursor.fetchone()
    print(account_info)
    return account_info
def validate_pin(account_data, provided_pin):
    hashed_provided_pin = hashlib.sha256(provided_pin.encode()).hexdigest()
    return hashed_provided_pin == account_data[6]


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/account', methods=['POST'])
def account():
    if request.method == 'POST':
        accno = request.form['accno']

        if len(accno) < 9 or len(accno) > 18:
            return render_template('error.html', message='Invalid account number. Account number should be between 9 and 18 digits.')
        try:
        # Check if the account exists in the database
            account_data = check_account_exist_in_db(accno)
        except psycopg2.Error as e:
            conn.rollback()
            print(str(e))
            return render_template('error.html', message='Error fetching account')
        if account_data:
            return redirect('/options')
        else:
            # Account number is valid but not found in the database
            # Redirect to the account details page
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
        
        # Hash the PIN before storing it in the database
        hashed_pin = hashlib.sha256(pin.encode()).hexdigest()
        # Create a new account in the database
        try:
            cursor.execute("""
                INSERT INTO banking_app.{} (account_no, name, account_type, branch, gmail, pin, total_balance)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """.format(table_name), (accno, name, account_type, branch, gmail, hashed_pin, 10000))
            conn.commit()
            return render_template('success.html', message='Account details saved successfully')
        except psycopg2.Error as e:
            conn.rollback()
            error_message = str(e)  # Convert the error to a string
            print("Error creating account:", error_message)  # Print the error message for debugging

            return render_template('error.html', message='Error creating account')
    else:
        if accno:
            return render_template('save_account_details.html', accno=accno)

@app.route('/options', methods=['GET'])
def options():
    return render_template('options.html')

@app.route('/withdraw', methods=['GET', 'POST'])
def withdraw():
    if request.method == 'POST':
        amount = int(request.form['amount'])
        accno = request.form['accno']
        pin = request.form['pin']  # Add the new PIN field
        account_data = check_account_exist_in_db(accno)  #will have tuple matching that account_number
        if amount <= 0:
            return render_template('error.html', message='Invalid amount')
        if not account_data:
            return render_template('error.html', message='Invalid account number')
        if not validate_pin(account_data, pin):  # Check the PIN
            return render_template('error.html', message='Invalid PIN')
        if amount > account_data[3]:
            return render_template('error.html', message='Insufficient balance')
        # Perform withdrawal logic here
        try:
            # Send withdrawal confirmation email
            new_balance = account_data[3] - amount
            recipient_email = account_data[7]  # Assuming the email is at index 7
            subject = "Withdrawal Confirmation"
            message = render_template('email_template.html', subject=subject, message=f'You have successfully withdrawn {amount} from your account (Account Number: {accno}). Your new balance is {new_balance}.')
            send_email(recipient_email, subject, message)

            cursor.execute("""UPDATE banking_app.{} SET total_balance = %s WHERE account_no = %s""".format(table_name), (new_balance, accno))
            conn.commit()           
            return render_template('success.html', message='Amount withdrawn successfully')
        except Exception as e:
            # Handle the exception and show an error message
            return render_template('error.html', message=f'Error in withdrawing amount: {str(e)}')
        finally:
            server.quit()  # Close the SMTP server connection

    return render_template('withdraw.html')

@app.route('/deposit', methods=['GET', 'POST'])
def deposit():
    if request.method == 'POST':
        amount = int(request.form['amount'])
        accno = request.form['accno']
        pin = request.form['pin']
        account_data = check_account_exist_in_db(accno)  #will have tuple matching that account_number
        if amount <= 0:
            return render_template('error.html', message='Invalid amount')
        if not account_data:
            return render_template('error.html', message='Invalid account number')
        if not validate_pin(account_data, pin):  # Check the PIN
            return render_template('error.html', message='Invalid PIN')
        # Performed deposit logic here
        new_balance = account_data[3] + amount
        try:
            cursor.execute("""UPDATE banking_app.{} SET total_balance = %s WHERE account_no = %s""".format(table_name), (new_balance, accno))
            conn.commit()
            return render_template('success.html', message='Amount deposited successfully')
        except psycopg2.Error as e:
            conn.rollback()
            return render_template('error.html', message='Error in depositing amount')
    return render_template('deposit.html')

@app.route('/transfer', methods=['GET', 'POST'])
def transfer():
    if request.method == 'POST':
        account_no = request.form['account_no']
        amount = int(request.form['amount'])
        accno = request.form['accno']
        pin = request.form['pin']
        account_data = check_account_exist_in_db(accno)  #will have tuple matching that account_number
        destination_account_data = check_account_exist_in_db(account_no)
        if not account_data:
            return render_template('error.html', message='Invalid account number')
        if not destination_account_data:
            return render_template('error.html', message='Invalid destination account number')
        if amount <= 0:
            return render_template('error.html', message='Invalid amount')
        if amount > account_data[3]:
            return render_template('error.html', message='Insufficient balance')
        if not validate_pin(account_data, pin):  # Check the PIN
            return render_template('error.html', message='Invalid PIN')
        # Perform transfer logic here
        debit_in_accno = account_data[3] - amount
        credit_in_account_no = destination_account_data[3] + amount
        try:
            cursor.execute("""UPDATE banking_app.{} SET total_balance = %s WHERE account_no = %s""".format(table_name), (debit_in_accno, accno))
            cursor.execute("""UPDATE banking_app.{} SET total_balance = %s WHERE account_no = %s""".format(table_name), (credit_in_account_no, account_no))
            conn.commit()
            return render_template('success.html', message='Amount transferred successfully')
        except psycopg2.Error as e:
            conn.rollback()
            return render_template('error.html', message='Error in transferring amount')
    return render_template('transfer.html')

@app.route('/balance', methods=['GET', 'POST'])
def balance():
    if request.method == 'POST':
        accno = request.form['accno']
        pin = request.form['pin']
        account_data = check_account_exist_in_db(accno)  #will have tuple matching that account_number
        if not account_data:
            return render_template('error.html', message='Invalid account number')
        # Get account balance
        if not validate_pin(account_data,pin):
            return render_template('error.html', message= 'Incorrect PIN')
        balance_amount = account_data[3]
        return render_template('balance.html', accno=accno, balance=balance_amount)
    return render_template('balance.html')

@app.route('/pin_change', methods=['GET', 'POST'])
def pin_change():
    if request.method == 'POST':
        old_pin = request.form['old_pin']
        new_pin = request.form['new_pin']
        accno = request.form['accno']
        account_data = check_account_exist_in_db(accno)
        if not account_data:
            return render_template('error.html', message='Invalid account number')
        if not validate_pin(account_data, old_pin):
            return render_template('error.html', message='Incorrect old PIN')
        if old_pin == new_pin:
            return render_template('error.html', message='Old and new PINs cannot be the same')
        if len(new_pin) != 4 or not new_pin.isdigit():
            return render_template('error.html', message='Invalid new PIN')
        new_hashed_pin = hashlib.sha256(new_pin.encode()).hexdigest()
        # Update PIN in account data
        try:
            cursor.execute("""UPDATE banking_app.{} SET pin = %s WHERE account_no = %s""".format(table_name), (new_hashed_pin, accno))
            conn.commit()
            return render_template('success.html', message='PIN changed successfully')
        except psycopg2.Error as e:
            conn.rollback()
            return render_template('error.html', message='Error in changing the password')
    return render_template('pin_change.html')

@app.route('/account_info', methods=['GET', 'POST'])
def account_info():
    if request.method == 'POST':
        accno = request.form['accno']
        account_data = check_account_exist_in_db(accno)
        if not account_data:
            return render_template('error.html', message='Invalid account number')
        return render_template('account_info.html', 
                               name=account_data[1],
                               account_no=account_data[0],
                               account_type=account_data[2],
                               total_balance=account_data[3],
                               branch=account_data[4],
                               gmail=account_data[5])
    return render_template('account_info.html')

@app.route('/exit', methods=['GET'])
def exit():
    return render_template('exit.html')

if __name__ == '__main__':
    app.run()
