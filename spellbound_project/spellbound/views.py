from django.shortcuts import render
from django.http import JsonResponse
from django.core.mail import EmailMessage
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# Create your views here.
def index(request):
    if request.method == 'POST':
        # Retrieve form data
        name = request.POST.get('name', '').strip()
        email_address = request.POST.get('email', '').strip()
        genre = request.POST.get('genre', '').strip()
        word_count = request.POST.get('word_count', '').strip()
        service_tier = request.POST.get('service', '').strip()
        message = request.POST.get('message', '').strip()
        sample_file = request.FILES.get('sample_file')

        # Translate service tier code to human-readable label
        service_labels = {
            'dev': 'Developmental Editing',
            'line': 'Line & Stylistic Editing',
            'copy': 'Copy & Proofreading',
            'format': 'Book Formatting',
            'custom': 'Other / Custom Bundle'
        }
        service_name = service_labels.get(service_tier, service_tier or 'Not specified')

        # Validation
        if not name or not email_address:
            return JsonResponse({'status': 'error', 'message': 'Name and Email are required fields.'}, status=400)

        # Build email content
        subject = f"New Spellbound Inquiry from {name}"
        email_body = f"""New Inquiry Received from the Spellbound Website

Name: {name}
Email: {email_address}
Genre/Field: {genre or 'Not specified'}
Word Count: {word_count or 'Not specified'}
Service Tier: {service_name}

Project Description:
--------------------
{message or 'No description provided.'}
"""

        try:
            # Create EmailMessage
            email = EmailMessage(
                subject=subject,
                body=email_body,
                from_email=settings.DEFAULT_FROM_EMAIL or 'noreply@spellboundedit.com',
                to=['rosevictoriawilhelm@gmail.com'],
                reply_to=[email_address],
            )

            # Attach sample chapter if provided
            if sample_file:
                email.attach(sample_file.name, sample_file.read(), sample_file.content_type)

            email.send()
            return JsonResponse({'status': 'success', 'message': 'Your email has been sent! We will contact you shortly.'})
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return JsonResponse({
                'status': 'error',
                'message': 'There was a problem sending your message. Please try again later or contact us directly.'
            }, status=500)

    return render(request, 'spellbound/index.html')
