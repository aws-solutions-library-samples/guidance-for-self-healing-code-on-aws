import boto3
from botocore.client import Config
from langchain.llms.bedrock import Bedrock
from langchain.prompts import PromptTemplate

from providers import Model
from utils import get_logger

config = Config(connect_timeout=240, read_timeout=240)


logger = get_logger()

DEFAULT_MODEL = "anthropic.claude-v2"
DEFAULT_MODEL_REGION = "us-east-1"
PROMPT_TEMPLATE = PromptTemplate(
    input_variables=["stack_trace", "source_code"],
    template="""
Human: 
You are a code debugging and fixing assistant.
You will debug stack traces to identify the issues in the provided source code.
Generate a modified version of the source code to prevent the error from occurring again.
Modify only the code relevant to the fix.
Provide a response in JSON format with the following keys:
- description: a description of the bug and how the modified code fixes it
- title: a title for the fix
- source_code: an array of modified file objects with "filename" and "contents" keys

<example code>

def get_key(dict, key):
    return dict[key]

</example code>
<example response>
{{
    "description": "Handle KeyErrors when the key does not exist in the dict",
    "title": "Handle KeyErrors in get_key",
    "source_code": [
        {{
            "filename": "src/foo.py",
            "contents": "def get_key(dict, key):\n    try:\n    value = dict[key]\n    except KeyError:\n        return None\n"
        }}
    ]
}}
</example response>

<code>
{source_code}
</code>
<stack_trace>
{stack_trace}
</stack_trace>

Assistant:{{
""",
)


class Claude(Model):
    """Claude model class."""

    def __init__(self, model_id=DEFAULT_MODEL, model_aws_region=DEFAULT_MODEL_REGION):
        bedrock_client = boto3.client(
            "bedrock-runtime",
            region_name=model_aws_region,
            config=config,
        )
        self.llm = Bedrock(
            client=bedrock_client,
            model_id=model_id,
            model_kwargs={
                "temperature": 0.0,
                "max_tokens_to_sample": 10000,
                "top_p": 0.999,
                "top_k": 250,
                "stop_sequences": [
                    "\\n\\nHuman::",
                ],
            },
        )
        logger.info("Initialized Claude")

    def _create_prompt(self, stack_trace, source_code_map):
        """Create a prompt for the model to generate a code fix."""
        logger.info("Creating prompt for model")
        source_code_parts = []
        for filename, source_code in source_code_map.items():
            source_code_parts.append(
                f"File: {filename}\n\nContents:\n{source_code}\n\n"
            )
        concatenated_source_code = "\n".join(source_code_parts)
        prompt = PROMPT_TEMPLATE.format(
            stack_trace=stack_trace, source_code=concatenated_source_code
        )
        return prompt

    def _invoke(self, prompt):
        """Invoke the model with the prompt."""
        logger.info(f"Prompt: {prompt}")
        response = self.llm(prompt)
        # Append opening curly braces which might be missing, depending on the prompt.
        if not response.startswith("{"):
            response = "{" + response
        logger.info(f"Raw response from GenAI: {response}")
        return response
