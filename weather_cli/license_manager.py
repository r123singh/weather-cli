import base64
import hashlib
import json
import os
from datetime import datetime
from typing import Dict, Optional

LICENSE_FILE = "license.json"


class LicenseManager:
    def __init__(self):
        self.license_data = self._load_license()

    def _load_license(self) -> Dict:
        """Load license data from file"""
        if os.path.exists(LICENSE_FILE):
            try:
                with open(LICENSE_FILE, "r") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {"active": False}
        return {"active": False}

    def _save_license(self, data: Dict):
        """Save license data to file"""
        with open(LICENSE_FILE, "w") as f:
            json.dump(data, f)

    def verify_license(self, license_key: str) -> bool:
        """Verify license key and activate premium features"""
        try:
            # Decode license key
            decoded = base64.b64decode(license_key).decode("utf-8")
            key_data = json.loads(decoded)

            # Verify license
            if self._validate_license(key_data):
                self.license_data = {
                    "active": True,
                    "type": key_data["type"],
                    "expiry_date": key_data["expiry_date"],
                    "features": key_data["features"],
                }
                self._save_license(self.license_data)
                return True
            return False
        except:
            return False

    def _validate_license(self, key_data: Dict) -> bool:
        """Validate license data"""
        required_fields = ["type", "expiry_date", "features", "signature"]
        if not all(field in key_data for field in required_fields):
            return False

        # Verify signature
        data_to_sign = f"{key_data['type']}{key_data['expiry_date']}"
        expected_signature = hashlib.sha256(data_to_sign.encode()).hexdigest()

        if key_data["signature"] != expected_signature:
            return False

        # Check expiry
        expiry_date = datetime.strptime(key_data["expiry_date"], "%Y-%m-%d")
        if datetime.now() > expiry_date:
            return False

        return True

    def is_premium(self) -> bool:
        """Check if premium features are active"""
        if not self.license_data.get("active"):
            return False

        # Check expiry for non-lifetime licenses
        if self.license_data["type"] != "lifetime":
            expiry_date = datetime.strptime(
                self.license_data["expiry_date"], "%Y-%m-%d"
            )
            if datetime.now() > expiry_date:
                self.license_data["active"] = False
                self._save_license(self.license_data)
                return False

        return True

    def get_premium_features(self) -> Dict:
        """Get available premium features"""
        if self.is_premium():
            return self.license_data.get("features", {})
        return {}

    def deactivate_license(self):
        """Deactivate current license"""
        self.license_data = {"active": False}
        self._save_license(self.license_data)

    def get_license_info(self) -> Dict:
        """Get current license information"""
        return self.license_data
