# PoD-History-Builder
# Saving character data over time via build planner links

# Downloads all ladder character to json file

- Using same functions as the trends site downloads all ladder SC and HC data to one big json file, runs at 45 minutes past the hour, every hour


## Collect.py looks at downloaded character json file and:
### For each character
- Looks at skills and equipment and creates a build planner url that maps those skills and equips
- Maps that url to timestamp
- Creates/updates index.json that maps timestamp url's to character names
- Runs at 1o minutes pas the hour, every hour

## Search.html
- Searches index for character names
- Returns all links from the snapshot files


## Limitations:
- We're buiding a url the planner can read, we're not equipping items in the planner. As a result:
-- We cannot import stats of an item, so magic, rare, and crafted items will come across with no stats/properties
-- This will not catch synth items
- HC characters that are dead will never change
- HC character that are dead wear no equipment
-- We could skip dead characters, but this doesn't feel right
-- Maybe add a disclaimer to search page stating the above
