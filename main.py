#!/usr/bin/env python3

import json
import os
import re
import sys
from datetime import datetime
from urllib.parse import quote

import requests


APP_NAME = "Instagram UID Assistant"
VERSION = "1.0.0"

USERNAME_RE = re.compile(r"^[A-Za-z0-9._]{1,30}$")


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def banner():
    print("=" * 58)
    print(f"        {APP_NAME} v{VERSION}")
    print("        Public/authorized Instagram utility")
    print("=" * 58)


def valid_username(username):
    return bool(USERNAME_RE.fullmatch(username))


def normalize_username(username):
    username = username.strip()

    if username.startswith("@"):
        username = username[1:]

    if "instagram.com/" in username:
        username = username.rstrip("/").split("instagram.com/")[-1]
        username = username.split("/")[0]
        username = username.split("?")[0]

    return username


def profile_url(username):
    return f"https://www.instagram.com/{quote(username)}/"


def get_public_profile_page(username):
    """
    Basic public profile-page check.

    This does NOT attempt to bypass Instagram protections.
    """
    url = profile_url(username)

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 Chrome/140 Safari/537.36"
        )
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=10,
            allow_redirects=True,
        )

        return {
            "status_code": response.status_code,
            "reachable": response.status_code < 400,
            "url": response.url,
        }

    except requests.RequestException as exc:
        return {
            "status_code": None,
            "reachable": False,
            "url": url,
            "error": str(exc),
        }


def lookup_authorized_graph_api(username):
    """
    Optional official Graph API lookup.

    The token must belong to an authorized Meta/Instagram
    integration. This function does not obtain or steal tokens.
    """

    token = os.getenv("INSTAGRAM_ACCESS_TOKEN")

    if not token:
        return {
            "success": False,
            "message": (
                "INSTAGRAM_ACCESS_TOKEN is not configured. "
                "Public profile URL mode is still available."
            ),
        }

    # This endpoint is intended for an authorized API integration.
    # The exact fields available depend on the API/account setup.
    url = "https://graph.instagram.com/me"

    params = {
        "fields": "id,username",
        "access_token": token,
    }

    try:
        response = requests.get(url, params=params, timeout=10)

        if response.status_code != 200:
            return {
                "success": False,
                "status_code": response.status_code,
                "message": "Official API request was not successful.",
            }

        data = response.json()

        return {
            "success": True,
            "data": data,
        }

    except requests.RequestException as exc:
        return {
            "success": False,
            "message": str(exc),
        }


def save_json(data, filename="result.json"):
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

    return filename


def save_txt(data, filename="result.txt"):
    with open(filename, "w", encoding="utf-8") as file:
        file.write(f"{APP_NAME}\n")
        file.write("=" * 50 + "\n\n")

        for key, value in data.items():
            file.write(f"{key}: {value}\n")

    return filename


def username_mode():
    print("\nEnter Instagram username.")
    print("Example: cristiano")
    print()

    raw = input("Username: ")
    username = normalize_username(raw)

    if not valid_username(username):
        print("\n[!] Invalid Instagram username format.")
        input("\nPress Enter to continue...")
        return

    url = profile_url(username)

    print("\n[+] Username :", username)
    print("[+] Profile  :", url)

    print("\n[*] Checking public profile URL...")

    result = get_public_profile_page(username)

    if result["reachable"]:
        print(
            f"[+] Profile URL is reachable "
            f"(HTTP {result['status_code']})."
        )
    else:
        print(
            f"[!] Could not verify profile "
            f"(HTTP {result.get('status_code')})."
        )

    data = {
        "username": username,
        "profile_url": url,
        "checked_at": datetime.now().isoformat(),
        "public_page_check": result,
    }

    print("\n1. Export JSON")
    print("2. Export TXT")
    print("3. Back")

    choice = input("\nSelect: ").strip()

    if choice == "1":
        filename = save_json(data)
        print(f"\n[+] Saved: {filename}")

    elif choice == "2":
        filename = save_txt(data)
        print(f"\n[+] Saved: {filename}")

    input("\nPress Enter to continue...")


def authorized_api_mode():
    print("\n" + "-" * 58)
    print("Official Instagram/Meta API mode")
    print("-" * 58)

    print(
        "\nThis mode requires an access token from your own "
        "authorized Meta/Instagram application."
    )

    result = lookup_authorized_graph_api()

    if result["success"]:
        print("\n[+] API request successful.")
        print(json.dumps(result["data"], indent=4))

        save = input("\nSave API result to JSON? [y/N]: ").lower()

        if save == "y":
            filename = save_json(result["data"], "api_result.json")
            print(f"[+] Saved: {filename}")

    else:
        print(f"\n[!] {result['message']}")

    input("\nPress Enter to continue...")


def about():
    print("\n" + "-" * 58)
    print(APP_NAME)
    print("-" * 58)
    print(
        """
Purpose:
  A small CLI utility for working with Instagram usernames
  and authorized Instagram/Meta API integrations.

This project does NOT:
  - collect passwords
  - collect OTP codes
  - brute-force accounts
  - steal session cookies
  - bypass authentication
  - bypass Instagram security
  - attempt unauthorized account access
"""
    )

    input("Press Enter to continue...")


def main():
    while True:
        clear_screen()
        banner()

        print("\n[1] Username / public profile utility")
        print("[2] Authorized API lookup")
        print("[3] About")
        print("[4] Exit")

        choice = input("\nSelect option: ").strip()

        if choice == "1":
            username_mode()

        elif choice == "2":
            authorized_api_mode()

        elif choice == "3":
            about()

        elif choice == "4":
            print("\nBye bhai 👋")
            sys.exit(0)

        else:
            print("\n[!] Invalid option.")
            input("Press Enter to continue...")


if __name__ == "__main__":
    main()
