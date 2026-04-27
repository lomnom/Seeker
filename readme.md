# Scrape
This tool allows automation of the conventional web scraping workflow. If a human was to do it, they would:
-  Need some piece of information to be collected from a list of targets. 
  - eg. The color of each fruit in a list of fruits
- For each target, do these tedious steps:
    1. Use a search engine (like google) to enter some repetive prompt.
      - Eg. Color of {fruit}
    2. Read through the first few search results.
    3. If an answer is found, note it down somewhere.

This tool allows you to pass in a list of subjects, search queries and llm instructions to automate the scraping process cheaply.

## Install & dependencies
Run the following to install the tool and its dependencies.
```bash
# Dependencies (hopefully all of them lol)
pip3 install openai selenium pyyaml

# Tool
git clone https://github.com/lomnom/Seeker
cd Seeker
```

## Setup
Put your OpenAI api key in `Seeker/api_key.txt`. This tool uses the super cheap `gpt-5-nano` model, $5 in credits is more than enough for all uses.

## Usage
A seeker project is a folder which contains:
1. `subjects.txt`: A list of subjects, one on each line
2. `algo.yaml`: A file that defines search queries and prompts used to instruct an AI to extract information from webpages in search results.

Upon running `python3 scrape.py path/to/project_folder`, a `result.csv` file is produced to store results that the bot finds. Each row corresponds to the result for a subject. If a `result.csv` already exists and there is already data inside, the subjects for which data has already been collected will not be scraped for again.

### Simple example: Fruits
The `fruits` folder in this repository is an example of a seeker project. As expected, it contains the user-created `algo.yaml` and `subjects.txt`. Seeker has been run on this before with `python3 seeker.py fruits`, and the corresponding `result.csv` has been produced.

The purpose of this seeker project is to scrape the color of a list of fruits. Here, the subjects are fruits: the fruits to scrape for are listed in `subjects.txt`:
```txt
Apple
Pomelo
Pear
```

Snowy the Cat used to do the following tedious steps for each fruit:
1. Use a search engine to search "Color of the {fruit} fruit".
2. Read the top 3 result webpages one by one for the answer.
  - Due to a personal grudge, he skips results that have `reddit` anywhere in the link.
  - Specifically, if there is one reddit result among the top 3 results, he only ends up reading two pages.

To create a seeker bot that can do his work for him, snowy writes the following `algo.yaml`:
```yaml
- search-queries:
  - Color of the {s} fruit
  site-blacklist:
  - reddit
  top_n_results: 3
  prompt: '
    From the website pasted below, please extract the color of an {s}.
    Output nothing except one line, containing ONLY
        color
    If not successful, output ONLY
        unsuccessful'
  results:
  - color
```

Breakdown:
- `search-queries` specifies what the bot will search for
- `site-blacklist` specifies results that are skipped
- `top_n_results` specifies the top how many results the bot should read
- `prompt`:
  - For every search result the bot wants to read, it will:
    - Roughly speaking, open the website and copy all of its contents
    - Paste this `prompt` followed by the website contents into ChatGPT.
    - Expect a single line, with a result like `red` or `blue`
- For both the search query and the prompt, `{s}` is replaced with the relevant subject when used:
  - eg. `Color of the {s} fruit` --> `Color of the Apple fruit` when apple is being scraped
- `results`: After ChatGPT replies with that single line, the bot needs to know the format of this line to be able to write `result.csv`.
  - When the bot just replies with one thing (color in this case), just `- color` is listed.

How are results written to `result.csv`?
- Let's say for the subject `Apple`, the answer was found on the website `apples.com` where GPT replied `red`.
- Since `result` only has one item, `color`, the bot will write the following row:
```
subject   | color    | src_1
----------+----------+------------
Apple     | red      | apples.com
```
If the bot was unsuccessful, an empty row would be added,

With this `algo.yaml` and `subjects.txt` in the `fruits` project folder, Snowy can run `python3 scraper.py fruits` to get the colors of all his fruits.

### Full example: SomeIC
In a certain SomeIC event, the Math HOD and ICT HOD emails of a list of singaporean schools had to be obtained. 

