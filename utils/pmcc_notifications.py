"""
PMCC Notification System
Send email and SMS alerts for assignment risk on short calls
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_email_alert(recipient_email, subject, body, risk_level='MODERATE'):
    """
    Send email alert for assignment risk
    
    Args:
        recipient_email: Email address to send to
        subject: Email subject
        body: Email body (HTML supported)
        risk_level: Risk level (CRITICAL, HIGH, MODERATE, LOW)
    
    Returns:
        dict: Success status and message
    """
    try:
        # Get SMTP credentials from environment
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        smtp_username = os.getenv('SMTP_USERNAME', '')
        smtp_password = os.getenv('SMTP_PASSWORD', '')
        sender_email = os.getenv('SMTP_FROM_EMAIL', smtp_username)
        
        if not smtp_username or not smtp_password:
            return {
                'success': False,
                'message': 'SMTP credentials not configured. Set SMTP_USERNAME and SMTP_PASSWORD in .env file.'
            }
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = sender_email
        msg['To'] = recipient_email
        
        # Add emoji based on risk level
        emoji_map = {
            'CRITICAL': '🚨',
            'HIGH': '⚠️',
            'MODERATE': '⚡',
            'LOW': '✅'
        }
        emoji = emoji_map.get(risk_level, '📊')
        
        # Create HTML body
        html_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px; }}
                .container {{ background-color: white; padding: 30px; border-radius: 10px; max-width: 600px; margin: 0 auto; }}
                .header {{ background: linear-gradient(135deg, #d4af37 0%, #f4e5b8 100%); padding: 20px; border-radius: 10px; margin-bottom: 20px; }}
                .header h1 {{ color: #1a1d23; margin: 0; font-size: 24px; }}
                .risk-badge {{ display: inline-block; padding: 8px 16px; border-radius: 5px; font-weight: bold; margin: 10px 0; }}
                .risk-critical {{ background-color: #ff4444; color: white; }}
                .risk-high {{ background-color: #ff9800; color: white; }}
                .risk-moderate {{ background-color: #ffc107; color: #1a1d23; }}
                .risk-low {{ background-color: #4caf50; color: white; }}
                .content {{ color: #333; line-height: 1.6; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{emoji} PMCC Assignment Risk Alert</h1>
                </div>
                <div class="risk-badge risk-{risk_level.lower()}">{risk_level} RISK</div>
                <div class="content">
                    {body}
                </div>
                <div class="footer">
                    <p>This is an automated alert from your Prosper Trading PMCC Dashboard.</p>
                    <p>Login to your dashboard to take action.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Attach HTML body
        html_part = MIMEText(html_body, 'html')
        msg.attach(html_part)
        
        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
        
        return {
            'success': True,
            'message': f'Email sent successfully to {recipient_email}'
        }
    
    except Exception as e:
        return {
            'success': False,
            'message': f'Email error: {str(e)}'
        }


def send_sms_alert(phone_number, message):
    """
    Send SMS alert via Twilio
    
    Args:
        phone_number: Phone number in E.164 format (e.g., +14155551234)
        message: SMS message text
    
    Returns:
        dict: Success status and message
    """
    try:
        # Get Twilio credentials from environment
        twilio_account_sid = os.getenv('TWILIO_ACCOUNT_SID', '')
        twilio_auth_token = os.getenv('TWILIO_AUTH_TOKEN', '')
        twilio_from_number = os.getenv('TWILIO_FROM_NUMBER', '')
        
        if not twilio_account_sid or not twilio_auth_token or not twilio_from_number:
            return {
                'success': False,
                'message': 'Twilio credentials not configured. Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_FROM_NUMBER in .env file.'
            }
        
        # Import Twilio (optional dependency)
        try:
            from twilio.rest import Client
        except ImportError:
            return {
                'success': False,
                'message': 'Twilio library not installed. Run: pip install twilio'
            }
        
        # Create Twilio client
        client = Client(twilio_account_sid, twilio_auth_token)
        
        # Send SMS
        sms = client.messages.create(
            body=message,
            from_=twilio_from_number,
            to=phone_number
        )
        
        return {
            'success': True,
            'message': f'SMS sent successfully to {phone_number}',
            'sid': sms.sid
        }
    
    except Exception as e:
        return {
            'success': False,
            'message': f'SMS error: {str(e)}'
        }


def send_assignment_risk_alert(risk_alerts, recipient_email=None, recipient_phone=None):
    """
    Send consolidated assignment risk alert via email and/or SMS
    
    Args:
        risk_alerts: List of risk alert dicts with symbol, strike, risk_level, message
        recipient_email: Email address (optional)
        recipient_phone: Phone number (optional)
    
    Returns:
        dict: Results of email and SMS sending
    """
    results = {
        'email': None,
        'sms': None
    }
    
    # Filter for high-priority alerts (CRITICAL or HIGH)
    high_priority = [a for a in risk_alerts if a['risk_level'] in ['CRITICAL', 'HIGH']]
    
    if not high_priority:
        return {
            'email': {'success': True, 'message': 'No high-priority alerts to send'},
            'sms': {'success': True, 'message': 'No high-priority alerts to send'}
        }
    
    # Build email body
    if recipient_email:
        email_body = "<h2>⚠️ Short Call Positions Requiring Attention</h2>"
        email_body += "<ul>"
        
        for alert in high_priority:
            email_body += f"""
            <li>
                <strong>{alert['symbol']} ${alert['strike']:.2f}</strong><br>
                Expiration: {alert['expiration']} ({alert['dte']} DTE)<br>
                Current Price: ${alert['current_price']:.2f}<br>
                <span style="color: {'red' if alert['risk_level'] == 'CRITICAL' else 'orange'};">
                    {alert['message']}
                </span>
            </li>
            """
        
        email_body += "</ul>"
        email_body += "<p><strong>Recommended Actions:</strong></p>"
        email_body += "<ul>"
        email_body += "<li>Consider rolling the short call to a higher strike or later expiration</li>"
        email_body += "<li>Close the short call if profit target is met</li>"
        email_body += "<li>Monitor closely as expiration approaches</li>"
        email_body += "</ul>"
        
        # Determine highest risk level
        highest_risk = 'CRITICAL' if any(a['risk_level'] == 'CRITICAL' for a in high_priority) else 'HIGH'
        
        results['email'] = send_email_alert(
            recipient_email,
            f"🚨 PMCC Assignment Risk Alert - {len(high_priority)} Position(s)",
            email_body,
            risk_level=highest_risk
        )
    
    # Build SMS message
    if recipient_phone:
        sms_message = f"🚨 PMCC Alert: {len(high_priority)} short call(s) at risk. "
        
        for alert in high_priority[:2]:  # Limit to 2 for SMS brevity
            sms_message += f"{alert['symbol']} ${alert['strike']:.2f} ({alert['risk_level']}). "
        
        sms_message += "Check dashboard for details."
        
        results['sms'] = send_sms_alert(recipient_phone, sms_message)
    
    return results


def get_notification_preferences():
    """
    Get notification preferences from environment variables
    
    Returns:
        dict: Email and phone preferences
    """
    return {
        'email': os.getenv('NOTIFICATION_EMAIL', ''),
        'phone': os.getenv('NOTIFICATION_PHONE', ''),
        'enabled': os.getenv('NOTIFICATIONS_ENABLED', 'false').lower() == 'true'
    }
