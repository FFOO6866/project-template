"""
Convert Netscape cookies.txt to Playwright JSON format
"""
import json
from datetime import datetime

# Read cookies.txt and extract horme.com.sg cookies
cookies_txt = """webmail.horme.com.sg	FALSE	/	TRUE	1792623187	roundcube_cookies	enabled
webmail.horme.com.sg	FALSE	/	FALSE	0	timezone	Asia/Shanghai
.horme.com.sg	TRUE	/	TRUE	0	ASP.NET_SessionId	c2wlff2egequaludfzuby4iw
.horme.com.sg	TRUE	/	TRUE	1761687219	browseHistory	1234|
www.horme.com.sg	FALSE	/	TRUE	0	BVImplmain_site	10666
.horme.com.sg	TRUE	/	FALSE	1795642420	_ga	GA1.1.1025216906.1761082420
.horme.com.sg	TRUE	/	TRUE	1792618419	BVBRANDID	1d3911ed-c007-4aa7-82c7-2b3242c5d91c
.horme.com.sg	TRUE	/	FALSE	1768858420	_fbp	fb.2.1761082420170.725214867909872808
.horme.com.sg	TRUE	/	FALSE	1768858421	_gcl_au	1.1.765785358.1761082421
webmail.horme.com.sg	FALSE	/	TRUE	0	webmailsession	integrum%40horme.com.sg%3a5XleS0lTzWBV679C%2c984abd68867b2d2b91c46c88232ee5dc
webmail.horme.com.sg	FALSE	/	TRUE	0	roundcube_sessid	b43762c2bcb2ab39f5734c43436e8832
.horme.com.sg	TRUE	/	TRUE	1761089257	BVBRANDSID	5ace3994-5983-40c6-93e8-35efe5364ee2
.horme.com.sg	TRUE	/	FALSE	1795647992	_ga_2DDE67D0LK	GS2.1.s1761087456$o2$g1$t1761087992$j50$l0$h774412165
webmail.horme.com.sg	FALSE	/	TRUE	0	roundcube_sessauth	Ze8AMEnCQBKbYJKhy2YHlLOnYPpwyrL6-1761088800"""

playwright_cookies = []

for line in cookies_txt.strip().split('\n'):
    parts = line.split('\t')
    if len(parts) >= 7:
        domain = parts[0]
        path = parts[2]
        secure = parts[3] == 'TRUE'
        expires = int(parts[4]) if parts[4] != '0' else -1
        name = parts[5]
        value = parts[6]

        cookie = {
            'name': name,
            'value': value,
            'domain': domain,
            'path': path,
            'expires': expires,
            'httpOnly': False,
            'secure': secure,
            'sameSite': 'None' if secure else 'Lax'
        }

        playwright_cookies.append(cookie)

session_data = {
    'cookies': playwright_cookies,
    'localStorage': {},
    'sessionStorage': {},
    'extracted_at': datetime.now().isoformat(),
    'validated': True  # User confirmed they're logged in
}

# Save to file
with open('horme_session.json', 'w') as f:
    json.dump(session_data, f, indent=2)

print("SUCCESS! Session file created: horme_session.json")
print(f"\nCookies extracted: {len(playwright_cookies)}")
print("\nKey cookies found:")
for cookie in playwright_cookies:
    if cookie['name'] in ['ASP.NET_SessionId', 'BVBRANDID', 'browseHistory']:
        print(f"  - {cookie['name']}: {cookie['value'][:50]}...")

print("\nReady to use for authenticated scraping!")
