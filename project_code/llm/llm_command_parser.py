import logging
from openai import OpenAI
import json

from project_code.app_config.settings import app_settings



class LlmCommandParser:
    def __init__(self):
        self.client = OpenAI(
            api_key=app_settings.llm.api_key,
            base_url=app_settings.llm.base_url
        )
        self.model = app_settings.llm.llm_model
        with open("llm/prompt_split_command.txt", "r", encoding="utf-8") as f:
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


    def split_user_command(self, user_command):

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
            max_tokens=1000,
        )

        raw_output = response.choices[0].message.content
        parsed_output = json.loads(raw_output)
        return parsed_output


if __name__ == '__main__':

    llmCommandParser = LlmCommandParser()
    res = llmCommandParser.split_user_command("Hey jarvis go to building number one, and point to the car or cow")
    res = llmCommandParser.split_user_command("Hey team fly to junction number five, surround it and tell me what you see")
    res = llmCommandParser.split_user_command("Buddy describe")
    # res = llm_Manager.split_user_command("Hey")
    # res = llm_Manager.split_user_command("Buddy to back to home")
    for command in res:
        print(command)
