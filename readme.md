# Scrape

## Dependencies
```bash
pip3 install openai
pip3 install selenium
pip3 install pyyaml
```

## Setup
OpenAI api key in `api_key.txt`. Put list of schools in `schools.txt`.

## Method
Pipeline:
1. Use selenium to search “contact email [school] singapore chemistry head of department hod”
2. Open the first 3 results and extract page text
3. Query gpt5-nano with:
```
Extract the email of the Chemistry Head of Department (HOD). 
If there is no explicit Chemistry HOD, choose the closest role in this order:
1. HOD Science
2. SH Chemistry
3. SH Science
4. Other close matches you are able to infer, excluding Principal, Vice Principal and faculty that do not have any subordinates. 

Output ONLY one line in this format:
"email; role_name"
or output "Not found". 

Prefer to format role_name as [designation, department] where possible, eg. “Head of Department, Chemistry” or “Subject Head, Science”. If there are no contact emails, or the page contains no close matches, output “not found”.
```