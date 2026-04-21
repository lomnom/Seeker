"""
Main program to run.

Run as python3 [path/to/folder]

In folder, there must be:
- algo.yaml
- subjects.txt

algo.yaml defines the scraping that should be done.
Something like
- prompt: '
    From the website pasted below, please extract the color of an {s}.
    Output nothing except one line, containing ONLY
        color
    If not successful, output ONLY
        unsuccessful
  '
  results:
  - color
  search-query:
  - Color of an {s}
  site-blacklist:
  - reddit
  top_n_results: 3
- {}

subjects.txt is a list of subjects that scraping is to be done on.
Eg, if you are scraping the colors of fruits,
    Apple
    Orange
    Pomelo
    Apricot

Workflow:
1. You have a list of subjects you want to collect the same type of info on.
  - Eg. fruits and their color.
2. For each subject, the bot:
  1. Uses a search engine to search various search queries
    - Color of an {fruit}
  2. Reads the top few results and passes the contents of each site into an llm one by one.
  3. For each site, the llm is asked your prompt, where the webpage is treated as being pasted below.
  3. The AI must be instructed to reply with only one line, either
     unsuccessful
     color

Full algo.yaml specification:

An algo.yaml notates a list of one or more components to extract.
A component is as follows
- prompt (str): Prompt to be passed to gpt
  results (list): 
  - A list of results the LLM gives back. 
  search-query (list): 
  - A list of search queries to try in order
  site-blacklist(list): 
  - sites that are ignored in search results
  top_n_results (int): The top how many results to try
  try_last (bool, optional): If we want to try using the site that was successful for the previous 
            component for this subject.
"""

import sys
from log import log, green, no_color
import yaml

def run_project(folder: str):
    

def main():
    """
    Entrypoint of the script.
    """
    project = sys.argv[1]
    log(f"Starting on project {project}!")

    run_project(project)