"""
IMAP Connection Test
Tests real connection to webmail.horme.com.sg
NO MOCK - Tests actual IMAP server with real credentials
"""

import os
import sys
from imapclient import IMAPClient
from datetime import datetime

# Fix Windows console encoding for Unicode characters
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


def test_imap_connection():
    """Test IMAP connection with real credentials"""
    print("=" * 70)
    print("IMAP CONNECTION TEST")
    print("Server: webmail.horme.com.sg")
    print("=" * 70)
    print()

    # Get credentials from environment
    print("Step 1: Loading credentials from environment...")
    imap_server = os.getenv('EMAIL_IMAP_SERVER')
    imap_port = int(os.getenv('EMAIL_IMAP_PORT', 993))
    username = os.getenv('EMAIL_USERNAME')
    password = os.getenv('EMAIL_PASSWORD')
    use_ssl = os.getenv('EMAIL_USE_SSL', 'true').lower() == 'true'

    if not all([imap_server, username, password]):
        print(f"{RED}✗ Missing environment variables:{RESET}")
        if not imap_server:
            print(f"  - EMAIL_IMAP_SERVER")
        if not username:
            print(f"  - EMAIL_USERNAME")
        if not password:
            print(f"  - EMAIL_PASSWORD")
        print()
        print("Set these in .env file or environment")
        return False

    print(f"{GREEN}✓ Credentials loaded{RESET}")
    print(f"  Server: {imap_server}:{imap_port}")
    print(f"  Username: {username}")
    print(f"  SSL: {use_ssl}")
    print()

    # Step 2: Create IMAP client
    print("Step 2: Creating IMAP client...")
    try:
        client = IMAPClient(
            imap_server,
            port=imap_port,
            use_uid=True,
            ssl=use_ssl,
            timeout=30
        )
        print(f"{GREEN}✓ IMAP client created{RESET}")
    except Exception as e:
        print(f"{RED}✗ Failed to create IMAP client: {e}{RESET}")
        return False

    print()

    try:
        # Step 3: Login
        print("Step 3: Attempting login...")
        try:
            client.login(username, password)
            print(f"{GREEN}✓ Login successful{RESET}")
        except Exception as e:
            print(f"{RED}✗ Login failed: {e}{RESET}")
            print()
            print("Common issues:")
            print("  - Incorrect password")
            print("  - Account requires app-specific password")
            print("  - IMAP not enabled on account")
            print("  - Firewall blocking connection")
            return False

        print()

        # Step 4: List folders
        print("Step 4: Listing mail folders...")
        try:
            folders = client.list_folders()
            print(f"{GREEN}✓ Found {len(folders)} folders{RESET}")

            # Show first 5 folders
            for i, (flags, delimiter, name) in enumerate(folders[:5]):
                print(f"  {i+1}. {name}")

            if len(folders) > 5:
                print(f"  ... and {len(folders) - 5} more")
        except Exception as e:
            print(f"{YELLOW}⊘ Could not list folders: {e}{RESET}")

        print()

        # Step 5: Select INBOX
        print("Step 5: Selecting INBOX folder...")
        try:
            folder_info = client.select_folder("INBOX")
            total_messages = folder_info[b'EXISTS']
            print(f"{GREEN}✓ INBOX selected{RESET}")
            print(f"  Total messages: {total_messages}")
        except Exception as e:
            print(f"{RED}✗ Could not select INBOX: {e}{RESET}")
            return False

        print()

        # Step 6: Search for messages
        print("Step 6: Searching for messages...")
        try:
            # Search for all messages
            all_messages = client.search(["ALL"])
            print(f"{GREEN}✓ Found {len(all_messages)} total messages{RESET}")

            # Search for unseen messages
            unseen_messages = client.search(["UNSEEN"])
            print(f"{GREEN}✓ Found {len(unseen_messages)} unseen messages{RESET}")

            # Search for messages with RFQ keywords
            rfq_keywords = ["quotation", "RFQ", "quote", "proposal"]
            keyword_count = 0

            for keyword in rfq_keywords:
                try:
                    results = client.search(["SUBJECT", keyword])
                    if results:
                        keyword_count += len(results)
                        print(f"{BLUE}  • '{keyword}' in subject: {len(results)} messages{RESET}")
                except:
                    pass

            if keyword_count > 0:
                print(f"{GREEN}✓ Found {keyword_count} messages with RFQ keywords{RESET}")
            else:
                print(f"{YELLOW}⊘ No messages with RFQ keywords found{RESET}")

        except Exception as e:
            print(f"{YELLOW}⊘ Search failed: {e}{RESET}")

        print()

        # Step 7: Fetch sample message (if available)
        if unseen_messages:
            print("Step 7: Fetching sample message header...")
            try:
                sample_id = unseen_messages[0]
                message_data = client.fetch([sample_id], ['ENVELOPE'])

                if sample_id in message_data:
                    envelope = message_data[sample_id][b'ENVELOPE']
                    print(f"{GREEN}✓ Sample message retrieved{RESET}")
                    print(f"  Message ID: {sample_id}")
                    print(f"  From: {envelope.from_[0].mailbox.decode()}@{envelope.from_[0].host.decode()}")
                    print(f"  Subject: {envelope.subject.decode() if envelope.subject else '(no subject)'}")
                    print(f"  Date: {envelope.date}")
            except Exception as e:
                print(f"{YELLOW}⊘ Could not fetch sample message: {e}{RESET}")
        else:
            print("Step 7: No messages to fetch (inbox is empty or all read)")

        print()

        # Step 8: Test capabilities
        print("Step 8: Checking server capabilities...")
        try:
            capabilities = client.capabilities()
            print(f"{GREEN}✓ Server capabilities: {len(capabilities)}{RESET}")

            important_caps = ['IDLE', 'SORT', 'THREAD', 'UIDPLUS']
            for cap in important_caps:
                if cap.encode() in capabilities:
                    print(f"  ✓ {cap} supported")
                else:
                    print(f"  ✗ {cap} not supported")
        except Exception as e:
            print(f"{YELLOW}⊘ Could not check capabilities: {e}{RESET}")

        print()

        # Summary
        print("=" * 70)
        print(f"{GREEN}✓ IMAP CONNECTION TEST PASSED{RESET}")
        print()
        print("Summary:")
        print(f"  Server: {imap_server}:{imap_port}")
        print(f"  Authentication: ✓ Success")
        print(f"  Folder access: ✓ Success")
        print(f"  Message search: ✓ Success")
        print(f"  Total messages: {total_messages}")
        print(f"  Unseen messages: {len(unseen_messages)}")
        print()
        print("Email monitor service should work correctly.")
        print("=" * 70)

        return True

    finally:
        # Always logout
        try:
            client.logout()
            print(f"\n{GREEN}✓ Logged out successfully{RESET}")
        except:
            pass


if __name__ == '__main__':
    try:
        success = test_imap_connection()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}Test interrupted by user{RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{RED}✗ Unexpected error: {e}{RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
