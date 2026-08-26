"""
Security validation utilities for uploaded media and disaster reports.
Remediates SEC-005: Unrestricted File Upload vulnerabilities.
"""

import os
from rest_framework.exceptions import ValidationError

ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.mp4', '.mov', '.m4v', '.pdf'}
ALLOWED_MIME_TYPES = {
    'image/jpeg', 'image/png', 'image/webp',
    'video/mp4', 'video/quicktime', 'video/x-m4v',
    'application/pdf'
}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


def validate_uploaded_media(file_obj):
    """
    Validates user-uploaded disaster report attachments against strict security criteria:
    1. Maximum file size <= 10 MB
    2. Extension whitelist check (blocks .html, .svg, .py, .exe, .sh, etc.)
    3. Content-Type MIME whitelist check
    """
    if not file_obj:
        raise ValidationError("No file was provided for upload.")

    # 1. Check file size
    if file_obj.size > MAX_FILE_SIZE_BYTES:
        size_mb = round(file_obj.size / (1024 * 1024), 2)
        raise ValidationError(
            f"File size of {size_mb}MB exceeds maximum permitted limit of 10MB."
        )

    # 2. Check file extension
    ext = os.path.splitext(file_obj.name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(
            f"File extension '{ext}' is not permitted. "
            f"Allowed file types: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    # 3. Check Content-Type header if provided
    content_type = getattr(file_obj, 'content_type', '')
    if content_type and content_type.lower() not in ALLOWED_MIME_TYPES:
        raise ValidationError(
            f"File MIME type '{content_type}' is not supported or prohibited for security reasons."
        )

    return True
