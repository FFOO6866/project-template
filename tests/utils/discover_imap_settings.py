"""
IMAP Settings Discovery Tool
Tries common IMAP server configurations for horme.com.sg
NO MOCK - Tests actual servers
"""

import sys
from imapclient import IMAPClient
import socket

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# ANSI colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def test_imap_server(server, port, use_ssl, username, password):
    """Test a specific IMAP configuration"""
    print(f"\n{BLUE}Testing:{RESET} {server}:{port} (SSL={use_ssl})")

    try:
        # Test TCP connection first
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((server, port))
        sock.close()

        if result != 0:
            print(f"  {RED}✗ Cannot connect to port{RESET}")
            return False

        print(f"  {GREEN}✓ Port is reachable{RESET}")

        # Try IMAP connection
        client = IMAPClient(
            server,
            port=port,
            use_uid=True,
            ssl=use_ssl,
            timeout=10
        )
        print(f"  {GREEN}✓ IMAP client created{RESET}")

        # Try authentication
        try:
            client.login(username, password)
            print(f"  {GREEN}✓ Login successful!{RESET}")

            # Get server capabilities
            capabilities = client.capabilities()
            print(f"  {GREEN}✓ Server capabilities: {len(capabilities)}{RESET}")

            # Try selecting INBOX
            client.select_folder("INBOX")
            print(f"  {GREEN}✓ INBOX accessible{RESET}")

            client.logout()

            print(f"\n{GREEN}{'='*60}{RESET}")
            print(f"{GREEN}✓ WORKING CONFIGURATION FOUND!{RESET}")
            print(f"{GREEN}{'='*60}{RESET}")
            print(f"Server: {server}")
            print(f"Port: {port}")
            print(f"SSL: {use_ssl}")
            print(f"Username: {username}")
            print(f"{GREEN}{'='*60}{RESET}")

            return True

        except Exception as e:
            print(f"  {YELLOW}⊘ Authentication failed: {e}{RESET}")
            return False

    except socket.gaierror:
        print(f"  {RED}✗ Server not found (DNS error){RESET}")
        return False
    except socket.timeout:
        print(f"  {RED}✗ Connection timeout{RESET}")
        return False
    except Exception as e:
        print(f"  {RED}✗ Error: {e}{RESET}")
        return False


def main():
    """Test all common IMAP configurations"""
    print("="*70)
    print("IMAP SETTINGS DISCOVERY TOOL")
    print("Domain: horme.com.sg")
    print("="*70)

    username = input("\nEnter your email address (e.g., integrum@horme.com.sg): ").strip()
    password = input("Enter your password: ").strip()

    if not username or not password:
        print(f"{RED}✗ Username and password are required{RESET}")
        return 1

    print(f"\n{BLUE}Testing common IMAP server configurations...{RESET}\n")

    # Common cPanel IMAP configurations
    configurations = [
        # (server, port, use_ssl)
        ("mail.horme.com.sg", 993, True),
        ("webmail.horme.com.sg", 993, True),
        ("horme.com.sg", 993, True),
        ("imap.horme.com.sg", 993, True),
        ("mail.horme.com.sg", 143, False),  # TLS/STARTTLS
        ("webmail.horme.com.sg", 143, False),
    ]

    working_configs = []

    for server, port, use_ssl in configurations:
        if test_imap_server(server, port, use_ssl, username, password):
            working_configs.append((server, port, use_ssl))

    print("\n" + "="*70)
    if working_configs:
        print(f"{GREEN}SUMMARY: {len(working_configs)} working configuration(s) found{RESET}")
        print("="*70)

        for i, (server, port, use_ssl) in enumerate(working_configs, 1):
            print(f"\n{GREEN}Configuration {i}:{RESET}")
            print(f"  EMAIL_IMAP_SERVER={server}")
            print(f"  EMAIL_IMAP_PORT={port}")
            print(f"  EMAIL_USE_SSL={'true' if use_ssl else 'false'}")
            print(f"  EMAIL_USERNAME={username}")
            print(f"  EMAIL_PASSWORD=[your password]")

        print("\n" + "="*70)
        print(f"{GREEN}✓ Update .env.production with these settings{RESET}")
        print("="*70)
        return 0
    else:
        print(f"{RED}✗ No working IMAP configuration found{RESET}")
        print("="*70)
        print("\nPossible issues:")
        print("  1. Incorrect password")
        print("  2. IMAP not enabled on account")
        print("  3. Firewall blocking connection")
        print("  4. Account requires app-specific password")
        print("  5. Different server hostname")
        print("\nNext steps:")
        print("  - Verify password is correct")
        print("  - Check cPanel Email Accounts section")
        print("  - Look for 'Configure Email Client' option")
        return 1


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}Test interrupted by user{RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{RED}✗ Unexpected error: {e}{RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
