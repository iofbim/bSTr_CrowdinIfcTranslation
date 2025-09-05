# to learn the project number of the crowdin project. For enterprise crowdin project please use
# credentials to be stored at root of the python script in .env file with
# CROWDIN_PERSONAL_TOKEN=123asd123asd # add your personal access token here with 
# ORGANIZATION=firstpart # of the link to project. firstpart.crowdin.com

import os
from dotenv import load_dotenv
from crowdin_api import CrowdinClient

# Load variables from .env file
load_dotenv()

class MyClient(CrowdinClient):
    TOKEN = os.getenv("CROWDIN_PERSONAL_TOKEN")
    ORGANIZATION = os.getenv("ORGANIZATION")

client = MyClient()

# Example: list projects
projects = client.projects.list_projects()
for p in projects["data"]:
    print(f"{p['data']['id']} - {p['data']['name']}")
