import os
from datetime import datetime, timedelta
from typing import Dict, List, Callable
from functools import wraps
import json
from flask import request, jsonify
from pymacaroons import Macaroon, Verifier, MACAROON_V2

class AuthError(Exception):
    pass

class FileStore:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.data: Dict[str, str] = {}
        self.load_from_file()

    def load_from_file(self):
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r') as f:
                self.data = json.load(f)

    def save_to_file(self):
        with open(self.file_path, 'w') as f:
            json.dump(self.data, f)

    def create_root_key(self, token_id: bytes, root_key: bytes):
        self.data[token_id.hex()] = root_key.hex()
        self.save_to_file()

    def get_root_key(self, token_id: bytes) -> bytes:
        root_key_hex = self.data.get(token_id.hex())
        if root_key_hex is None:
            raise AuthError("Root key not found")
        return bytes.fromhex(root_key_hex)

class Authenticator:
    def __init__(self, store: FileStore):
        self.store = store

    def new_macaroon(self, constraints: Dict[str, str]) -> str:
        location = "https://example.com"
        identifier = os.urandom(16).hex()
        root_key = os.urandom(32)

        self.store.create_root_key(identifier.encode(), root_key)

        macaroon = Macaroon(location=location, identifier=identifier, key=root_key, version=MACAROON_V2)

        for key, value in constraints.items():
            macaroon.add_first_party_caveat(f"{key}={value}", version=MACAROON_V2)

        return macaroon.serialize()

    def verify_macaroon(self, req_ctx: Dict[str, str], macaroon_string: str, predicates: List[Callable]) -> bool:
        try:
            macaroon = Macaroon.deserialize(macaroon_string)
            root_key = self.store.get_root_key(macaroon.identifier)

            

            for predicate in predicates:
                verifier = Verifier()
                verifier.satisfy_general(lambda caveat: predicate(req_ctx, caveat))
                verifier.verify(macaroon, root_key)
            
            return True
        except Exception as e:
            raise AuthError(f"Invalid macaroon: {str(e)}")

def inspect_macaroon(macaroon_string):
    macaroon = Macaroon.deserialize(macaroon_string)
    print(f"    Macaroon: {macaroon_string}")
    print(f"    Version: {macaroon.version}")
    
    print("    Caveats:")
    for caveat in macaroon.caveats:
        print(f"    - {str(caveat.caveat_id)}")
    
    print(f"\n    Signature: {macaroon.signature}")

def expires_at_predicate(req_ctx: Dict[str, str], caveat: str) -> bool:
    print(f"    Expires at predicate: {caveat}")
    if not caveat.startswith("expires_at="):
        return True
    req_time = req_ctx['current_time']
    expires_at = datetime.fromisoformat(caveat.split("=")[1])
    print(f"    Expires at: {expires_at}")
    print(f"    Current time: {req_time}")
    print(f"    Expires at < Current time: {expires_at < req_time}")
    if expires_at < req_time:
        raise AuthError("Macaroon expired")
    
    return True

def methods_predicate(req_ctx: Dict[str, str], caveat: str) -> bool:
    print(f"    Methods predicate: {caveat}")
    if not caveat.startswith("valid_methods="):
        return True
    method = req_ctx['method']
    valid_methods = caveat.split("=")[1].split(',')
    if method not in valid_methods:
        print(f"method: {method} valid_methods: {valid_methods}")
        raise AuthError("Invalid method")
    return True

store = FileStore('auth_db.json')
authenticator = Authenticator(store)

def auth_middleware(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({"error": "Missing Authorization header"}), 401
        
        macaroon = auth_header.replace('Bearer ', '').strip()
        if not macaroon:
            return jsonify({"error": "Invalid Authorization header format"}), 401
        
        method = request.path.strip('/')
        req_ctx = {
            'current_time': datetime.utcnow(),
            'method': method
        }
        
        predicates =[expires_at_predicate, methods_predicate]
        
        try:
            if not authenticator.verify_macaroon(req_ctx, macaroon, predicates):
                return jsonify({"error": "Unauthorized"}), 401
        except AuthError as e:
            return jsonify({"error": str(e)}), 401
        
        return f(*args, **kwargs)
    return decorated_function

def new_token(expires_at: datetime = None, methods: str = None) -> str:
    if expires_at is None:
        expires_at = datetime.utcnow() + timedelta(minutes=1)
    if methods is None:
        methods = "create,solve,close"
    
    constraints = {
        "expires_at": expires_at.isoformat(),
        "valid_methods": methods
    }
    
    return authenticator.new_macaroon(constraints)
