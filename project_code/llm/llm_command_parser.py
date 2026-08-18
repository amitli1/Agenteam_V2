import logging
from openai import OpenAI
import json
import re
from project_code.app_config.settings import app_settings
from project_code.utils.utils import is_intel, log_boxed
import time

class LlmCommandParser:
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

        with open("llm/prompt_split_command_concise.txt", "r", encoding="utf-8") as f:
            self.split_user_command_prompt = f.read()

        # JSON schema used to constrain the model output (guided decoding).
        # The model must return an array of sub-command objects.
        self.split_command_schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "team_member": {
                        "type": "string",
                        "enum": ["jarvis", "buddy", "team", ""],
                    },
                    "fly_command": {"type": "string"},
                    "vision_command": {"type": "string"},
                },
                "required": ["team_member", "fly_command", "vision_command"],
                "additionalProperties": False,
            },
        }


    def log_nicely(self, user_command, parsed_output, total_time):
        lines = [
            f"[{i}] team_member={cmd.get('team_member')!r}, "
            f"fly_command={cmd.get('fly_command')!r}, "
            f"vision_command={cmd.get('vision_command')!r}"
            for i, cmd in enumerate(parsed_output)
        ]
        lines.append(f"llm_time: {total_time:.2f} seconds")
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
                max_tokens=150,
            )
            end_time = time.time()
        except Exception as e:
            logging.error(f"Error while calling llm: {e}")
            return []

        # usage = response.usage
        # logging.info(
        #     f"tokens - prompt: {usage.prompt_tokens}, "
        #     f"completion: {usage.completion_tokens}, "
        #     f"total: {usage.total_tokens}"
        # )
        #logging.info(f'Split user command (with LLM) took {(end_time - start_time):.2f} seconds')
        if response.choices[0].finish_reason != "stop":
            logging.error(f"LLM response finish reason: {response.choices[0].finish_reason}")

        raw_output = response.choices[0].message.content
        parsed_output = json.loads(raw_output)

        self.log_nicely(user_command, parsed_output, (end_time - start_time))

        return parsed_output


if __name__ == '__main__':

    llmCommandParser = LlmCommandParser()
    res = llmCommandParser.split_user_command("Hey jarvis go to building number one, and point to the car or cow")
    #res = llmCommandParser.split_user_command("Hey team fly to junction number five, surround it and tell me what you see")
    #res = llmCommandParser.split_user_command("Buddy describe")
    #res = llmCommandParser.split_user_command("Buddy return home")
    #res = llmCommandParser.split_user_command("hey team go home")
    res = llmCommandParser.split_user_command('Hey jarvis Hold the junction and look for weapons')
    # res = llm_Manager.split_user_command("Hey")
    # res = llm_Manager.split_user_command("Buddy to back to home")
    for command in res:
        print(command)

    # command: Hey jarvis Hold the junction and look for weapons
    # result :
# {'team_member': 'jarvis', 'fly_command': '', 'vision_command': 'Hold the junction'}
# {'team_member': 'jarvis', 'fly_command': '', 'vision_command': 'look for weapons'}
