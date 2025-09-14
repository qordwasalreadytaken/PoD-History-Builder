import js2py
context = js2py.EvalJs()
with open("item_metadata.js", "r", encoding="utf-8") as f:
    context.execute(f.read())
stats = context.stats.to_dict()
import json
with open("item_metadata.json", "w") as f:
    json.dump(stats, f, indent=2)
