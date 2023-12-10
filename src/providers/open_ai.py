import json

import openai

from providers import Model
from utils import get_logger

logger = get_logger()

DEFAULT_MODEL = "gpt-3.5-turbo"
DEFAULT_TEMPERATURE = 0
SYSTEM_PROMPT = """
You are a code debugging assistant.
You will be provided with a piece of Python 3 source code and a Sentry stack trace.
Your objective is to debug stack traces and produce code fixes.
Do not include any content in the response outside of the JSON object.
You will generate the description of the bug and the Python 3 source code to fix the bug.
Keep the ordering of the functions and classes in the source code in tact.
Provide a response in JSON format with the following keys:
- description
- title
- source_code

Example response format:
```
{
    "description": "The get_dict_value function is missing a return statement. Add a return statement to avoid TypeError",
    "title": "Add missing return statement",
    "source_code": [
        {
            "filename": "foo.py",
            "contents": "def get_dict_value():\\n    print(key)\\n    return obj[key]\\n\\ndef get_index_value(list, index):\\n    return list[index]"
        },
    ]
}
```
"""
USER_PROMPT = """
Sentry stack trace:
```
{stack_trace}
```
Source code:
```
{concatenated_source_code}
```
"""


class GPT(Model):
    """GPT model class."""

    def __init__(self, api_key, model=DEFAULT_MODEL, temperature=DEFAULT_TEMPERATURE):
        self.api_key = api_key
        self.openai = openai
        self.openai.api_key = api_key
        self.model = model
        self.temperature = temperature

    def _create_prompt(self, stack_trace, source_code_map):
        """Create a prompt for the model to generate a code fix."""
        logger.info("Creating prompt for GPT")
        source_code_parts = []
        for filename, source_code in source_code_map.items():
            source_code_parts.append(
                f"File: {filename}\n\nContents:\n{source_code}\n\n"
            )
        concatenated_source_code = "\n".join(source_code_parts)
        prompt = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": USER_PROMPT.format(
                    concatenated_source_code=concatenated_source_code,
                    stack_trace=stack_trace,
                ),
            },
        ]
        return prompt

    def _invoke(self, prompt):
        """Invoke the model with the prompt."""
        logger.info(
            f"Invoking OpenAI endpoint with model {self.model} and prompt:\n{prompt}"
        )
        response = self.openai.ChatCompletion.create(
            model=self.model,
            messages=prompt,
            temperature=self.temperature,
        )
        return response["choices"][0]["message"]["content"]
