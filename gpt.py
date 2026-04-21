"""
This module implements a simple way to ask gpt to extract information
from page text.

Put your openai api key in `api-key.txt` in the same folder as this file.
"""

from openai import OpenAI
import json
from typing import Callable
from pathlib import Path
from log import log

# https://stackoverflow.com/questions/4060221/
api_key_path = Path(__file__).with_name('api-key.txt')
with api_key_path.open('r') as key_file:
    API_KEY = key_file.read()

class GPT:
    """
    Provides abstractions to allow use of GPT to extract information from
    page text.
    """
    def __init__(self):
        with open("api-key.txt", 'r') as key_file:
            self.gpt = OpenAI(
                api_key=API_KEY
            )

    model = "gpt-5-nano"
    def ask_gpt(self, prompt: list, max_output_tokens: int = 2500) -> tuple:
        """
        See openai.OpenAI.responses.create input argument for prompt format.
        max_output_tokens includes reasoning tokens, making it high even if you 
        want short answers.

        Raises RuntimeError if token budget is exceeded.

        Returns response (text, full response json)
        """
        # Prompt caching is implicit.
        response = self.gpt.responses.create(
            model="gpt-5-nano",
            input=prompt,
            max_output_tokens=max_output_tokens # Includes reasoning tokens
        )

        # Process response text
        output = response.output_text
        if response.status != "completed":
            raise RuntimeError("Token budget exceeded!")

        return output, json.loads(response.to_json()) # lol
    
    def page_machine(self, prompt_str: str, output: list[str]) -> Callable:
        """
        Creates a function that takes in page text and uses gpt to extract info
        from it. GPT explicitly plays the role of information extractor.

        For the machine(page_info: str, subject: str) -> dict|None:
            Pass in the page info and the current subject the info is being collected 
            on (eg. Pei Cai Secondary).

            Output is a list of strings, like ["email", "role"], that defines what 
            the AI is to output.
            For the example above, the llm must only output one line like:
                haroldol_baller@school.com | Math HOD
            OR
                unsuccesful

            In the prompt text, {s} will be substituted for the subject.
            Eg. when subject is "Shuckity Secondary School",
                "Hi GPT, please find the Math HOD for {s}"
                --> Hi GPT, please find the Math HOD for Shuckity Secondary School

            If the reply is "unsuccessful" in any capitalisation, None is returned.
            Else, a dictionary like {"email": "haroldol_baller@school.com", "role": "Math HOD"}
            is returned.

            RuntimeError is raised by ask_gpt or if the response is incorrectly formatted.
        """

        def machine(page: str, subject: str) -> dict|None:
            """
            Constructed function. Pass in the page text and the current subject the info is
            being collected on (eg. Pei Cai Secondary).

            Refer to GPT.page_machine for full documentation.
            """
            nonlocal prompt_str, self, output

            log("GPT is processing the page...")

            prompt_str = prompt_str.replace("{s}", subject)
            prompt = [
                { # Note that role prompting locks AI into being info extractor.
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
                            "text": prompt_str
                        }
                    ]
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": page
                        }
                    ]
                }
            ]

            answer, meta = self.ask_gpt(prompt) # may throw RuntimeError.
            log(f"GPT answer: {answer}")
            if "unsuccessful" in answer.lower():
                return None
            else:
                items = answer.split("|")
                if len(items) != len(output):
                    raise RuntimeError(f"Number of items in response {answer} does not match output {output}!"
                                        "Incorrect response formatting?")

                result = {}
                for name, item in zip(output, items):
                    result[name] = item.strip()
                return result
        
        return machine

## To future me:
# gpt = GPT()
# machine = gpt.page_machine(
#     """
#     From the website pasted below, please extract the birthday of {s}.
#     Output nothing except one line, containing ONLY
#         full name | birthday
#     If not successful, output ONLY
#         unsuccessful
#     """,
#     ["full_name", "birthday"]
# )

# result = machine("""
# Office birthdays:
# - Hellman Ong: 11/11/1998
# - Shuckers Shuck: 11/01/1998
# - Ballsy Baller: 11/01/2008
# """, "ballsy")

# log(result)