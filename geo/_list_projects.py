# -*- coding: utf-8 -*-
"""تشخيص: قائمة مشاريع Google Cloud المتاحة لاعتماد Earth Engine المحفوظ."""
import json
import os
import sys

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass

import requests
from ee import oauth as ee_oauth
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

cred_path = os.path.expanduser("~/.config/earthengine/credentials")
d = json.load(open(cred_path))
creds = Credentials(
    None,
    refresh_token=d["refresh_token"],
    client_id=ee_oauth.CLIENT_ID,
    client_secret=ee_oauth.CLIENT_SECRET,
    token_uri="https://oauth2.googleapis.com/token",
    scopes=d.get("scopes"),
)
creds.refresh(Request())
r = requests.get(
    "https://cloudresourcemanager.googleapis.com/v1/projects",
    headers={"Authorization": f"Bearer {creds.token}"}, timeout=30,
)
r.raise_for_status()
for p in r.json().get("projects", []):
    print(p["projectId"], "|", p.get("name"), "|", p.get("lifecycleState"))
