"""
Create users from CSV for Harbor and (optionally) add them as project members.
CSV headers: Username, Password, Role
Optional header: Project (multiple projects separated by spaces)

Example:
  python create_users_from_csv.py --csv users.csv --host https://example.com --admin-user admin --admin-pass 'secret' --project myproject1,myproject2
"""

import csv
import argparse
import getpass
import os
import sys
import time
from typing import Optional

import harbor_client
from harbor_client.rest import ApiException

ROLE_MAP = {
    "projectadmin": 1,
    "project_admin": 1,
    "project-admin": 1,
    "admin": 1,
    "developer": 2,
    "dev": 2,
    "guest": 3,
    "visitor": 3,
    "maintainer": 4,
    "master": 4,
}


def make_api_client(host: str, username: str, password: str, verify_ssl: bool = True) -> harbor_client.ApiClient:
    configuration = harbor_client.Configuration()
    configuration.host = host.rstrip("/") + "/api/v2.0" if not host.endswith("/api/v2.0") else host
    configuration.username = username
    configuration.password = password
    api_client = harbor_client.ApiClient(configuration)
    if not verify_ssl:
        try:
            api_client.rest_client.pool_manager.connection_pool_kw['cert_reqs'] = False
        except Exception:
            pass
    return api_client


def create_users_from_csv(csv_file: str, host: str, admin_user: str, admin_pass: str, default_projects: Optional[str], create_project_if_missing: bool = False):
    api_client = make_api_client(host, admin_user, admin_pass)
    user_api = harbor_client.UserApi(api_client)
    member_api = harbor_client.MemberApi(api_client)
    project_api = harbor_client.ProjectApi(api_client)

    results = []
    default_projects_list = [p.strip() for p in default_projects.split(",")] if default_projects else []

    with open(csv_file, newline='', encoding='utf-8') as fh:
        reader = csv.DictReader(fh)
        for row_no, row in enumerate(reader, start=1):
            username = (row.get('Username') or row.get('username') or '').strip()
            password = (row.get('Password') or row.get('password') or '').strip()
            role_raw = (row.get('Role') or row.get('role') or '').strip()
            projects_row = (row.get('Project') or row.get('project') or '').strip()

            if not username or not password or not role_raw:
                results.append((row_no, username, 'SKIP', 'missing username/password/role'))
                continue

            role_key = role_raw.replace(' ', '').replace('-', '').replace('_', '').lower()
            role_id = ROLE_MAP.get(role_key)
            if role_id is None:
                try:
                    role_id = int(role_raw)
                except Exception:
                    results.append((row_no, username, 'SKIP', f'unknown role "{role_raw}"'))
                    continue

            user_id = None
            user_created = False
            try:
                api_resp = user_api.search_users(username, page=1, page_size=10)
                if api_resp:
                    for item in api_resp:
                        if getattr(item, 'username', '').lower() == username.lower():
                            user_id = getattr(item, 'user_id', None)
                            break

                if user_id is not None:
                    results.append((row_no, username, 'SKIP', f'user "{username}" already exists'))
                else:
                    user_req = harbor_client.UserCreationReq()
                    user_req.username = username
                    user_req.password = password
                    user_req.email = f"{username}@local.local"
                    user_req.realname = username
                    user_api.create_user(user_req)
                    time.sleep(0.2)
                    search_resp = user_api.search_users(username, page=1, page_size=1)
                    if search_resp:
                        user_id = getattr(search_resp[0], 'user_id', None)
                        user_created = True

                if not user_id:
                    results.append((row_no, username, 'ERROR', 'could not determine user id after creation'))
                    continue

            except ApiException as e:
                results.append((row_no, username, 'ERROR', f'create_user failed: {e}'))
                continue

            projects_to_use = projects_row.split() if projects_row else default_projects_list
            added_to_projects = False

            for proj_name in projects_to_use:
                if not proj_name:
                    continue
                try:
                    project_api.head_project(proj_name)
                except ApiException as e:
                    if create_project_if_missing:
                        try:
                            proj_req = harbor_client.ProjectReq()
                            proj_req.project_name = proj_name
                            proj_req.metadata = harbor_client.ProjectMetadata()
                            proj_req.metadata.public = "false"
                            project_api.create_project(proj_req)
                            time.sleep(0.2)
                        except Exception as e2:
                            results.append((row_no, username, 'ERROR', f'project create/check failed: {e2}'))
                            continue
                    else:
                        results.append((row_no, username, 'WARN', f'project "{proj_name}" not found - skipping project membership'))
                        continue

                try:
                    pm = harbor_client.ProjectMember()
                    user_entity = harbor_client.UserEntity()
                    user_entity.user_id = int(user_id)
                    user_entity.username = username
                    pm.member_user = user_entity
                    pm.role_id = int(role_id)
                    member_api.create_project_member(project_name_or_id=proj_name, project_member=pm)
                    results.append((row_no, username, 'OK', f'user_id={user_id} added to project {proj_name} role={role_id}'))
                    added_to_projects = True
                except ApiException as e:
                    if e.status == 409:
                        results.append((row_no, username, 'SKIP', f'user "{username}" already in project {proj_name}'))
                    else:
                        results.append((row_no, username, 'ERROR', f'add to project failed: {e}'))

            if user_created and not added_to_projects:
                results.append((row_no, username, 'OK_USER', f'user_id={user_id}'))

    print('RESULTS:')
    for r in results:
        print(r)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create Harbor users from CSV')
    parser.add_argument('--csv', required=True, help='CSV input file (headers: Username,Password,Role[,Project])')
    parser.add_argument('--host', required=True, help='Harbor host (e.g. https://harbor.example.com)')
    parser.add_argument('--admin-user', required=False, default=os.environ.get('HARBOR_ADMIN_USER'), help='Harbor admin username')
    parser.add_argument('--admin-pass', required=False, default=os.environ.get('HARBOR_ADMIN_PASS'), help='Admin password (or set HARBOR_ADMIN_PASS env var)')
    parser.add_argument('--project', required=False, help='Default projects (comma-separated) to add users into if CSV field missing')
    parser.add_argument('--create-project-if-missing', action='store_true', help='Create project if it does not exist')

    args = parser.parse_args()

    if not args.admin_user:
        print('admin-user not provided and HARBOR_ADMIN_USER not set', file=sys.stderr)
        sys.exit(2)
    if not args.admin_pass:
        args.admin_pass = getpass.getpass('Admin password: ')

    create_users_from_csv(args.csv, args.host, args.admin_user, args.admin_pass, args.project, args.create_project_if_missing)
