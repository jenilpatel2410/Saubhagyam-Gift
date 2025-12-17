import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings
import os
import logging
from .models import FCMTokenModel
import json
from django.db.models import Q

logger = logging.getLogger(__name__)

def initialize_firebase():
    """Initialize Firebase Admin SDK"""
    try:
        # Check if Firebase is already initialized
        app = firebase_admin.get_app()
        logger.info(f"Firebase already initialized with project ID: {app.project_id}")
        return app
    except ValueError:
        try:
            # Get the path to your Firebase service account key file
            # service_account_path = os.path.join(settings.BASE_DIR, 'config', 'firebase-credentials.json')
            service_account_path = settings.FIREBASE_CREDENTIALS_PATH
            
            # Read the service account key file
            with open(service_account_path, 'r') as f:
                service_account_info = json.load(f)
            
            # Log project details for verification
            project_id = service_account_info.get('project_id')
            # client_email = service_account_info.get('client_email')
            # logger.info(f"Initializing Firebase with project ID: {project_id}")
            # logger.info(f"Client email: {client_email}")
            
            # Initialize Firebase with your credentials
            cred = credentials.Certificate(service_account_info)
            app = firebase_admin.initialize_app(cred, {
                'projectId': project_id,
                'storageBucket': f"{project_id}.appspot.com"
            })
            logger.info(f"Firebase initialized successfully with project ID: {app.project_id}")
            return app
        except Exception as e:
            logger.error(f"Error initializing Firebase: {str(e)}")
            raise

def validate_token(token):
    """Validate a single FCM token"""
    try:
        # Initialize Firebase
        app = initialize_firebase()
        
        # Try to send a test message
        message = messaging.Message(
            data={'validate': 'true'},  # minimal harmless payload
            token=token
        )
        
        # Send the message
        response = messaging.send(message)
        # logger.info(f"Token validation successful: {response}")
        return True
        
    except Exception as e:
        error_message = str(e)
        logger.error(f"Token validation failed: {error_message}")
        
        if "Requested entity was not found" in error_message:
            logger.error("Token is not registered with Firebase")
            return False
        elif "SenderId mismatch" in error_message:
            logger.error("Token is from a different Firebase project")
            return False
        elif "Invalid registration token" in error_message:
            logger.error("Token is invalid or malformed")
            return False
        else:
            logger.error(f"Unknown error: {error_message}")
            return False

def get_fcm_tokens(customer_id, user_id):
    """Get all valid FCM tokens for a customer_id"""
    try:
        # Get all tokens for the customer_id
        tokens = list(FCMTokenModel.objects.filter(Q(user_id=customer_id) | Q(user_id=user_id)).values_list('token', flat=True))
        logger.info(f"Found {len(tokens)} tokens for Customer {customer_id}")

        # Validate each token
        valid_tokens = []
        for token in tokens:
            if validate_token(token):
                valid_tokens.append(token)
            else:
                # Remove invalid token
                FCMTokenModel.objects.filter(token=token).delete()
                logger.info(f"Removed invalid token: {token[:20]}...")
        
        return valid_tokens
    except Exception as e:
        logger.error(f"Error getting FCM tokens for Taluka {customer_id}: {str(e)}")
        return []

def send_notification(customer_id, title, body, data=None, user_id=None):
    """
    Send a notification to all FCM tokens associated with a customer_id.
    
    :param customer_id: The customer_id or object with a unique ID associated with FCM tokens
    :param title: Notification title
    :param body: Notification body
    :param data: Optional payload dictionary to include in the message
    :return: Dictionary with success and failure counts
    """
    try:
        app = initialize_firebase()
        # logger.info(f"[Firebase Init] Using Firebase project ID: {app.project_id}")
        
        tokens = get_fcm_tokens(customer_id, user_id)
        if not tokens:
            logger.warning(f"[FCM] No tokens found for customer_id ID: {customer_id}")
            return {'success_count': 0, 'failure_count': 0}
        
        success_count = 0
        failure_count = 0
        
        for token in tokens:
            if not token:
                continue  # Skip empty tokens
            
            try:
                image_url, video_url, news_id = '', '', ''
                if data:
                    image_url=data.get('image_url')
                    video_url=data.get('video_url')
                    news_id=data.get('news_id')
                message = messaging.Message(
                    notification=messaging.Notification(
                        title=title,
                        body=body,
                        # image=image_url,
                    ),
                    token=token,
                    webpush=messaging.WebpushConfig(
                        headers={'Urgency': 'high'},
                        notification=messaging.WebpushNotification(
                            title=title,
                            body=' ', #body,
                            icon='/static/images/logo.png',
                            badge='/static/images/badge.png'
                        )
                    ),
                    data=data or {}  # Add custom key-value data if provided
                )

                response = messaging.send(message)
                # logger.info(f"[FCM] Sent to token: {token[:20]}... (message ID: {response})")
                success_count += 1

            except Exception as e:
                error_msg = str(e)
                logger.error(f"[FCM Error] Token: {token[:20]}... - {error_msg}")
                failure_count += 1

                if "Requested entity was not found" in error_msg or "registration token is not a valid FCM registration token" in error_msg:
                    FCMTokenModel.objects.filter(token=token).delete()
                    logger.info(f"[FCM Cleanup] Removed invalid token: {token[:20]}...")

        logger.info(f"[FCM Summary] Success: {success_count}, Failures: {failure_count}")
        return {'success_count': success_count, 'failure_count': failure_count}

    except Exception as e:
        logger.exception(f"[FCM Fatal] Notification send failed: {str(e)}")
        return {'success_count': 0, 'failure_count': 0}


