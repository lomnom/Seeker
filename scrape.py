import os
from openai import OpenAI
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from yaml import dump as yaml_dump
from json import loads
import atexit
import time
import csv
from time import perf_counter
import json

red = "\033[31m"
green = "\033[32m"
no_color = "\033[0m" 
START = perf_counter()
def log(*args, **kwargs):
    """Logs messages with a timestamp since startup. Same syntax as print."""
    timestamp = perf_counter() - START
    timestamp = round(timestamp, 2)
    timestamp = str(timestamp).ljust(8, " ") + "s"
    timestamp = f"[{timestamp}]" 
    timestamp = "\033[2m" + timestamp + "\033[22m" # make dim.

    print(timestamp, *args, **kwargs)

def init_openAI():
    """
    Creates an openai client `gpt` in global scope.
    """
    global gpt
    with open("api_key.txt", 'r') as key_file:
        gpt = OpenAI(
            api_key=key_file.read()
        )

def ask_gpt(text: str, school: str) -> (dict, dict):
    """
    Prompt GPT to extract email and relevant info from text.
    Returns extracted, response_info, input
    extracted = {
        "email": ...,
        "role": ...,
    } OR "Not found" OR "Token budget exceeded"
    response_info = response.to_json
    """

    prompt = f"""
    From the webpage pasted below, extract the email of the Mathematics (Math) Head of Department (HOD)
    in **{school}**. 
    If there is no explicit Mathematics HOD, choose the closest role in this order:
    1. Subject Head (SH) Mathematics
    2. Lead Teacher Mathematics
    3. Head Teacher Mathematics
    4. Senior Teacher Mathematics
    5. Explicitly exclude non-teaching roles. DO NOT include any teacher not related to Mathematics, 
       eg. Science, Special Project, Computing

    Output ONLY one line in this format:
    "email; role_name"
    or output "Not found". 

    Prefer to format role_name as [designation, department] where possible, eg. 
    “Head of Department, Math or “Subject Head, Math. 
    If there are no contact emails, or the page contains no close matches, output “Not found”.
    """

    input = [
        {
            "role": "system",
            "content": [
                {
                    "type": "input_text", 
                    "text": "You are a meticulous AI tasked with extracting information from a page."
                }
            ]
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": prompt
                }
            ]
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": text
                }
            ]
        }
    ]

    # Prompt caching is implicit.
    response = gpt.responses.create(
        model="gpt-5-nano",
        input=input,
        max_output_tokens=2500 # Includes reasoning tokens
    )

    # Process response text
    output = response.output_text
    if response.status != "completed":
        result = "Token budged exceeded"
    elif "not found" in output.lower():
        result = "not found"
    else:
        try:
            email, role = output.split(";")
            email, role = email.strip(), role.strip()
            result = {"email": email, "role": role}
        except:
            result = "Invalid response"

    return result, json.loads(response.to_json()) # lol

# You need to set this firefox profile.
profile_file = '/Users/user/Library/Application Support/Firefox/Profiles/3jof0ins.default-release'
def init_selenium():
    """
    Creates a selenium webdriver in global scope, as `driver`
    """
    global driver

    log("Starting webdriver...")
    driver = webdriver.Firefox()
    
    driver.set_window_size(767, 767) # Non-default viewport.

    # Remove huge red warning sign
    # driver.execute_cdp_cmd(
    #     "Page.addScriptToEvaluateOnNewDocument",
    #     {
    #         "source": """
    #         Object.defineProperty(navigator, 'webdriver', {
    #             get: () => undefined
    #         })
    #         """
    #     }
    # )

    atexit.register(driver.quit) # Quit driver on exit

    log("Selenium init done.")

