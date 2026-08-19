import logging
from openai import OpenAI
import json
import re
from project_code.app_config.settings import app_settings
from project_code.utils.utils import is_intel, log_boxed
import time

class LlmCommandParser_V2:
    def __init__(self):

        base_url   = app_settings.llm.base_url
        self.model = app_settings.llm.llm_model

        if is_intel() is False:
            base_url   = re.sub(r'(localhost|127\.0\.0\.1)', 'host.docker.internal', base_url)
            self.model = "/models"

        self.client = OpenAI(
            api_key=app_settings.llm.api_key,
            base_url=base_url
        )

        with open("llm/mission_command_parser_v2.txt", "r", encoding="utf-8") as f:
            self.split_user_command_prompt = f.read()

        self.split_command_schema = {
            "type": "object",
            "properties": {
                "fly_command": {
                    "type": "object",
                    "properties": {
                        "fly_cmd_type": {
                            "type": "string",
                            "enum": ["fly", "surround", "follow", ""],
                        },
                        "location": {"type": "string"},
                    },
                    "required": ["fly_cmd_type", "location"],
                    "additionalProperties": False,
                },
                "vision_command": {
                    "type": "object",
                    "properties": {
                        "vision_cmd_type": {
                            "type": "string",
                            "enum": ["point", "hold", "summary", "describe", "follow", ""],
                        },
                        "objects": {"type": "string"},
                    },
                    "required": ["vision_cmd_type", "objects"],
                    "additionalProperties": False,
                },
                "team_member": {
                    "type": "string",
                    "enum": ["jarvis", "buddy", "team"],
                },
                "need_more_data": {"type": "boolean"},
            },
            "required": ["fly_command", "vision_command", "team_member", "need_more_data"],
            "additionalProperties": False,
        }

    def log_nicely(self, user_command, parsed_output, total_time):
        fly_command = parsed_output.get("fly_command", {})
        vision_command = parsed_output.get("vision_command", {})

        lines = [
            f"llm_time        = {total_time:.2f} seconds",
            f"team_member     = {parsed_output.get('team_member')!r}",
            f"fly_cmd_type    = {fly_command.get('fly_cmd_type')!r}, "
            f"location        = {fly_command.get('location')!r}",
            f"vision_cmd_type = {vision_command.get('vision_cmd_type')!r}, "
            f"objects         = {vision_command.get('objects')!r}",
            f"need_more_data  = {parsed_output.get('need_more_data')!r}",
        ]
        log_boxed(f"Parsed split_user_command for: '{user_command}'", lines)

    def split_user_command(self, user_command):

        try:
            start_time = time.time()
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.split_user_command_prompt},
                    {"role": "user", "content": f"USER COMMAND: {user_command}"}
                ],
                extra_body={
                    "reasoning_effort": "low",
                    "seed": 0,
                    "guided_json": self.split_command_schema,
                },
                temperature=0.0,
                max_tokens=300,
            )
            end_time = time.time()
        except Exception as e:
            logging.error(f"Error while calling llm: {e}")
            return []

        if response.choices[0].finish_reason != "stop":
            logging.error(f"LLM response finish reason: {response.choices[0].finish_reason}")

        raw_output = response.choices[0].message.content
        parsed_output = json.loads(raw_output)

        self.log_nicely(user_command, parsed_output, (end_time - start_time))

        return parsed_output


if __name__ == '__main__':

    llmCommandParser = LlmCommandParser_V2()
    start_time = time.time()
    res = llmCommandParser.split_user_command("Hey jarvis go to building number one, and point to the car or cow")
    end_time = time.time()
    print(f"Total time: {end_time - start_time:.2f} seconds")
    # for command in res:
    #     print(command)
    print(json.dumps(res, indent=4))