The `someic` folder in this repository contains the actual `algo.yaml` file used, and a sample `subjects.txt` and `result.csv` containing 10 random schools.

A simplified version of the `algo.yaml` used is shown below:
```yaml
- prompt: '
    From the webpage pasted below, extract the email of the Mathematics (Math) Head of Department (HOD)
    in {s}. 

    Output nothing except one line, containing ONLY
        email | role name
    If not successful (eg. no contact emails for specifically {s}, or the page contains no close matches), output ONLY
        unsuccessful
    
    Prefer to format role_name like "Head of Department, Math"'
  results:
  - math_email
  - math_role
  search-queries:
  - email address Mathematics head of department HOD {s}
  - email address Math head of department HOD {s}
  site-blacklist:
  - zoominfo
  - contactout
  top_n_results: 3

- prompt: '
    From the webpage pasted below, extract the email of one individual.
    
    You are tasked to find the email of the {s} Head of Department (HOD) in
    Information and Communications Technology (Infocomm/ICT) 

    Output nothing except one line, containing ONLY
        email | role name
    If not successful (eg. no contact emails for specifically {s}, or the page contains no close matches), output ONLY
        unsuccessful

    Prefer to format role_name like "Head of Department, ICT"'
  results:
  - comp_email
  - comp_role
  search-queries:
  - email address Information and Communications Technology HOD {s}
  - email address ICT head of department HOD {s}
  site-blacklist:
  - zoominfo
  - contactout
  top_n_results: 3
  try_last: true
```

This `algo.yaml` takes full advantage of the features in seeker. Let us go through several things.

**1:** It looks like there are two `algo.yaml`s typed one after the other. Each such block is referred to as a `component`. When multiple `component`s are chained together, it means that for each subject the components will execute one by one. In this case, for each school, the Math HOD will be found followed by the ICT HOD.

**2:** There are multiple search prompts listed! The bot will try them one-by-one, starting from the first, reading the top n results for each search till an answer is found. In this case for the math component, the bot will try reading the top 3 results to `email address Mathematics head of department HOD {s}`, and if an answer has not been found yet, try reading the top 3 results for `email address Math head of department HOD {s}`.

**3:** There are multiple `site-blacklists`. Intuitively, this means that a site containing ANY of the blacklisted strings will be skipped.

**4:** The `try_last` flag is not required and can be excluded. If it is included and set to `true`, it means that for this component, try finding an answer from the page which an answer was found from for the previous component. In case, let's say that the math HOD for balls school was found at `schoolballs.com/staff`. Since `try_last` is true for the ICT component, the first link that the ICT component will try to find an answer from will be `schoolballs.com/staff`. This is quite useful in this case as schools often have all staff emails on the same page. This flag will not work in the first component for obvious reasons. 

**5:** To get the AI to return multiple pieces of information, the response must be formatted as `info_1 | info_2 | info_3 | ...`. These corresponding return values are listed in order in the results section (left-to-right in the prompt response --> top to bottom in the results list).

**6:** So what is the output fieldname format? The general pattern is:
```
subject | component 1 result columns | src_1 | component 2 result columns ...
```

In this case, it is:
```
subject,math_email,math_role,src_1,comp_email,comp_role,src_2
```

### More?
These examples should have covered all that seeker has to offer as of now. For further details, email me at `zhaoxiong.ang@gmail.com` or just read the source code at `scrape.py` lmao. 

## Technical details
A selenium webbrowser instance (Firefox) is spawned.

For each subject:
1. duckduckgo is opened and search result links are obtained.
2. Each relevant search result webpage is opened and converted to text through the selenium API.
3. The OpenAI API is called through the python wrapper

### Files
- `web.py` is solely for spawning and using a selenium webbrowser instance to get search result links from duckduckgo and open search result pages.
- `gpt.py` is solely responsible for defining a function constructor that takes in a prompt and returns a function that accepts webpage data and returns GPT response.
- `scrape.py` is responsible for utilising web and gpt to run `algo.yaml` on `subjects.txt` to create `result.csv`