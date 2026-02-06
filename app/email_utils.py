import boto3
import os
from flask import current_app, url_for
from botocore.exceptions import ClientError

def send_password_reset_email(user):
    """
    Sends a password reset email.
    - If ENABLE_AWS_SES is True: Sends via AWS SES.
    - If ENABLE_AWS_SES is False: Prints to console (for local testing).
    """
    # 1. Generate the secure token
    token = user.get_reset_password_token()
    
    # 2. Generate the link (External=True ensures it's a full https:// URL)
    reset_url = url_for('auth.reset_password', token=token, _external=True)

    # --- MODE A: Local Debugging (Console Print) ---
    if not current_app.config.get('ENABLE_AWS_SES'):
        print("\n" + "="*50)
        print(f"📧 [MOCK EMAIL] Password Reset Requested")
        print(f"👤 To: {user.email}")
        print(f"🔗 Link: {reset_url}")
        print("="*50 + "\n")
        return True

    # --- MODE B: AWS SES (Production) ---
    sender = current_app.config.get('SES_SENDER_EMAIL')
    aws_region = current_app.config.get('AWS_REGION')
    
    if not sender:
        current_app.logger.error("SES_SENDER_EMAIL not configured.")
        return False

    subject = "Password Reset Request - Wormhole Queue"
    body_text = f"Hello {user.username},\n\nTo reset your password, visit: {reset_url}\n\nIf you did not request this, please ignore this email."
    body_html = f"""
    <html>
    <body>
        <h3>Password Reset Request</h3>
        <p>Hello <b>{user.username}</b>,</p>
        <p>Click the link below to reset your password:</p>
        <p><a href="{reset_url}">Reset Password</a></p>
        <p>Or copy this link: {reset_url}</p>
    </body>
    </html>
    """

    try:
        # Boto3 will automatically look for AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY 
        # in the environment variables (which you set in .env).
        client = boto3.client('ses', region_name=aws_region)
        
        client.send_email(
            Source=sender,
            Destination={'ToAddresses': [user.email]},
            Message={
                'Subject': {'Data': subject},
                'Body': {
                    'Text': {'Data': body_text},
                    'Html': {'Data': body_html}
                }
            }
        )
        current_app.logger.info(f"Email sent to {user.email} via AWS SES.")
        return True
    except ClientError as e:
        current_app.logger.error(f"AWS SES Error: {e.response['Error']['Message']}")
        return False
    except Exception as e:
        current_app.logger.error(f"Unexpected Email Error: {e}")
        return False