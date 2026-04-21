"""
This module implements a simple way to ask gpt to extract information
from page text.
"""

from openai import OpenAI

class GPT:
    def __init__(self):
        self.gpt = OpenAI(
            api_key=key_file.read()
        )
    
    def ask_gpt(prompt: list):
        """
        See openai.OpenAI.responses.create for prompt format.

        Returns response text.
        """
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