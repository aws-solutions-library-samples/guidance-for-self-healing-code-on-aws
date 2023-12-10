import boto3
from langchain.llms.bedrock import Bedrock
from langchain.prompts import PromptTemplate

from providers import Model
from utils import get_logger

logger = get_logger()

DEFAULT_MODEL = "anthropic.claude-v1"
DEFAULT_MODEL_REGION = "us-east-1"
PROMPT_TEMPLATE = PromptTemplate(
    input_variables=["stack_trace", "source_code"],
    template="""
Human: You are a code debugging assistant.
You will first debug stack traces to identify the issues in the provided source code.
You will be provided with a piece of Python 3 source code and a stack trace to generate your response.
<code>
{source_code}
</code>
<stack_trace>
{stack_trace}
</stack_trace>
You will generate complete source code with the fixes for different issues and error handling.
You will provide a response in JSON format with the following keys:
- description: a description of the bug
- title
- source_code: an array of file objects with "filename" and "contents" keys
Here is an example of a JSON format. Your response should be formatted to this json response without any free text.
{{
    "description": "This code is missing a return statement",
    "title": "Add missing return statement",
    "source_code": [
        {{
            "filename": "foo.py",
            "contents": "def foo(): return 'foo'"
        }},
        {{
            "filename": "bar.py",
            "contents": "def bar(): return 'bar'"
        }}
    ]
}}
""",
)


class Claude(Model):
    """Claude model class."""

    def __init__(self, model_id=DEFAULT_MODEL, model_aws_region=DEFAULT_MODEL_REGION):
        bedrock_client = boto3.client("bedrock-runtime", region_name=model_aws_region)
        self.llm = Bedrock(
            client=bedrock_client,
            model_id=model_id,
            model_kwargs={
                "temperature": 0.0,
                "max_tokens_to_sample": 2048,
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
        logger.info(f"Raw response from GenAI: {response}")
        return response
