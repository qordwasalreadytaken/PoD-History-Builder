# PoD-History-Builder
Saving character data over time via build planner links

Downloads all ladder character to json file
    -Using same functions as the trends site downloads all ladder SC and HC data to one big json file, runs at 45 minutes past the hour, every hour

Collect.py looks at downloaded character json file and:
    For each character
        Looks at skills and equipment and creates a build planner url that maps those skills and equips
        Maps that url to timestamp
    Creates/updates index.json that maps timestamp url's to character names
    Runs at 1o minutes pas the hour, every hour
    
Search.html
    Searches index for character names
    Returns all links from the snapshot files

