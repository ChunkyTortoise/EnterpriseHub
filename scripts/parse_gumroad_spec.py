import re
import json

def parse_spec(file_path):
    with open(file_path, 'r') as f:
        content = f.read()
    
    products = []
    
    # Simple regex to find product sections
    # They look like: #### Product X: [Name]
    sections = re.split(r'#### Product \d+:', content)
    
    for section in sections[1:]:
        lines = section.strip().split('\n')
        name = lines[0].strip()
        
        product = {"spec_name": name}
        
        # Parse table fields
        # | **Title** | AgentForge Starter — Multi-LLM Orchestration Framework |
        table_matches = re.findall(r'\| \*\*([^*]+)\*\* \| ([^|]+) \|', section)
        for field, value in table_matches:
            product[field.lower().replace(" ", "_")] = value.strip()
            
        # Parse Full Description
        # **Full Description** (paste this into the description field):
        # ```markdown
        # ...
        # ```
        desc_match = re.search(r'\*\*Full Description\*\*.*?:?\s*```markdown\n(.*?)\n```', section, re.DOTALL)
        if desc_match:
            product["description"] = desc_match.group(1)
            
        products.append(product)
        
    return products

if __name__ == "__main__":
    products = parse_spec('plans/GEMINI_BROWSER_EXECUTION_PROMPT.md')
    # Save to json for the creator script
    with open('scripts/parsed_products.json', 'w') as f:
        json.dump(products, f, indent=2)
    print(f"Parsed {len(products)} products to scripts/parsed_products.json")
