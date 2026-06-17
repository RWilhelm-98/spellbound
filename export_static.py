import os
import sys
import shutil

# Add the spellbound_project directory to the Python path
project_dir = os.path.join(os.path.dirname(__file__), 'spellbound_project')
sys.path.append(project_dir)

# Set the Django settings module environment variable
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'spellbound_project.settings')

# Disable DJANGO_DEBUG and set a dummy secret key to simulate production if needed
os.environ['DJANGO_DEBUG'] = 'False'
os.environ['DJANGO_SECRET_KEY'] = 'netlify-export-dummy-key'

try:
    import django
    django.setup()
    from django.test import Client
    from django.core.management import call_command
except ImportError as e:
    print(f"Error importing Django. Make sure your virtual environment is active: {e}")
    sys.exit(1)

def export_static_site():
    print("Step 1: Running collectstatic to gather all assets...")
    # Gather static files
    call_command('collectstatic', '--noinput', clear=True, ignore_patterns=['input.css', '*.mjs'])

    print("\nStep 2: Rendering portfolio page...")
    client = Client()
    response = client.get('/')
    if response.status_code != 200:
        print(f"Error: Failed to render home page (Status: {response.status_code})")
        sys.exit(1)

    html_content = response.content.decode('utf-8')

    # Configure Netlify Forms (Optional integration)
    # This automatically adds Netlify attributes to our HTML form so Netlify collects form submissions!
    target_form_tag = '<form id="contact-form" class="space-y-6" method="POST" action="" enctype="multipart/form-data">'
    if target_form_tag in html_content:
        html_content = html_content.replace(
            target_form_tag,
            '<form id="contact-form" class="space-y-6" name="contact" method="POST" action="/" data-netlify="true" enctype="multipart/form-data">'
        )
        print("Integrated Netlify Forms into contact page form.")
    else:
        print("Warning: Contact form tag not found in html_content. Netlify Forms may not be configured properly.")


    # Create dist folder
    dist_dir = os.path.join(os.path.dirname(__file__), 'dist')
    if os.path.exists(dist_dir):
        shutil.rmtree(dist_dir)
    os.makedirs(dist_dir)

    # Write index.html
    index_path = os.path.join(dist_dir, 'index.html')
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"Wrote index.html to {index_path}")

    # Copy staticfiles folder to dist/static
    src_static_dir = os.path.join(project_dir, 'staticfiles')
    dst_static_dir = os.path.join(dist_dir, 'static')
    
    if os.path.exists(src_static_dir):
        shutil.copytree(src_static_dir, dst_static_dir)
        print(f"Copied static assets from {src_static_dir} to {dst_static_dir}")
    else:
        print(f"Error: staticfiles directory not found at {src_static_dir}")
        sys.exit(1)

    print("\nSuccess! Static site successfully generated in the 'dist' directory.")
    print("You can deploy the 'dist' folder directly to Netlify.")

if __name__ == '__main__':
    export_static_site()
