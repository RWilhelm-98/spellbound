from django.test import TestCase
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

class ContactFormTests(TestCase):
    def test_get_index_page(self):
        """GET request to the index page returns status 200."""
        response = self.client.get(reverse('spellbound_index'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'spellbound/index.html')

    def test_post_valid_contact_form(self):
        """POST request with valid form data sends an email to the correct recipient."""
        form_data = {
            'name': 'Gideon Gray',
            'email': 'gideon@archives.com',
            'genre': 'Fantasy',
            'word_count': '85000',
            'service': 'line',
            'message': 'This is a test story description.'
        }
        response = self.client.post(reverse('spellbound_index'), form_data)
        
        # Verify JSON response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')
        
        # Verify email was sent
        self.assertEqual(len(mail.outbox), 1)
        sent_email = mail.outbox[0]
        self.assertEqual(sent_email.subject, 'New Spellbound Inquiry from Gideon Gray')
        self.assertEqual(sent_email.to, ['rosevictoriawilhelm@gmail.com'])
        self.assertEqual(sent_email.reply_to, ['gideon@archives.com'])
        self.assertIn('Name: Gideon Gray', sent_email.body)
        self.assertIn('Email: gideon@archives.com', sent_email.body)
        self.assertIn('Genre/Field: Fantasy', sent_email.body)
        self.assertIn('Word Count: 85000', sent_email.body)
        self.assertIn('Service Tier: Line & Stylistic Editing', sent_email.body)
        self.assertIn('This is a test story description.', sent_email.body)

    def test_post_valid_contact_form_with_attachment(self):
        """POST request with an attached file correctly includes it in the sent email."""
        sample_file = SimpleUploadedFile(
            "sample_chapter.pdf",
            b"This is the content of the sample chapter.",
            content_type="application/pdf"
        )
        form_data = {
            'name': 'Harrow Nonagesimus',
            'email': 'harrow@tomb.com',
            'genre': 'Gothic Sci-Fi',
            'word_count': '5000',
            'service': 'dev',
            'message': 'Please review my short sample.',
            'sample_file': sample_file
        }
        response = self.client.post(reverse('spellbound_index'), form_data)
        
        # Verify JSON response
        self.assertEqual(response.status_code, 200)
        
        # Verify email was sent with attachment
        self.assertEqual(len(mail.outbox), 1)
        sent_email = mail.outbox[0]
        self.assertEqual(sent_email.to, ['rosevictoriawilhelm@gmail.com'])
        self.assertEqual(len(sent_email.attachments), 1)
        attachment = sent_email.attachments[0]
        self.assertEqual(attachment[0], 'sample_chapter.pdf')
        self.assertEqual(attachment[1], b"This is the content of the sample chapter.")
        self.assertEqual(attachment[2], 'application/pdf')

    def test_post_invalid_contact_form(self):
        """POST request with missing name or email returns status 400."""
        # Missing name
        form_data = {
            'email': 'gideon@archives.com',
            'message': 'No name provided'
        }
        response = self.client.post(reverse('spellbound_index'), form_data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['status'], 'error')
        self.assertEqual(len(mail.outbox), 0)

        # Missing email
        form_data = {
            'name': 'Gideon Gray',
            'message': 'No email provided'
        }
        response = self.client.post(reverse('spellbound_index'), form_data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['status'], 'error')
        self.assertEqual(len(mail.outbox), 0)

