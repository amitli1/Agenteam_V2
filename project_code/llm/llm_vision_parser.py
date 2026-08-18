import json
import logging

from openai import OpenAI
import time

from project_code.utils.utils import log_boxed

logger = logging.getLogger(__name__)


class VisionParser:
    """
    Uses an LLM to parse a free-text user command into structured vision commands.

    Supported vision commands: 'point', 'hold', 'summary', 'describe'
    """


    def __init__(
        self,
        model_name: str = "openai/gpt-oss-20b",
        base_url: str = "http://localhost:8090/v1",
        api_key: str = "EMPTY"

    ):

        self.model_name = model_name
        self.client = OpenAI(base_url=base_url, api_key=api_key)

        with open("llm/vision_parser_prompt.txt", "r", encoding="utf-8") as f:
            self.system_prompt = f.read()

        # JSON schema used to constrain the model output (guided decoding).
        self.vision_command_schema = {
            "type": "object",
            "properties": {
                "vision_commands": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "enum": ["point", "hold", "summary", "describe"],
                            },
                            "objects": {
                                "type": "string",
                                "description": "Comma-separated objects to focus on, or empty string if none specified.",
                            },
                            "need_more_data": {"type": "boolean"},
                        },
                        "required": ["command", "objects", "need_more_data"],
                        "additionalProperties": False,
                    },
                }
            },
            "required": ["vision_commands"],
            "additionalProperties": False,
        }

    def log_nicely(self, user_command, parsed_output, total_time):
        commands = parsed_output.get("vision_commands", [])
        if not commands:
            lines = ["No vision commands parsed."]
        else:
            lines = [
                f"[{i}] command={cmd.get('command')!r}, "
                f"objects={cmd.get('objects')!r}, "
                f"need_more_data={cmd.get('need_more_data')!r}"
                for i, cmd in enumerate(commands)
            ]
        lines.append(f"llm_time: {total_time:.2f} seconds")
        log_boxed(f"Parsed vision_commands for: '{user_command}'", lines)

    def parse(self, user_command: str) -> dict:
        try:
            start_time = time.time()
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"USER COMMAND: {user_command}"},
                ],
                extra_body={
                    "reasoning_effort": "low",
                    "seed": 0,
                    "guided_json": self.vision_command_schema,
                },
                temperature=0.0,
                max_tokens=150,
            )
            end_time = time.time()
            if response.choices[0].finish_reason != "stop":
                logging.error(f"LLM response finish reason: {response.choices[0].finish_reason}")

            raw_output    = response.choices[0].message.content
            parsed_output = json.loads(raw_output)
            self.log_nicely(user_command, parsed_output, end_time - start_time)
            return parsed_output
        except Exception as e:
            logger.error(f"VisionParser.parse failed: {e}")
            return {"vision_commands": []}


if __name__ == "__main__":
    vision_parser = VisionParser()

    examples = [
        # "point to the red car or blue truck",
        # "point",
        # "hold the junction",
        # "Hold the junction and look for weapons",
        "surround and tell me about vehicles and people you see",
        # "surround and tell me what you see",
        # "describe",
        # "describe the people",
    ]

    for text in examples:
        result = vision_parser.parse(text)
        print(f"command: {text}")
        print(f"result : {result}\n")