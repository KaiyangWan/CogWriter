import json
import logging
import re
from llms.llms import async_call_llm
from json_repair import repair_json
import asyncio

class PlanningAgent:
    @staticmethod
    async def async_create_hierarchy(model, example, semaphore):
        if example["type"] == "Week":
            example = await PlanningAgent.async_create_week_plan(model, example, semaphore)
        elif example["type"] == "Floor":
            example = await PlanningAgent.async_create_floor_plan(model, example, semaphore)
        elif example["type"] == "Menu Week":
            example = await PlanningAgent.async_create_menu_plan(model, example, semaphore)
        elif example["type"] == "Block":
            example = await PlanningAgent.async_create_block_plan(model, example, semaphore)

        return example

    @staticmethod
    async def async_create_week_plan(model, example, semaphore):
        plan_prompt = f"""
You are an expert writer, and your task is to create a weekly plan containing 52 weeks.
User requirements:
{example['prompt']}

Think step by step. Analyse the user requirements to identify special events and their exact week and list them in "special_events". If the event is periodic, list them seperately by number and specify which weeks they will be in (e.g. 1st [event_name]). Then follow your analysis to create a weekly plan for each week.
Here is an example of the output format:
{{
    "analysis": "",
    "special_events": [ 
        {{
            "event_name": "Husband's Birthday",
            "week_numb": "May 13th, Week 19"
        }}
        ...
    ],
    "weekly_plan": [
        {{
            "week_id": "Week 1 (January 1st - January 7th)",
            "events": "New Year celebrations and family gathering"
        }},
        ...
    ]
}}
Return your analysis and plan in ONLY this exact json format:
{{
    "analysis": "",
    "special_events": [ 
        {{
            "event_name": "event_name",
            "week_numb": "date and week number",
        }}
    ],
    # Strictly follow the special_events for specific weeks
    "weekly_plan": [
        {{
            "week_id": "Week 1 (January 1st - January 7th)",
            "events": "Brifly list special events of this week"
        }},
        ...
    ]
}}"""
        
        print(plan_prompt)
        trial = 0
        while True:
            logging.info(f"Creating initial plan")

            try:
                async with semaphore:
                    response = await async_call_llm(model, plan_prompt)

                # repair the json string
                response = repair_json(response)    
                print(response)
            except Exception as e:
                logging.error(f"Error processing example: {e}")
                trial += 1
                if trial >= 3:
                    logging.error(f"Failed to process example after 3 attempts. Skipping.")
                    break
                await asyncio.sleep(1 * trial)  # Exponential backoff
                logging.error(f"Trying again.")

            match = re.search(r"\{.*\}", response, re.DOTALL)
            if match:
                try:
                    response = dict(json.loads(match.group(0)))
                except json.JSONDecodeError:
                    trial += 1
                    logging.error(f"Failed to parse response. Trying again.")
                    continue

                example["weekly_plan"] = response["weekly_plan"]
                break
            else:
                trial += 1
                logging.error(f"Failed to parse response. Trying again.")

        # Revise the plan
        revise_prompt = f"""
You are an expert writer, and your task is to revise a weekly plan containing 52 weeks.
Current weekly plan:
{example['weekly_plan']}

User requirements:
{example['prompt']}

Think step by step. The current week plan may contain some wrong infomation. 
Refer to the user requirements to identify special events and their exact date and list them in "special_events". If the event is periodic, list them seperately and specify which weeks they will be in (e.g. 1st [event_name]). 
Then follow your analysis to revise the weekly plan for each week.
Return your analysis and revised plan in ONLY this exact json format:
{{
    "analysis": "",
    "revised_weekly_plan": [
        {{
            "week_id": "Week 1 (January 1st - January 7th)",
            "events": "Brifly list special events of this week"
        }},
        ...
    ]
}}"""

        print(revise_prompt)

        trial = 0
        while True:
            logging.info(f"Revising plan")

            try:
                async with semaphore:
                    response = await async_call_llm(model, revise_prompt)

                # repair the json string
                response = repair_json(response)
                print(response)
            except Exception as e:
                logging.error(f"Error processing example: {e}")
                trial += 1
                if trial >= 3:
                    logging.error(f"Failed to process example after 3 attempts. Skipping.")
                    break
                await asyncio.sleep(1 * trial)  # Exponential backoff
                logging.error(f"Trying again.")

            match = re.search(r"\{.*\}", response, re.DOTALL)
            if match:
                try:
                    response = dict(json.loads(match.group(0)))
                except json.JSONDecodeError:
                    trial += 1
                    logging.error(f"Failed to parse response. Trying again.")
                    continue

                example["weekly_plan"] = response["revised_weekly_plan"]
                break
            else:
                trial += 1
                logging.error(f"Failed to parse response. Trying again.")

        return example

    @staticmethod
    async def async_create_floor_plan(model, example, semaphore):
        plan_prompt = f"""
You are an expert architect, and your task is to write a plan for constructing a skyscraper with 100 floors.
User requirements:
{example['prompt']}

Think step by step. Analyse the user requirements to identify special requirements and their exact floor number and list them in "special_floors" list. If the facility is periodic, list them seperately by number and specify which floors they will be in. Then follow your analysis to create the floor-by-floor plan.
Here is an example of the output format:
{{
    "analysis": "",
    "special_floors": [
        {{
            "special_purpose": "Graphic design studio"
            "floor_number": "Floor 51",
        }}
        ...
    ],
    "floor_plan": [
        {{
            "floor_id": "Floor 1",
            "purpose": "The primary lobby and reception area of the skyscraper"
        }}
        ...
    ]
}}

Return your analysis and plan in ONLY the following exact JSON format:
{{
    "analysis": "",
    "special_floors": [
        {{
            "special_purpose": "special purpose"
            "floor_number": "Floor number",
        }},
        ...
    ],
    # Strictly follow the special_floors for specific floors
    "floor_plan": [
        {{
            "floor_id": "Floor 1",
            "purpose": "Briefly describe the purpose of this floor"
        }},
        ...
    ]
}}"""

        print(plan_prompt)
        trial = 0
        while True:
            logging.info("Creating initial floor plan")
            try:
                async with semaphore:
                    response = await async_call_llm(model, plan_prompt)

                # repair the json string
                response = repair_json(response)
                print(response)
            except Exception as e:
                logging.error(f"Error processing example: {e}")
                trial += 1
                if trial >= 3:
                    logging.error("Failed to process example after 3 attempts. Skipping.")
                    break
                await asyncio.sleep(1 * trial)  # Exponential backoff
                logging.error("Trying again.")
                continue

            match = re.search(r"\{.*\}", response, re.DOTALL)
            if match:
                try:
                    response_dict = json.loads(match.group(0))
                except json.JSONDecodeError:
                    trial += 1
                    logging.error("Failed to parse response as JSON. Trying again.")
                    if trial >= 3:
                        break
                    continue

                if "floor_plan" in response_dict:
                    example["floor_plan"] = response_dict["floor_plan"]
                else:
                    logging.error("JSON does not contain 'floor_plan'. Trying again.")
                    trial += 1
                    if trial >= 3:
                        break
                    continue

                break
            else:
                trial += 1
                logging.error("Failed to find JSON in the response. Trying again.")
                if trial >= 3:
                    break

        revise_prompt = f"""
You are an expert architect. You have a skyscraper floor plan as follows:
{example['floor_plan']}

Now, please revise this floor plan based on the user's requirements again:
{example['prompt']}

Think step by step:
- If any details are incorrect, missing, or inconsistent, correct them.
- Floor assignments should align strictly with the user's specification.

Return your analysis and the final revised plan in ONLY this exact JSON format:
{{
    "analysis": "",
    "revised_floor_plan": [
        {{
            "floor_id": "Floor 1",
            "purpose": "Briefly describe the purpose of this floor"
        }},
        ...
    ]
}}
"""

        print(revise_prompt)
        trial = 0
        while True:
            logging.info("Revising floor plan")
            try:
                async with semaphore:
                    response = await async_call_llm(model, revise_prompt)

                # repair the json string
                response = repair_json(response)
                print(response)
            except Exception as e:
                logging.error(f"Error processing example: {e}")
                trial += 1
                if trial >= 3:
                    logging.error("Failed to process example after 3 attempts. Skipping.")
                    break
                await asyncio.sleep(1 * trial)  # Exponential backoff
                logging.error("Trying again.")
                continue

            match = re.search(r"\{.*\}", response, re.DOTALL)
            if match:
                try:
                    response_dict = json.loads(match.group(0))
                except json.JSONDecodeError:
                    trial += 1
                    logging.error("Failed to parse response as JSON. Trying again.")
                    if trial >= 3:
                        break
                    continue

                if "revised_floor_plan" in response_dict:
                    example["floor_plan"] = response_dict["revised_floor_plan"]
                else:
                    logging.error("JSON does not contain 'revised_floor_plan'. Trying again.")
                    trial += 1
                    if trial >= 3:
                        break
                    continue

                break
            else:
                trial += 1
                logging.error("Failed to find JSON in the response. Trying again.")
                if trial >= 3:
                    break

        return example
    
    @staticmethod
    async def async_create_menu_plan(model, example, semaphore):
        plan_prompt = f"""
You are an expert chef, and your task is to create a weekly menu plan containing 52 weeks.
User requirements:
{example['prompt']}

Think step by step. Analyse the user requirements to identify special dishes and their exact week and list them in "special_dishes". If the dish is periodic, list them seperately by number and specify which weeks they will be in (e.g. 1st [dish_name]). Then follow your analysis to create a weekly menu plan for each week.
Here is an example of the output format:
{{
    "analysis": "",
    "special_dishes": [ 
        {{
            "dish_name": "Winter Solstice Feast featuring Venison Stew",
            "week_numb": "05-13, Week 19"
        }}
        ...
    ],
    "weekly_plan": [
        {{
            "week_id": "Menu Week 1 (January 1st - January 7th)",
            "dishes": "Australia Day BBQ featuring Lamb Chops"
        }},
        ...
    ]
}}
Return your analysis and plan in ONLY this exact json format:
{{
    "analysis": "",
    "special_dishes": [ 
        {{
            "dish_name": "dish_name",
            "week_numb": "date and week number",
        }}
    ],
    # Strictly follow the special_dishes for specific weeks
    "weekly_plan": [
        {{
            "week_id": "Menu Week 1 (January 1st - January 7th)",
            "dishes": "Australia Day BBQ featuring Lamb Chops"
        }},
        ...
    ]
}}"""
        
        print(f"Input Prompt: {plan_prompt}")
        
        trial = 0
        while True:
            logging.info(f"Creating initial plan")

            try:
                async with semaphore:
                    response = await async_call_llm(model, plan_prompt)

                # repair the json string
                response = repair_json(response)    
                print(response)
            except Exception as e:
                logging.error(f"Error processing example: {e}")
                trial += 1
                if trial >= 3:
                    logging.error(f"Failed to process example after 3 attempts. Skipping.")
                    break
                await asyncio.sleep(1 * trial)  # Exponential backoff
                logging.error(f"Trying again.")

            match = re.search(r"\{.*\}", response, re.DOTALL)
            if match:
                try:
                    response = dict(json.loads(match.group(0)))
                except json.JSONDecodeError:
                    trial += 1
                    logging.error(f"Failed to parse response. Trying again.")
                    continue

                example["weekly_plan"] = response["weekly_plan"]
                break
            else:
                trial += 1
                logging.error(f"Failed to parse response. Trying again.")

        # Revise the plan
        revise_prompt = f"""
You are an expert writer, and your task is to revise a weekly plan containing 52 weeks.
Current weekly plan:
{example['weekly_plan']}

User requirements:
{example['prompt']}

Think step by step. The current week plan may contain some wrong infomation. 
Refer to the user requirements to identify special dishes and their exact date and list them in "special_dishes". If the dish is periodic, list them seperately and specify which weeks they will be in (e.g. 1st [dish_name]). 
Then follow your analysis to revise the weekly plan for each week.
Return your analysis and revised plan in ONLY this exact json format:
{{
    "analysis": "",
    "revised_weekly_plan": [
        {{
            "week_id": "Menu Week 1 (January 1st - January 7th)",
            "dishes": "Australia Day BBQ featuring Lamb Chops"
        }},
        ...
    ]
}}"""

        print(f"Input Prompt: {revise_prompt}")

        trial = 0
        while True:
            logging.info(f"Revising plan")

            try:
                async with semaphore:
                    response = await async_call_llm(model, revise_prompt)

                # repair the json string
                response = repair_json(response)
                print(response)
            except Exception as e:
                logging.error(f"Error processing example: {e}")
                trial += 1
                if trial >= 3:
                    logging.error(f"Failed to process example after 3 attempts. Skipping.")
                    break
                await asyncio.sleep(1 * trial)  # Exponential backoff
                logging.error(f"Trying again.")

            match = re.search(r"\{.*\}", response, re.DOTALL)
            if match:
                try:
                    response = dict(json.loads(match.group(0)))
                except json.JSONDecodeError:
                    trial += 1
                    logging.error(f"Failed to parse response. Trying again.")
                    continue

                example["weekly_plan"] = response["revised_weekly_plan"]
                break
            else:
                trial += 1
                logging.error(f"Failed to parse response. Trying again.")

        return example


    @staticmethod
    async def async_create_block_plan(model, example, semaphore):
        plan_prompt = f"""
You are an expert designer, and your task is to write a plan for designing a city with 10x10 block grid, numbered from 1 to 100.
User requirements:
{example['prompt']}

Think step by step. Analyse the user requirements to identify special requirements and their exact block number and list them in "special_blocks" list. If the requirement is periodic, list them seperately by number and specify which blocks they will be in. Then follow your analysis to create the block-by-block plan.
Here is an example of the output format:
{{
    "analysis": "",
    "special_blocks": [
        {{
            "special_use": "library use"
            "block_number": "Block 10 (0, 1)",
        }}
        ...
    ],
    "block_plan": [
        {{
            "block_id": "Block 1 (0, 0)",
            "use": "The primary lobby and reception area of the skyscraper"
        }}
        ...
    ]
}}

Return your analysis and plan in ONLY the following exact JSON format:
{{
    "analysis": "",
    "special_blocks": [
        {{
            "special_use": "special use"
            "block_number": "block number",
        }},
        ...
    ],
    # Strictly follow the special_blocks for specific blocks
    "block_plan": [
        {{
            "block_id": "block_id",
            "use": "use"
        }},
        ...
    ]
}}"""

        print(plan_prompt)
        trial = 0
        while True:
            logging.info("Creating initial block plan")
            try:
                async with semaphore:
                    response = await async_call_llm(model, plan_prompt)

                # repair the json string
                response = repair_json(response)
                print(response)
            except Exception as e:
                logging.error(f"Error processing example: {e}")
                trial += 1
                if trial >= 3:
                    logging.error("Failed to process example after 3 attempts. Skipping.")
                    break
                await asyncio.sleep(1 * trial)  # Exponential backoff
                logging.error("Trying again.")
                continue

            match = re.search(r"\{.*\}", response, re.DOTALL)
            if match:
                try:
                    response_dict = json.loads(match.group(0))
                except json.JSONDecodeError:
                    trial += 1
                    logging.error("Failed to parse response as JSON. Trying again.")
                    if trial >= 3:
                        break
                    continue

                if "block_plan" in response_dict:
                    example["block_plan"] = response_dict["block_plan"]
                else:
                    logging.error("JSON does not contain 'block_plan'. Trying again.")
                    trial += 1
                    if trial >= 3:
                        break
                    continue

                break
            else:
                trial += 1
                logging.error("Failed to find JSON in the response. Trying again.")
                if trial >= 3:
                    break

        revise_prompt = f"""
You are an expert architect. You have a skyscraper block plan as follows:
{example['block_plan']}

Now, please revise this block plan based on the user's requirements again:
{example['prompt']}

Think step by step:
- If any details are incorrect, missing, or inconsistent, correct them.
- block assignments should align strictly with the user's requirements.

Return your analysis and the final revised plan in ONLY this exact JSON format:
{{
    "analysis": "your analysis",
    "revised_block_plan": [
        {{
            "block_id": "block_id",
            "use": "use"
        }},
        ...
    ]
}}
"""

        print(revise_prompt)
        trial = 0
        while True:
            logging.info("Revising block plan")
            try:
                async with semaphore:
                    response = await async_call_llm(model, revise_prompt)

                # repair the json string
                response = repair_json(response)
                print(response)
            except Exception as e:
                logging.error(f"Error processing example: {e}")
                trial += 1
                if trial >= 3:
                    logging.error("Failed to process example after 3 attempts. Skipping.")
                    break
                await asyncio.sleep(1 * trial)  # Exponential backoff
                logging.error("Trying again.")
                continue

            match = re.search(r"\{.*\}", response, re.DOTALL)
            if match:
                try:
                    response_dict = json.loads(match.group(0))
                except json.JSONDecodeError:
                    trial += 1
                    logging.error("Failed to parse response as JSON. Trying again.")
                    if trial >= 3:
                        break
                    continue

                if "revised_block_plan" in response_dict:
                    example["block_plan"] = response_dict["revised_block_plan"]
                else:
                    logging.error("JSON does not contain 'revised_block_plan'. Trying again.")
                    trial += 1
                    if trial >= 3:
                        break
                    continue

                break
            else:
                trial += 1
                logging.error("Failed to find JSON in the response. Trying again.")
                if trial >= 3:
                    break

        return example
    