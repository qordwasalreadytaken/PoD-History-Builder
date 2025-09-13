# PoD-History-Builder
Saving character data over time via build planner links

Downloads all ladder character to json file
    -Incomplete, using static file for build and test; need to add download ALL
Collect.py looks at downloaded character json file and:
    For each character
        Looks at skills and equipment and creates a build planner url that maps those skills and equips
        Maps that url to timestamp
    Creates/updates index.json that maps timestamp url's to character names
Search.html
    Searches index for character names
    Returns all links from the snapshot files

