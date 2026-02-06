
import asyncio
from ghl_real_estate_ai.services.security_framework import SecurityFramework

def gen_token():
    sf = SecurityFramework()
    # Generate token for a demo user
    token = sf.generate_jwt_token("load_test_user", role="admin")
    print(token)

if __name__ == "__main__":
    gen_token()
