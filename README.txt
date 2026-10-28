KIKANDWA COMMUNITY SECONDARY SCHOOL — WEBSITE PACKAGE

This package preserves the existing website layout while changing the school identity, applying the green / white / yellow palette, and using selected photographs from the supplied KIKANDWA ASSETS ZIP. The supplied badge is included. Photos have been lightly corrected for contrast and colour; no heavy effects have been applied.

RUN LOCALLY ON WINDOWS
1. Install Python 3.11 or newer from https://www.python.org/downloads/windows/ and tick “Add Python to PATH”.
2. Extract this ZIP to a normal folder (do not run from inside the ZIP preview).
3. Double-click RUN_SCHOOL_WEBSITE.bat and keep the server window open.
4. Visit http://127.0.0.1:5000/ . Parent Portal: http://127.0.0.1:5000/portal.html . Admin: http://127.0.0.1:5000/admin.html .
5. If it fails, send the error shown in the black server window.

CURRENTLY IMPLEMENTED
- Responsive school pages and navigation.
- Parent registration, login, session sign-out, and password hashing.
- Admission applications with unique references and parent-specific tracking.
- Contact enquiries stored by the backend.
- Admin sign-in, viewing applications and enquiries, and updating admission status/notes.
- School photos and badge from the supplied asset ZIP, with mild image correction.
- Green / white / yellow theme while preserving the original page structure and layout.

ADMIN ACCOUNT SETUP
Set these environment variables before the first server run (use your own private values):
  set SECRET_KEY=use-a-long-random-secret-value
  set ADMIN_EMAIL=your-admin-email@example.com
  set ADMIN_PASSWORD=choose-a-unique-password-at-least-12-characters
Then run RUN_SCHOOL_WEBSITE.bat from the same Command Prompt. The admin account is created only if these variables are set and that email does not already exist. Do not share admin credentials.

IMPORTANT SCOPE LIMITS
The current backend manages admissions and contact enquiries. It does NOT yet contain real student grade/report-card, attendance, timetable, fee-payment, email verification, or password-reset services. Do not advertise those as active until the school supplies the authoritative records and those features are implemented. The parent registration flow creates a parent account, but student access must be linked to verified school records before using real student data.

ONLINE DEPLOYMENT
Static-only hosting cannot run this Flask backend. Deploy the complete folder to a Python-capable host, set SECRET_KEY, ADMIN_EMAIL, ADMIN_PASSWORD and COOKIE_SECURE=1 in the host environment, enable HTTPS, and configure persistent storage for DATABASE_PATH. Configure backups, CSRF protection, rate limiting, privacy notices, and retention/deletion rules before using real student information. Review the deployment for applicable Ugandan data-protection requirements.
