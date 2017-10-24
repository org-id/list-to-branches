## Org-id.guide csv to branches

This script processes the file `business_register_codelist.csv` and maps the information against the org-id list schema to create a list json file with the relevant prefixes and contextual information.

It then creates a new branch on github for each list (named after the prefix) with the relevant lists committed, except those cases where:
* There is already an existing branch for that prefix code
* There is already a list with that prefix code on the `master` branch

Firstly, you will need to add a personal auth token to the environment: `export GITHUB_TOKEN="{token}"``

Then, run:
```
python3 import_to_branches.py  
```

At the end of the run the program will print out information about those branches/lists not created:
```
BRANCHES ALREADY EXIST: [ <branch prefixes> ]
LISTS ALREADY EXIST ON MASTER: [ <list prefixes> ]
```
