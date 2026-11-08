# GPT-OSS-20B (no clock):
```
Attaching to llm-tester
llm-tester  | [PASS] [3.3 sec] hey buddy fly to building number two
llm-tester  | [PASS] [2.2 sec] hey team fly home
llm-tester  | [PASS] [2.6 sec] hey jarvis surround the junction
llm-tester  | [PASS] [2.3 sec] hey jarvis surround the building and look for people and vehicles
llm-tester  | [PASS] [2.3 sec] hey jarvis hold the junction
llm-tester  | [PASS] [2.2 sec] buddy hold the junction and tell me if you see red car or blue truck
llm-tester  | [PASS] [2.2 sec] buddy follow the yellow car
llm-tester  | [PASS] [1.8 sec] hey team follow
llm-tester  | [PASS] [2.2 sec] buddy describe
llm-tester  | [PASS] [2.4 sec] buddy describe the person in the car
llm-tester  | [PASS] [2.2 sec] hey jarvis point at the yellow car
llm-tester  | [PASS] [3.3 sec] hey jarvis surround the building and tell me what you see hey jarvis look for birds
llm-tester  | [PASS] [3.8 sec] Hey team, walk around the building and describe to me what you see
llm-tester  | [PASS] [2.3 sec] Hey jarvis stop pointing
llm-tester  | [PASS] [5.1 sec] Hey team, hold the junction, if you see any vehicle follow it
llm-tester  | [PASS] [2.3 sec] Hey buddy stop following
llm-tester  | [PASS] [1.9 sec] Hey buddy hold
llm-tester  | 
llm-tester  | 17/17 tests passed.
```

# Phi3:
```

```

# Qwen3:
```
llm-tester  | [PASS] [1.4 sec] hey buddy fly to building number two
llm-tester  | [PASS] [1.4 sec] hey team fly home
llm-tester  | [PASS] [1.5 sec] hey jarvis surround the junction
llm-tester  | [PASS] [1.4 sec] hey jarvis surround the building and look for people and vehicles
llm-tester  | [PASS] [1.3 sec] hey jarvis hold the junction
llm-tester  | [PASS] [1.4 sec] buddy hold the junction and tell me if you see red car or blue truck
llm-tester  | [PASS] [1.4 sec] buddy follow the yellow car
llm-tester  | [PASS] [1.3 sec] hey team follow
llm-tester  | [PASS] [1.3 sec] buddy describe
llm-tester  | [PASS] [1.4 sec] buddy describe the person in the car
llm-tester  | [PASS] [1.3 sec] hey jarvis point at the yellow car
llm-tester  | [FAIL] [1.4 sec] hey jarvis surround the building and tell me what you see hey jarvis look for birds
llm-tester  |     expected: {'fly_command': {'fly_cmd_type': 'surround', 'location': 'building'}, 'vision_command': {'vision_cmd_type': 'summary', 'vision_cmd_action': 'start', 'objects': 'birds'}, 'team_member': 'jarvis', 'need_more_data': False}
llm-tester  |     actual  : {'fly_command': {'fly_cmd_type': 'surround', 'location': 'building'}, 'vision_command': {'vision_cmd_type': 'summary', 'vision_cmd_action': 'start', 'objects': ''}, 'team_member': 'jarvis', 'need_more_data': True}
llm-tester  | [PASS] [1.3 sec] Hey team, walk around the building and describe to me what you see
llm-tester  | [PASS] [1.3 sec] Hey jarvis stop pointing
llm-tester  | [FAIL] [1.3 sec] Hey team, hold the junction, if you see any vehicle follow it
llm-tester  |     expected: {'fly_command': {'fly_cmd_type': 'follow', 'location': 'vehicle'}, 'vision_command': {'vision_cmd_type': 'hold', 'vision_cmd_action': 'start', 'objects': 'vehicle'}, 'team_member': 'team', 'need_more_data': False}
llm-tester  |     actual  : {'fly_command': {'fly_cmd_type': 'follow', 'location': 'vehicle'}, 'vision_command': {'vision_cmd_type': 'hold', 'vision_cmd_action': 'start', 'objects': 'junction'}, 'team_member': 'team', 'need_more_data': False}
llm-tester  | [PASS] [1.3 sec] Hey buddy stop following
llm-tester  | [PASS] [1.3 sec] Hey buddy hold
llm-tester  | 
llm-tester  | 15/17 tests passed.


```
