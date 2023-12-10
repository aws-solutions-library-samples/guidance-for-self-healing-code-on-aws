import json
import re


def remove_newlines(json_string):
    """Remove newline characters if they aren't enclosed in double quotes."""
    result = json_string
    result = re.sub('(?<!")\\n', "", result)
    result = re.sub("\\n(?= *})", "", result)
    return result


class Model:
    """Model class for GenAI."""

    def fix_code(self, stack_trace, source_code_map):
        """Trigger the code fix generation process."""
        prompt = self._create_prompt(stack_trace, source_code_map)
        content = self._invoke(prompt)
        cleaned_content = self.clean_result(content)
        return json.loads(cleaned_content)

    def clean_result(self, content):
        """Clean the response from the model."""
        cleaned_result = content.replace("```", "")
        cleaned_result = remove_newlines(cleaned_result)
        cleaned_result = cleaned_result.strip()
        cleaned_result = cleaned_result.rstrip(",")
        # Replace \n with \\n to escape newlines in JSON
        cleaned_result = cleaned_result.replace("\n", "\\n")
        return cleaned_result
