import json
import re

with open('synth_inventory.js', 'r') as f:
    js = f.read()

# Remove the variable assignment and trailing semicolon
match = re.search(r'const synthInventory\s*=\s*(\[.*?\])\s*;', js, re.DOTALL)
if not match:
    raise ValueError("Could not find synthInventory array in JS file.")

# Remove trailing commas from the array for valid JSON
array_str = re.sub(r',\s*([}\]])', r'\1', match.group(1))

items = json.loads(array_str)

found = False
for item in items:
    if "properties" in item and len(item["properties"]) <= 4:
        print(item.get('id'))
        found = True
if not found:
    print("No items found with 4 or fewer properties.")