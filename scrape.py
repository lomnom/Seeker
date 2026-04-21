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
  search-queries:
  - Color of a {s}
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

The program creates result.csv, in this case:
subject | color
Apple | Red
Orange | Orange
Pomelo | Pink
Apricot | Orange

Workflow:
1. You have a list of subjects you want to collect the same type of info on.
  - Eg. fruits and their color.
2. For each subject, the bot:
  1. Uses a search engine to search various search queries
    - Color of a {fruit}
  2. Reads the top few results and passes the contents of each site into an llm one by one.
  3. For each site, the llm is asked your prompt, where the webpage is treated as being pasted below.
  3. The AI must be instructed to reply with only one line, either
     unsuccessful
     color
3. The results are put into result.csv

Full algo.yaml specification:

An algo.yaml notates a list of one or more components to extract.
A component is as follows
- prompt (str): Prompt to be passed to gpt.
  results (list): 
  - A list of results the LLM gives back. If llm outputs teacher_name | teacher_role, it is
  - teacher_name
  - teacher_role
  search-queries (list): 
  - A list of search queries to try in order
  site-blacklist (list): 
  - sites that are ignored in search results
  top_n_results (int): The top how many results to try
  try_last (bool, optional): If we want to try using the site that was successful for the previous 
            component for this subject.

In the project folder, result.csv is created. The rows are:
subject | component 1 result columns | src_1 | component 2 result columns ...
"""

import sys
from log import log, green, red, no_color
from gpt import GPT
from web import WebInstance
import yaml
import csv
from typing import Callable

def scrape_subject(subject: str, algo: list, web: WebInstance, machines: list[Callable]) -> dict:
    """
    Scrape a single subject, given the page machines, algo and web instance.
    Returns a result dictionary, like a row in result.csv.
    """
    answer = {"subject": subject}
    log(f"Working on subject {subject}...")

    for i, step in enumerate(algo):
        step_result = None
        tried_last = False

        # #1: Search the queries
        for query in step["search-queries"]:
            # Actual search
            query = query.replace("{s}", subject)
            log(f"Searching {query} on duckduckgo...")
            results = web.search_engine(query, step["top_n_results"])

            # Insert last success if try_last and exists
            if "try_last" in step and step["try_last"] and i>0 and answer[f"src_{i}"] and not tried_last:
                tried_last = True
                results.insert(0, answer[f"src_{i}"])
                log("Trying successful source of previous component as try_last enabled.")

            # Look through results one by one
            for url in results:
                # Skip blacklists
                skip = False
                for blacklist in step["site-blacklist"]:
                    if blacklist in url:
                        skip = True
                if skip:
                    log(f"Skipping blacklisted site {url}")
                    continue

                # Good result
                text = web.page_text(url)
                if text is None:
                    continue # Some exception happened here.
                
                try:
                    result = machines[i](text, subject)
                except Exception as e:
                    log(f"GPT raised error {repr(e)}. Skipping this page.")
                    continue
                if result is not None:
                    # Success!
                    step_result = {**result, f"src_{i+1}": url}
                    break
            
            if step_result is not None:
                break
        
        # Add step result in.
        if step_result is None:
            step_result = {}
            for item in (step["results"] + [f"src_{i+1}"]):
                step_result[item] = ""
            log(f"Component #{i+1} failed... {step_result}", color = red)
        else:
            log(f"Component #{i+1} successful! {step_result}", color = green)
        
        answer = {**answer, **step_result}
    
    return answer

def fieldnames_from_algo(algo: list) -> list[str]:
    """
    This determines output fieldnames from an algo.
    """
    fieldnames = ["subject"]
    for i, component in enumerate(algo):
        for result in component["results"]:
            if result in fieldnames:
                log(
                    f"Error on result name {result}! results cannot repeat or be named subject.", color = red
                )
                quit()
            fieldnames.append(result)
        fieldnames.append(f"src_{i+1}")
    return fieldnames

def run_scraper(subjects: list[str], algo: list, submit_result: Callable):
    """
    Run the scraper for all subjects passed.
    Creates WebInstance and site machines
    """
    # Create site_machines.
    gpt = GPT()
    machines = []
    for component in algo:
        machines.append(
            gpt.page_machine(
                component["prompt"], component["results"]
            )
        )
    log("Site machines created", color = green)

    # Create WebInstance
    web = WebInstance()

    for subject in subjects:
        try:
            result = scrape_subject(subject, algo, web, machines)
        except Exception as e:
            log(f"Exception {repr(e)} encountered on subject {subject}!", color=red)
            result = {}
            for field in fieldnames_from_algo(algo):
                result[field] = "internal error"
            result["subject"] = subject
        submit_result(result)


def get_csv(folder: str, fieldnames: list[str]) -> tuple:
    """
    Returns the old data (list of dictionaries) and a csv writer
        (old_data, writer, file_obj)
    object. Does not destroy old results.
    """
    outpath = folder + "result.csv"
    old_data = []
    try:
        with open(outpath) as outfile:
            reader = csv.DictReader(outfile)
            if reader.fieldnames != fieldnames:
                log(f"Error: Fieldnames in old result.csv and new do not match! Delete old?", color = red)
                quit()
            for row in reader:
                old_data.append(row)
        log(f"{len(old_data)} previous results found. Bringing forward.", color = green)

        outfile = open(outpath, 'a')
        writer = csv.DictWriter(outfile, fieldnames = fieldnames)
    except FileNotFoundError:
        outfile = open(outpath, 'w')
        writer = csv.DictWriter(outfile, fieldnames = fieldnames)
        writer.writeheader()

    return old_data, writer, outfile

def run_project(folder: str):
    """
    Runs a scraping project, given the path to the project folder.
    """
    if not folder.endswith("/"):
        folder = folder + "/"

    # Read in subjects.
    with open(folder + "subjects.txt") as subjects_file:
        subjects = subjects_file.read()
        subjects = subjects.strip().split("\n")
    
    # Parse in the algo yaml.
    with open(folder + "algo.yaml") as algo_file:
        algo = algo_file.read()
        algo = yaml.safe_load(algo)
    
    log("Successfully parsed subjects and algo.", color = green)
    
    # Obtain csv writer and current results
    fieldnames = fieldnames_from_algo(algo)
    
    old_data, csv_writer, outfile = get_csv(folder, fieldnames)
    log("Initialised csv.", color = green)

    # What to skip as we have already found result.
    to_skip = set()
    for item in old_data:
        to_skip.add(item["subject"])
    current = []
    for subject in subjects:
        if subject not in to_skip:
            current.append(subject)

    # Cook
    def submit_result(result: dict):
        csv_writer.writerow(result)
        outfile.flush()
    run_scraper(current, algo, submit_result)

    # Not really needed but feels right eh
    outfile.close() 


def main():
    """
    Entrypoint of the script.
    """
    project = sys.argv[1]
    log(f"Starting on project {project}!")

    run_project(project)

if __name__ == "__main__":
    main()