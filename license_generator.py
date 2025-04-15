import json
import base64
import hashlib
from datetime import datetime, timedelta
from typing import Dict

class LicenseGenerator:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
    
    def generate_license(self, license_type: str, duration_days: int = None) -> str:
        """Generate a license key"""
        if license_type == 'lifetime':
            expiry_date = '2099-12-31'
        else:
            expiry_date = (datetime.now() + timedelta(days=duration_days)).strftime('%Y-%m-%d')
        
        # Define features based on license type
        features = {
            'monthly': ['basic', 'maps', 'forecast'],
            'yearly': ['basic', 'maps', 'forecast', 'historical', 'export'],
            'lifetime': ['basic', 'maps', 'forecast', 'historical', 'export', 'api', 'custom']
        }
        
        # Create license data
        license_data = {
            'type': license_type,
            'expiry_date': expiry_date,
            'features': features.get(license_type, []),
            'generated_date': datetime.now().strftime('%Y-%m-%d')
        }
        
        # Generate signature
        data_to_sign = f"{license_type}{expiry_date}{self.secret_key}"
        license_data['signature'] = hashlib.sha256(data_to_sign.encode()).hexdigest()
        
        # Encode license data
        encoded_data = base64.b64encode(json.dumps(license_data).encode()).decode()
        
        return encoded_data
    
    def generate_batch(self, count: int, license_type: str, duration_days: int = None) -> Dict[str, str]:
        """Generate multiple license keys"""
        licenses = {}
        for i in range(count):
            license_key = self.generate_license(license_type, duration_days)
            licenses[f"LICENSE-{i+1}"] = license_key
        return licenses

def main():
    # Example usage
    generator = LicenseGenerator(secret_key="your-secret-key-here")
    
    # Generate single license
    monthly_license = generator.generate_license('monthly', 30)
    print(f"Monthly License: {monthly_license}")
    
    # Generate batch of licenses
    yearly_licenses = generator.generate_batch(5, 'yearly', 365)
    print("\nYearly Licenses:")
    for key, value in yearly_licenses.items():
        print(f"{key}: {value}")
    
    # Generate lifetime license
    lifetime_license = generator.generate_license('lifetime')
    print(f"\nLifetime License: {lifetime_license}")

if __name__ == "__main__":
    main() 