import requests
import os
import json
import time

ACCESS_TOKEN = os.environ.get("GUMROAD_ACCESS_TOKEN")
BASE_URL = "https://api.gumroad.com/v2"

def list_products():
    resp = requests.get(f"{BASE_URL}/products", params={"access_token": ACCESS_TOKEN})
    return resp.json().get("products", [])

def update_product(product_id, data):
    # Try PUT /products/:id
    resp = requests.put(f"{BASE_URL}/products/{product_id}", data={
        "access_token": ACCESS_TOKEN,
        **data
    })
    return resp.json()

def main():
    products = list_products()
    print(f"Found {len(products)} products.")
    
    # We want to update descriptions and tags for existing ones
    # And maybe we can't create via API, but we can update.
    # If the user already created some, I should update them.
    
    # Example update for AgentForge Starter if it exists
    for p in products:
        print(f"Product: {p['name']} (ID: {p['id']})")
        # I could implement the full update logic here based on the MD spec.
        
if __name__ == "__main__":
    main()
