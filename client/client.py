import requests
from datetime import datetime, timedelta, timezone
from pymacaroons import Macaroon
from time import sleep

SERVER_URL = "http://localhost:8080"

def get_new_admin_token(expires_in_seconds=30, methods="create,solve,close"):
    expires_at = (datetime.utcnow() + timedelta(seconds=expires_in_seconds)).isoformat()
    payload = {
        "expires_at": expires_at,
        "methods": methods
    }
    response = requests.post(f"{SERVER_URL}/newToken", json=payload)
    if response.status_code == 200:
        return response.json()["token"]
    else:
        raise Exception(f"Error: {response.status_code}\n{response.text}")

def inspect_macaroon(macaroon_string):
    macaroon = Macaroon.deserialize(macaroon_string)
    print(f"    Macaroon: {macaroon_string}")
    print(f"    Version: {macaroon.version}")
    
    print("    Caveats:")
    for caveat in macaroon.caveats:
        print(f"    - {str(caveat.caveat_id)}")
    
    print(f"\n    Signature: {macaroon.signature}")

def new_macaroon(macaroon, key, value):
    mac = Macaroon.deserialize(macaroon)
    mac.add_first_party_caveat(f"{key}={value}")
    return mac.serialize()


def create_issue(macaroon, title, description):
    payload = {
        "title": title,
        "description": description
    }

    print(f"Creating issue with {macaroon}")
    response = requests.post(f"{SERVER_URL}/create", json=payload, headers={"Authorization": f"Bearer {macaroon}"})
    if 200 <= response.status_code < 300:
        return response.json()["number"]
    else:
        raise Exception(f"Error: {response.status_code}\n{response.text}")

def mark_issue_solved(macaroon, issue_number):
    print(f"Marking issue as solved with {macaroon}")
    response = requests.post(f"{SERVER_URL}/solve", json={"issue_number": issue_number}, headers={"Authorization": f"Bearer {macaroon}"})
    if 200 <= response.status_code < 300:
        return
    else:
        raise Exception(f"Error: {response.status_code}\n{response.text}")

def close_issue(macaroon, issue_number):
    print(f"Closing issue with {macaroon}")
    response = requests.post(f"{SERVER_URL}/close", json={"issue_number": issue_number}, headers={"Authorization": f"Bearer {macaroon}"})
    if 200 <= response.status_code < 300:
        return
    else:
        raise Exception(f"Error: {response.status_code}\n{response.text}")

def main():
    try:
        macaroon_string = get_new_admin_token()
        print(f"New admin macaroon:")
        inspect_macaroon(macaroon_string)
        print(f"\n\n\n")

        # admin_macaroon = Macaroon.deserialize(macaroon_string)

        dummy_macaroon = new_macaroon(macaroon_string, "valid_methods", "create,solve")
        print(f"New dummy macaroon:")
        inspect_macaroon(dummy_macaroon)
        print(f"\n\n\n")

        in_10_seconds = (datetime.utcnow() + timedelta(seconds=10)).isoformat()
        short_lived_macaroon = new_macaroon(macaroon_string, "expires_at", in_10_seconds)
        print(f"New short-lived macaroon:")
        inspect_macaroon(short_lived_macaroon)
        print(f"\n\n\n")

        sleep(5)


        issue_number = create_issue(dummy_macaroon, "Test Issue", "This is a test issue")
        print(f"Issue created with ID: {issue_number}\n")

        mark_issue_solved(dummy_macaroon, issue_number)
        print(f"Issue marked as solved with ID: {issue_number}\n")

        try:
            close_issue(dummy_macaroon, issue_number)
            print(f"Issue closed with ID: {issue_number}\n")
        except Exception as e:
            print(f"Unable to close issue: {e}")

        
        close_issue(short_lived_macaroon, issue_number)

        sleep(5)

        issue_number = create_issue(dummy_macaroon, "Test Issue 2", "This is a test issue")
        print(f"Issue created with ID: {issue_number}")

        mark_issue_solved(dummy_macaroon, issue_number)
        print(f"Issue marked as solved with ID: {issue_number}")

        try:
            close_issue(short_lived_macaroon, issue_number)
            print(f"Issue closed with ID: {issue_number}")
        except Exception as e:
            print(f"Unable to close issue: {e}")

    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
