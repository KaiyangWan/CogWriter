import json
import logging
import re
import asyncio
from llms.llms import async_call_llm
from utils.wordCounter import count_words
from json_repair import repair_json

class GenerationAgent:

    @staticmethod
    async def async_generate(model, example, semaphore):
        if example['type'] == 'Week':
            example = await GenerationAgent.async_generate_week(model, example, semaphore)
        elif example["type"] == "Floor":
            example = await GenerationAgent.async_generate_floor(model, example, semaphore)
        elif example["type"] == "Menu Week":
            example = await GenerationAgent.async_generate_menu(model, example, semaphore)
        elif example["type"] == "Block":
            example = await GenerationAgent.async_generate_block(model, example, semaphore)
        return example

    @staticmethod
    async def async_generate_week(model, example, semaphore):
        async def process_week(week):
            prompt = f"""You are an expert writer. 
Write a 200-word weekly diary entry for the week of {week['week_id']}.
The events for this week are: {week['events']}
You should consider the coherence of the diary entry referring to the plan of the whole year:
{example['weekly_plan']}
You should consider the user requirements: {example['prompt']}
Check from the user requirements if there are any special events that should be included in the diary entry. If there are, include them in the diary entry. If there are no special events, write a general diary entry for the week.
Return the diary entry in the following json format:
{{
    "week_id": "{week['week_id']}",
    "check": "reason and check if the user requirements are met",
    "diary_entry": "Your 200-word diary entry here" 
}}
"""
            logging.info(f"Generating initial diary entry for week {week['week_id']}")

            while True:
                async with semaphore:
                    response = await async_call_llm(model, prompt)
                
                # repair the json string
                response = repair_json(response)

                print(response)

                match = re.search(r"\{.*\}", response, re.DOTALL)
                if match:
                    response = match.group(0)

                    try:
                        diary_entry = dict(json.loads(response))

                        week['diary_entry'] = diary_entry['diary_entry']
                        week['length_requirement'] = 200
                        logging.info(f"Diary entry word count: {count_words(diary_entry['diary_entry'])}")
                    except json.JSONDecodeError: 
                        logging.error(f"Failed to parse response. Trying again.")
                        continue

                    break
                else:
                    logging.error(f"Failed to parse response. Trying again.")

            # Refine the diary entry
            current_length = count_words(week['diary_entry'])
            required_length = week['length_requirement']

            word_diff = abs(required_length - current_length)

            while word_diff > (required_length * 0.1):
                refinement_prompt = f"""You are an expert editor. The provided text need to be {"shorten" if current_length > required_length else "lengthen"} by {word_diff} words while maintaining the original meaning and coherence.
                Text:
                {week['diary_entry']}
                Return only the refined text."""

                logging.info(f"Refining text for week {week['week_id']}")
                async with semaphore:
                    week['diary_entry'] = await async_call_llm(model, refinement_prompt)
                logging.info(f"Refined text: {week['diary_entry']}")

                current_length = count_words(week['diary_entry'])

                word_diff = abs(required_length - current_length)

            logging.info(f"Final diary entry word count: {count_words(week['diary_entry'])}")
            return week

        # Process all weeks concurrently
        tasks = [process_week(week) for week in example['weekly_plan']]
        example['weekly_plan'] = await asyncio.gather(*tasks)
        
        example['final_text'] = GenerationAgent.get_final_week_text(example['weekly_plan'])
        return example

    @staticmethod
    def get_final_week_text(weekly_plan):
        """
        Get the final text from the generated text with respect to the plan.
        """

        text = ""

        for week in weekly_plan:
            text += '#*# ' + week['week_id'] + ':' + week['diary_entry']

        text += '*** finished ***'
        return text

    @staticmethod
    async def async_generate_floor(model, example, semaphore):
        async def process_floor(floor):
            prompt = f"""You are an expert disigner. 
Write a 150-word skyscraper floor plan for the floor of {floor['floor_id']}.
The purpose for this floor is: {floor['purpose']}
You should consider the coherence of the floor plan by referring to the plan of the whole skyscraper:
{example['floor_plan']}

You should consider the user requirements: {example['prompt']}
Check from the user requirements if there are any special requirement that should be included in the floor plan. If there are, include them in the floor plan. If there are no special events, write a general floor plan.
Return the floor plan for the floor of {floor['floor_id']} in the following json format:
{{
    "floor_id": "{floor['floor_id']}",
    "check": "reason and check if the user requirements are met",
    "plan": "Your 150-word floor plan here" 
}}
"""
            logging.info(f"Generating initial floor plan for floor {floor['floor_id']}")

            while True:
                async with semaphore:
                    response = await async_call_llm(model, prompt)

                # repair the json string
                response = repair_json(response)

                print(response)

                match = re.search(r"\{.*\}", response, re.DOTALL)
                if match:
                    response = match.group(0)

                    try:
                        floor_plan = dict(json.loads(response))

                        floor['plan'] = floor_plan['plan']
                        floor['length_requirement'] = 150
                        logging.info(f"floor plan word count: {count_words(floor['plan'])}")
                    except json.JSONDecodeError: 
                        logging.error(f"Failed to parse response. Trying again.")
                        continue

                    break
                else:
                    logging.error(f"Failed to parse response. Trying again.")

            # Refine the floor plan
            current_length = count_words(floor['plan'])
            required_length = floor['length_requirement']

            word_diff = abs(required_length - current_length)

            while word_diff > (required_length * 0.1):
                refinement_prompt = f"""You are an expert editor. The provided text need to be {"shorten" if current_length > required_length else "lengthen"} by {word_diff} words while maintaining the original meaning and coherence.
                Text:
                {floor['plan']}
                Return only the refined text."""

                logging.info(f"Refining text for floor {floor['floor_id']}")
                async with semaphore:
                    floor['plan'] = await async_call_llm(model, refinement_prompt)
                logging.info(f"Refined text: {floor['plan']}")

                current_length = count_words(floor['plan'])
                word_diff = abs(required_length - current_length)

            logging.info(f"Final floor plan word count: {count_words(floor['plan'])}")
            return floor

        # Process all floors concurrently
        tasks = [process_floor(floor) for floor in example['floor_plan']]
        example['floor_plan'] = await asyncio.gather(*tasks)

        example['final_text'] = GenerationAgent.get_final_floor_text(example['floor_plan'])

        return example

    @staticmethod
    def get_final_floor_text(floor_plan):

        """
        Get the final text from the generated text with respect to the plan.
        """

        text = ""

        for floor in floor_plan:
            text += '#*# ' + floor['floor_id'] + ':' + floor['plan']

        text += '*** finished'
        return text
    
    @staticmethod
    async def async_generate_menu(model, example, semaphore):
        async def process_menu(week):
            prompt = f"""You are an expert chef. 
Write a 200-word weekly menu plan for the week of {week['week_id']}.
The dishes for this week are: {week['dishes']}
You should consider the coherence of the menu plan referring to the plan of the whole year:
{example['weekly_plan']}
You should consider the user requirements: {example['prompt']}
Check from the user requirements if there are any special dishes that should be included in the menu plan. If there are, include them in the menu plan. If there are no special dishes, write a general menu plan for the week.
Return the menu plan in the following json format:
{{
    "week_id": "{week['week_id']}",
    "check": "reason and check if the user requirements are met",
    "week_menu": "Your 200-word menu plan here"
}}
"""
            logging.info(f"Generating initial menu plan for week {week['week_id']}")

            print(f"Input Prompt: {prompt}")

            while True:
                async with semaphore:
                    response = await async_call_llm(model, prompt)
                
                # repair the json string
                response = repair_json(response)

                print(response)

                match = re.search(r"\{.*\}", response, re.DOTALL)
                if match:
                    response = match.group(0)

                    try:
                        week_menu = dict(json.loads(response))

                        week['week_menu'] = week_menu['week_menu']
                        week['length_requirement'] = 200
                        logging.info(f"Diary entry word count: {count_words(week['week_menu'])}")
                    except json.JSONDecodeError: 
                        logging.error(f"Failed to parse response. Trying again.")
                        continue

                    break
                else:
                    logging.error(f"Failed to parse response. Trying again.")

            # Refine the menu plan
            current_length = count_words(week['week_menu'])
            required_length = week['length_requirement']

            word_diff = abs(required_length - current_length)

            while word_diff > (required_length * 0.1):
                refinement_prompt = f"""You are an expert editor. The provided text need to be {"shorten" if current_length > required_length else "lengthen"} by {word_diff} words while maintaining the original meaning and coherence.
                Text:
                {week['week_menu']}
                Return only the refined text."""

                logging.info(f"Refining text for week {week['week_id']}")
                async with semaphore:
                    week['week_menu'] = await async_call_llm(model, refinement_prompt)
                logging.info(f"Refined text: {week['week_menu']}")

                current_length = count_words(week['week_menu'])

                word_diff = abs(required_length - current_length)

            logging.info(f"Final menu plan word count: {count_words(week['week_menu'])}")
            return week

        # Process all weeks concurrently
        tasks = [process_menu(week) for week in example['weekly_plan']]
        example['weekly_plan'] = await asyncio.gather(*tasks)
        
        example['final_text'] = GenerationAgent.get_final_menu_text(example['weekly_plan'])
        return example

    @staticmethod
    def get_final_menu_text(weekly_plan):
        """
        Get the final text from the generated text with respect to the plan.
        """

        text = ""

        for week in weekly_plan:
            text += '#*# ' + week['week_id'] + ':' + week['week_menu']

        text += '*** finished ***'
        return text


    @staticmethod
    async def async_generate_block(model, example, semaphore):
        async def process_block(block):
            prompt = f"""You are an expert disigner. 
Write a 150-word city block plan for the block of {block['block_id']}.
The use for this block is: {block['use']}
You should consider the coherence of the block plan by referring to the plan of the whole city:
{example['block_plan']}

You should consider the user requirements: {example['prompt']}
Check from the user requirements if there are any special requirement that should be included in the block plan. If there are, include them in the block plan. If there are no special events, write a general block plan.
Return the block plan for the block of {block['block_id']} in the following json format:
{{
    "block_id": "{block['block_id']}",
    "check": "reason and check if the user requirements are met",
    "plan": "Your 150-word block plan here" 
}}
"""
            logging.info(f"Generating initial block plan for block {block['block_id']}")

            while True:
                async with semaphore:
                    response = await async_call_llm(model, prompt)

                # repair the json string
                response = repair_json(response)

                print(response)

                match = re.search(r"\{.*\}", response, re.DOTALL)
                if match:
                    response = match.group(0)

                    try:
                        block_plan = dict(json.loads(response))

                        block['plan'] = block_plan['plan']
                        block['length_requirement'] = 150
                        logging.info(f"block plan word count: {count_words(block['plan'])}")
                    except json.JSONDecodeError: 
                        logging.error(f"Failed to parse response. Trying again.")
                        continue

                    break
                else:
                    logging.error(f"Failed to parse response. Trying again.")

            # Refine the block plan
            current_length = count_words(block['plan'])
            required_length = block['length_requirement']

            word_diff = abs(required_length - current_length)

            while word_diff > (required_length * 0.1):
                refinement_prompt = f"""You are an expert editor. The provided text need to be {"shorten" if current_length > required_length else "lengthen"} by {word_diff} words while maintaining the original meaning and coherence.
                Text:
                {block['plan']}
                Return only the refined text."""

                logging.info(f"Refining text for block {block['block_id']}")
                async with semaphore:
                    block['plan'] = await async_call_llm(model, refinement_prompt)
                logging.info(f"Refined text: {block['plan']}")

                current_length = count_words(block['plan'])
                word_diff = abs(required_length - current_length)

            logging.info(f"Final block plan word count: {count_words(block['plan'])}")
            return block

        # Process all blocks concurrently
        tasks = [process_block(block) for block in example['block_plan']]
        example['block_plan'] = await asyncio.gather(*tasks)

        example['final_text'] = GenerationAgent.get_final_block_text(example['block_plan'])

        return example

    @staticmethod
    def get_final_block_text(block_plan):

        """
        Get the final text from the generated text with respect to the plan.
        """

        text = ""

        for block in block_plan:
            text += '#*# ' + block['block_id'] + ':' + block['plan']

        text += '*** finished'
        return text