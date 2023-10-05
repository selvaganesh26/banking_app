import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Email configuration
sender_email = "selvaganeshmahadevan@gmail.com"
sender_password = "9841Selva@9841"
recipient_email = "selvaganeshmahadevan@gmail.com"
subject = "Message confirmation"
message = "hello daa losu"

# Create a MIMEMultipart object
msg = MIMEMultipart()
msg['From'] = sender_email
msg['To'] = recipient_email
msg['Subject'] = subject

# Attach the message to the MIMEMultipart object
msg.attach(MIMEText(message, 'plain'))

# SMTP server configuration
smtp_server = "smtp-mail.outlook.com"
smtp_port = 587

# Create an SMTP connection
try:
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()  # Enable TLS encryption

    # Login to your Outlook account
    server.login(sender_email, sender_password)

    # Send the email
    server.sendmail(sender_email, recipient_email, msg.as_string())

    print("Email sent successfully!")

except Exception as e:
    print(f"An error occurred: {str(e)}")

finally:
    # Quit the server
    server.quit()
