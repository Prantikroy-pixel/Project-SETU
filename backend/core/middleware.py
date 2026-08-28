"""
Custom Security Headers Middleware for SETU Platform (SEC-010).
Remediates all OWASP A05:2021 Security Misconfigurations flagged by SentinelScan.
"""

class SecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # 1. Content-Security-Policy (CSP) (CWE-693 / OWASP A05:2021)
        response['Content-Security-Policy'] = (
            "default-src 'self' https: data: blob: 'unsafe-inline' 'unsafe-eval'; "
            "img-src 'self' https: data: blob:; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com data:; "
            "connect-src 'self' https: wss:;"
        )

        # 2. X-Content-Type-Options (MIME-sniffing defense) (CWE-693)
        response['X-Content-Type-Options'] = 'nosniff'

        # 3. X-Frame-Options (Clickjacking defense) (CWE-1021)
        response['X-Frame-Options'] = 'DENY'

        # 4. Referrer-Policy (Information Leakage defense) (CWE-200)
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # 5. Permissions-Policy (Feature restriction) (CWE-693)
        response['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=(self), payment=()'

        # 6. Cross-Origin-Opener-Policy (Spectre/Side-Channel defense) (CWE-693)
        response['Cross-Origin-Opener-Policy'] = 'same-origin-allow-popups'

        # 7. Cross-Origin-Resource-Policy (Embedding protection) (CWE-693)
        response['Cross-Origin-Resource-Policy'] = 'same-site'

        # 8. Strict-Transport-Security (HSTS) (CWE-523)
        response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'

        return response