def search_engine(school: str) -> list:
    """
    Search for a school email page.
    Returns a list of three search results, from first to last.
    Each search result is (url, text)
    """
    # Do search (wow this search query was a pain to refine)
    search = [
        f'email address Mathematics head of department HOD {school}',
        f'email address Math head of department HOD {school}',
        f'email address "Mathematics" head of department HOD {school}'
    ]

    pages = []
    # Get first three search results of each query.
    for query in search:
        # Ping duckduckgo with the query
        success = False
        while not success:
            try:
                driver.get(f'https://www.ddg.gg/search?q={query}')
            except Exception as e:
                log(repr(e) + f" encountered on search query {query}! Trying again in 30s")
                time.sleep(30)
            else:
                success = True
        driver.implicitly_wait(3) # Wait till page fully loads before proceeding

        # Get first three search result links
        search_urls = []
        for i in range(3):
            result = driver.find_element(By.ID, f'r1-{i}') 
            link = result.find_element(By.CSS_SELECTOR, '[data-testid="result-title-a"]')
            url = link.get_attribute("href")
            search_urls.append(url)

        # Fetch text from each search result
        for search_url in search_urls:
            # Specially blacklisted useless sites
            blacklist = ["zoominfo", "contactout", "datanyse"]
            skip = False
            for item in blacklist:
                if item in search_url:
                    log(f"Skipping blacklisted source {item} in {search_url}")
                    skip = True
                    break
            if skip:
                continue

            try:
                # Open search result
                driver.get(search_url)
                # Wait till page fully loads before proceeding
                driver.implicitly_wait(3) 

                # Add all links to visible text so that page.text includes <a href=email> emails
                links = driver.find_elements(By.TAG_NAME, "a")

                for link in links:
                    href = link.get_attribute("href")
                    text = link.text.strip()
                    if href:
                        new_text = f"{text} [{href}]"
                        # Use JS to modify the page content
                        driver.execute_script("arguments[0].textContent = arguments[1];", link, new_text)
                
                # Extract page text
                try:
                    # Where the page content lives in most MOE sites
                    page = driver.find_element(By.CLASS_NAME, 'content')
                except:
                    # Not found, fallback to whole body
                    page = driver.find_element(By.TAG_NAME, 'html')
                
                page = page.text
                pages.append((driver.current_url, page))
            except Exception as e:
                log(repr(e) + f" encountered on {driver.current_url}!")
                # Usually some fast-evolving page that isnt the correct one anyway 
                # causing stale element errors
    
    return pages

# init_selenium()
# for page in search_engine("Pei Hwa Secondary School"):
#     print(page)

out_dir = "./output/" # Must put a trailing /
csv_headers = ["school", "email", "role", "source"]
def write_csv(row: dict):
    """
    Append one row to the csv.
    Flush instantly.
    """
    with open(out_dir + "results.csv", 'a') as outfile:
        out_csv = csv.DictWriter(outfile, fieldnames = csv_headers)
        out_csv.writerow(row)

def process_school(school: str):
    """
    Email extraction pipeline:
    - For the school,
    1. Use selenium to search for pages whch may have the emails and extact page content
    3. Query gpt5-nano to get page contents.

    Write to out_dir:
    1. results.csv:
    - school | email | role | source
    - In error cases email, role and source will be empty.
    2. logs/(schoolname).yaml:
    - Includes LLM output for that school.
    - Includes the page content
    """
    log(f"Working on {school}...")

    logs = [] # To write to the log yaml.
    success = False
    for url, page in search_engine(school):
        log(f"Searching for emails in page {url}...")

        result, full_info = ask_gpt(page, school)
        logs.append({"url": url, "result": result, "full_info": full_info})

        if type(result) is str:
            log(f"Failure! {result}.")
            continue # Not successful
        else:
            # Successful!
            result = {
                "school": school,
                "email": result["email"],
                "role": result["role"],
                "source": url,
            }
            write_csv(result)
            success = True
            log(f"{green}Success! {result}{no_color}")
            break
    
    if not success:
        write_csv({
            "school": school,
            "email": "",
            "role": "",
            "source": "",
        })
        log(f"{red}Emails for {school} could not be found...{no_color}")
    
    with open(out_dir + "logs/" + school.replace(' ', '-') + '.yaml' , 'w') as logfile:
        logfile.write(yaml_dump(logs))

def main():
    """
    Main program. Processes all schools.
    """
    log("Initialising...")

    # Make sure some outfiles exist already
    os.makedirs(os.path.dirname(out_dir), exist_ok=True)
    os.makedirs(os.path.dirname(out_dir + "logs/"), exist_ok=True)

    with open(out_dir + "results.csv", 'w') as outfile:
        out_csv = csv.DictWriter(outfile, fieldnames = csv_headers)
        out_csv.writeheader()

    # Get all schools we are working on
    schools = []
    with open("schools.txt", 'r') as in_file:
        for line in in_file.readlines():
            line = line.strip()
            if line == '':
                continue

            schools.append(line)
    
    # Init pipeline components
    init_selenium()
    init_openAI()

    log("Initialised!")

    # Work on each school
    for school in schools:
        process_school(school)

main()