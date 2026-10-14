import os
import uuid
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    """Checks if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file, upload_folder):
    """
    Validates and saves the uploaded image file securely.
    Returns the relative path to be saved in DB or raises ValueError.
    """
    if not file or file.filename == '':
        return None

    if not allowed_file(file.filename):
        raise ValueError("Invalid file type. Only PNG, JPG, JPEG, GIF are allowed.")

    original_name = secure_filename(file.filename)
    # Generate unique filename using uuid and original extension
    ext = original_name.rsplit('.', 1)[1].lower()
    unique_name = f"{uuid.uuid4().hex}.{ext}"

    # Ensure upload folder exists
    os.makedirs(upload_folder, exist_ok=True)
    
    file_path = os.path.join(upload_folder, unique_name)
    file.save(file_path)

    # Return relative URL route path (e.g. 'uploads/uuid.jpg')
    return f"uploads/{unique_name}"

def delete_file(file_path, upload_folder):
    """Deletes physical file from upload directory."""
    if not file_path:
        return
    # Strip leading 'uploads/' if exists in database record
    filename = file_path.replace('uploads/', '')
    full_path = os.path.join(upload_folder, filename)
    if os.path.exists(full_path):
        try:
            os.remove(full_path)
        except Exception:
            pass # Suppress delete error
