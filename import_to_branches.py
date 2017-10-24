import os
import json
import zipfile
import csv
import base64
from collections import OrderedDict

import requests
import datetime

try:
    GITHUB_TOKEN = os.environ['GITHUB_TOKEN']
except:
    print("need GITHUB_TOKEN")
    raise

register_codelist = "business_register_codelist.csv"
list_already_exist_on_master = []
branch_already_exist = []


with open('list-template.json', 'r') as myfile:
    list_template = json.load(myfile)


def codelist_to_github(register_codelist):
    keys = ['country', 'iso-code', 'list-code', 'structure/0', 'structure/1', 'structure/2', 'list type', 'name/en', 'name/local', 'url', 'description', 'access/availableOnline', 'access/exampleIdentifiers', 'access/onlineAccessDetails', 'access/guidanceOnLocatingIds']
    with open(register_codelist, "r", encoding="utf-8") as reg_file:
        csvreader = csv.DictReader(reg_file)
        org_list = list_template

        for i, row in enumerate(csvreader):
            prefix = row['list-code']
            org_list['coverage'] = [row['iso-code']]
            org_list['code'] = prefix
            org_list['structure'] = [row['structure/0']]
            if row['structure/1']:
                org_list['structure'].append(row['structure/1'])
            if row['structure/2']:
                org_list['structure'].append(row['structure/2'])
            org_list['listType'] = row['list type']
            org_list['name']['en'] = row['name/en']
            org_list['name']['local'] = row['name/local']
            org_list['url'] = row['url']
            org_list['description']['en'] = row['description']
            if(org_list['access']['availableOnline'] == 'TRUE'):
                org_list['access']['availableOnline'] = True
            if(org_list['access']['availableOnline'] == 'FALSE')):
                org_list['access']['availableOnline'] = False
            org_list['access']['exampleIdentifiers'] = row['access/exampleIdentifiers']
            org_list['access']['onlineAccessDetails'] = row['access/onlineAccessDetails']
            org_list['access']['guidanceOnLocatingIds'] = row['access/guidanceOnLocatingIds']
            edit_details(prefix, org_list)


def git_create_branch(branch):
    # ToDo - Add error handling
    if(GITHUB_TOKEN):
        headers={"Authorization":"token " + GITHUB_TOKEN}
    else:
        headers={}

    r = requests.get("https://api.github.com/repos/BobHarper1/register/branches/master",
        headers=headers)
    master_sha = r.json()['commit']['sha']

    payload = {
        "ref":"refs/heads/" + branch,
        "sha":master_sha
    }

    r = requests.post("https://api.github.com/repos/BobHarper1/register/git/refs", headers=headers,
    data=json.dumps(payload))

    return r


def git_pull_request(prefix, org_list):
    if(GITHUB_TOKEN):
        headers={"Authorization":"token " + GITHUB_TOKEN}
    else:
        headers={}

    message = "A new list has been proposed with the code " + prefix
    title_context = "New "
    message = message + "\n\n" + "**List title:** " + org_list['name']['en']
    message = message + "\n\n Preview the platform with this list at [http://org-id.guide/_preview_branch/" + prefix + "](http://org-id.guide/_preview_branch/" + prefix + ") "
    message = message + " (visiting [http://org-id.guide/list/" + prefix + "](http://org-id.guide/list/" + prefix + ") when the preview is active"
    message = message + " or check the files changed options above."
    message = message + "\n\n" + "Unless objections are raised, this update will be merged after 7 days."

    payload = {
        "title":title_context + " registry entry for '" + org_list['name']['en'] + "' (" + prefix +")",
        "body":message,
        "head":prefix,
        "base":"master"
    }

    r = requests.post("https://api.github.com/repos/BobHarper1/register/pulls",
            headers=headers,
            data=json.dumps(payload))

    return r

def check_branch_exists(prefix, headers):
    r = requests.get("https://api.github.com/repos/BobHarper1/register/branches/" + prefix, headers=headers)
    print(r.json())
    if('name' in r.json()):
        return True

def check_list_exists_on_master(folder, prefix, headers):
    try:
        r = requests.get("https://api.github.com/repos/BobHarper1/register/contents/lists/" + folder + "/" + prefix.lower() + ".json?ref=master",
        headers=headers)
        if('name' in r.json()):
            return True
    except:
        pass

def edit_details(prefix, org_list):
    use_branch = 'master'
    folder = prefix.split("-")[0].lower()
    sha = ""
    message = ""
    existing_edits = False
    pull_request = ""
    if(GITHUB_TOKEN):
        headers={"Authorization":"token " + GITHUB_TOKEN}
    else:
        headers={}

    string_list = json.dumps(org_list, sort_keys=True, indent=4, separators=(',', ': '))

    payload = {
        "content":base64.b64encode(bytes(string_list,'utf-8')).decode(),
        "message":"Updating " + prefix + " from list-to-branches",
        "committer":{
            "name":"org-id.guide user",
            "email":"contact@org-id.guide"
        },
        "branch":prefix
    }

    # Check if the branch already exists
    if(check_branch_exists(prefix, headers)):
        print("branch", prefix, "already exists")
        branch_already_exist.append(prefix)
    # We also need to check if this list already exists on the master branch
    elif(check_list_exists_on_master(folder, prefix, headers)):
        print("list", prefix, "already exists on master")
        list_already_exist_on_master.append(prefix)
    else:
        # We need to create the branch
        r = git_create_branch(prefix)
        print('CREATING BRANCH',r.json())

        r = requests.put("https://api.github.com/repos/BobHarper1/register/contents/lists/" + folder + "/" + prefix.lower() + ".json",
            headers=headers,
            data=json.dumps(payload))

        print(r.json())

        try:
            pull_request = git_pull_request(prefix, org_list)
            print(pull_request, ": ", prefix, org_list)
        except Exception as e:
            print(e)
            pass

    ## ToDo: Report back to the user on the updates...
    ## ToDo: Report back to the user on any errors...

if __name__ == '__main__':
    codelist_to_github(register_codelist)
    print("BRANCHES ALREADY EXIST:",branch_already_exist)
    print("LISTS ALREADY EXIST ON MASTER:",list_already_exist_on_master)
