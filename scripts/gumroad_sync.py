import os
import json
import requests
import re
import time

def get_existing_products():
    token = os.getenv('GUMROAD_ACCESS_TOKEN')
    headers = {'Authorization': f'Bearer {token}'}
    resp = requests.get('https://api.gumroad.com/v2/products', headers=headers)
    return resp.json().get('products', [])

def update_product(product_id, data):
    token = os.getenv('GUMROAD_ACCESS_TOKEN')
    headers = {'Authorization': f'Bearer {token}'}
    url = f'https://api.gumroad.com/v2/products/{product_id}'
    resp = requests.put(url, headers=headers, data=data)
    try:
        return resp.json()
    except:
        print(f"Error updating product {product_id}: {resp.status_code} {resp.text}")
        return {'success': False, 'message': resp.text}

def create_product(data):
    token = os.getenv('GUMROAD_ACCESS_TOKEN')
    headers = {'Authorization': f'Bearer {token}'}
    url = 'https://api.gumroad.com/v2/products'
    resp = requests.post(url, headers=headers, data=data)
    try:
        return resp.json()
    except:
        print(f"Error creating product: {resp.status_code} {resp.text}")
        return {'success': False, 'message': resp.text}

def parse_prompt_for_products(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    
    products = []
    # Split by Product sections - handle different formats
    sections = re.split(r'#### Product \d+:', content)
    
    for section in sections[1:]: # Skip preamble
        # Name is usually the first line
        lines = section.strip().split('\n')
        name = lines[0].strip()
        
        price_match = re.search(r'\*\*Price\*\*: \$(\d+,?\d*)', section)
        url_match = re.search(r'\*\*URL Slug\*\*: `([^`]+)`', section)
        desc_match = re.search(r'\*\*Full Description\*\*:\s*(?:```)?(.*?)```', section, re.DOTALL)
        short_desc_match = re.search(r'\*\*Short Description\*\* .*?: "([^"]+)"', section)
        tags_match = re.search(r'\*\*Tags\*\*: `([^`]+)`', section)
        
        if not price_match or not url_match:
            continue
            
        price_cents = int(price_match.group(1).replace(',', '')) * 100
        
        products.append({
            'name': name,
            'price': price_cents,
            'url': url_match.group(1),
            'description': desc_match.group(1).strip() if desc_match else "Description coming soon.",
            'short_description': short_desc_match.group(1) if short_desc_match else "",
            'tags': tags_match.group(1) if tags_match else ""
        })
        
    return products

def run_sync():
    print("🚀 Starting Gumroad Product Sync...")
    existing = get_existing_products()
    manifest = parse_prompt_for_products('content/gumroad/GEMINI_UPLOAD_PROMPT.md')
    
    print(f"Found {len(existing)} existing products.")
    print(f"Found {len(manifest)} products in manifest.")
    
    for mp in manifest:
        match = None
        # Try to match by slug in the short_url
        for ep in existing:
            if mp['url'] in ep['short_url']:
                match = ep
                break
        
        data = {
            'name': mp['name'],
            'price': mp['price'],
            'description': mp['description'],
            'summary': mp['short_description'],
            'tags': mp['tags'],
            'custom_permalink': mp['url']
        }
        
        if match:
            print(f"🔄 Updating '{mp['name']}'...")
            res = update_product(match['id'], data)
            if res.get('success'):
                print(f"  ✅ Updated: {res['product']['short_url']}")
            else:
                print(f"  ❌ Error: {res.get('message')}")
        else:
            print(f"➕ Creating '{mp['name']}'...")
            res = create_product(data)
            if res.get('success'):
                print(f"  ✅ Created: {res['product']['short_url']}")
            else:
                # If permalink taken, try without it or let user fix
                print(f"  ❌ Error: {res.get('message')}")
        
        time.sleep(1) # Rate limit safety

if __name__ == "__main__":
    run_sync()
