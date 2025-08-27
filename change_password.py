"""
Interactive password change helper for Harbor.
If target username is omitted, performs self password change (requires current password).
If acting user is an admin and specifies --target, the admin can set a new password for the target user.

Example (self):
  python change_password.py --host https://harbor.exposedcore.com --user alice --prompt-pass

Example (admin sets other's password):
  python change_password.py --host https://harbor.exposedcore.com --user admin --prompt-pass --target bob

"""

import argparse
import getpass
import os
import sys
import harbor_client
from harbor_client.rest import ApiException

def make_api_client(host: str, username: str, password: str, verify_ssl: bool = True) -> harbor_client.ApiClient:
    configuration = harbor_client.Configuration()
    configuration.host = host.rstrip("/") + "/api/v2.0"
    configuration.username = username
    configuration.password = password
    api_client = harbor_client.ApiClient(configuration)
    if not verify_ssl:
        try:
            api_client.rest_client.pool_manager.connection_pool_kw['cert_reqs'] = False
        except Exception:
            pass
    return api_client

def change_password_interactive(host: str, acting_user: str, acting_pass: str, target_username: str = None):
    api_client = make_api_client(host, acting_user, acting_pass)
    user_api = harbor_client.UserApi(api_client)

    try:
        if target_username and target_username.lower() != acting_user.lower():
            # admin changes another user's password
            search_resp = user_api.search_users(target_username, page=1, page_size=1)
            if not search_resp:
                print(f"[ERROR] User '{target_username}' not found")
                return
            target_id = getattr(search_resp[0], 'user_id', None)
            if not target_id:
                print(f"[ERROR] Cannot determine ID of '{target_username}'")
                return
            new_pass = getpass.getpass(f"New password for {target_username}: ")
            confirm = getpass.getpass("Confirm new password: ")
            if new_pass != confirm:
                print("[ERROR] Passwords do not match. Aborting.")
                return
            pw = harbor_client.PasswordReq()
            pw.new_password = new_pass
            user_api.update_user_password(int(target_id), pw)
            print(f"[OK] Password updated for '{target_username}'")
        else:
            # self password change
            search_resp = user_api.search_users(acting_user, page=1, page_size=1)
            if not search_resp:
                print(f"[ERROR] User '{acting_user}' not found")
                return
            my_id = getattr(search_resp[0], 'user_id', None)
            if not my_id:
                print("[ERROR] Cannot determine your user ID")
                return
            old = getpass.getpass("Current password: ")
            new = getpass.getpass("New password: ")
            confirm = getpass.getpass("Confirm new password: ")
            if new != confirm:
                print("[ERROR] Passwords do not match. Aborting.")
                return
            pw = harbor_client.PasswordReq()
            pw.old_password = old
            pw.new_password = new
            try:
                user_api.update_user_password(int(my_id), pw)
                print("[OK] Password changed successfully")
            except ApiException as e:
                if e.status == 400:
                    print(f"[ERROR] Bad request: {e.body}")
                elif e.status == 401:
                    print("[ERROR] Unauthorized: wrong current password or insufficient permissions")
                else:
                    print(f"[ERROR] Failed to change password: {e}")
    except ApiException as e:
        print(f"[ERROR] API Exception: {e}")
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Change Harbor password interactively',
        usage='python3 change_password.py --host HOST --user USER [--target TARGET] --prompt-pass'
    )
    parser.add_argument('--host', required=True, help='Harbor host (http://localhost or https://harbor.example.com)')
    parser.add_argument('--user', required=False, default=os.environ.get('HARBOR_ADMIN_USER'), help='Your username')
    parser.add_argument('--prompt-pass', action='store_true', help='Prompt for your password')
    parser.add_argument('--target', required=False, help='Target username to change (admin only)')
    args = parser.parse_args()

    if not args.user:
        print("[ERROR] Acting user not provided and HARBOR_ADMIN_USER not set", file=sys.stderr)
        sys.exit(2)

    if args.prompt_pass or not os.environ.get('HARBOR_ADMIN_PASS'):
        acting_pass = getpass.getpass('Password for acting user: ')
    else:
        acting_pass = os.environ.get('HARBOR_ADMIN_PASS')

    change_password_interactive(args.host, args.user, acting_pass, target_username=args.target)
