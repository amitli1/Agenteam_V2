# MissionPlannerAgent:
1. get_way_points:
    1.1 used only LLM to convert text to entity_number, entity_type
    1.2 with that output (columns names) we can search in the DF
    1.3 there is function to do the same without LLM (_parse_with_rules)
        1.3.1 For now - ut used if LLM failed to parse.
