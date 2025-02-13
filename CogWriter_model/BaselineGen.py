from llms.llms import async_call_llm
import json
import time
import logging
import asyncio
from json_repair import repair_json
import re

class BaselineGen:

    @staticmethod
    async def async_generate(model, example, semaphore):
        # Initialize OpenAI client

        # Retry logic
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                time_start = time.time()
                
                async with semaphore:


                    response = await async_call_llm(model, example["prompt"])
                    time_end = time.time()
                    
                    logging.info(f"Time taken: {time_end - time_start} seconds")
                    
                    logging.info(f"Response: {response}")

                    # Update example with response data
                    response = str(response)
                    example["response"] = response
                    example["output_blocks"] = response.split('#*#')
                    example["word_count"] = len(response.split())
                    example["time_taken"] = time_end - time_start
                    example["final_text"] = response

                return example
                
            except Exception as e:
                retry_count += 1
                if retry_count == max_retries:
                    logging.error(f"Failed to process example after {max_retries} attempts: {e}")
                    raise
                logging.warning(f"Attempt {retry_count} failed: {e}. Retrying...")
                await asyncio.sleep(1 * retry_count)  # Exponential backoff

### chain of thought
#                     chain_of_thought_prompt = f"""{example["prompt"]}
# Let's think step by step."""

#                     response = await async_call_llm(model, chain_of_thought_prompt)


### self-refine
# async with semaphore:
#                     initial_response = await async_call_llm(model, example["prompt"])

#                     print(f"Inital response: {initial_response}")

#                     self_refine_prompt = f"""You are an AI model that provides feedback to improve the following text to better met the user requirements.
# The generated text is as follows:
# {initial_response}

# The user requirements are as follows:
# {example["prompt"]}

# Please provide feedback on the generated text."""

#                     feedback_response = await async_call_llm(model, self_refine_prompt)

#                     print(f"Feedback response: {feedback_response}")

#                     output_prompt = f"""Inprove the following text for the user requirements based on the feedback provided.
# The user requirements are as follows:
# {example["prompt"]}

# The generated text is as follows:
# {initial_response}

# The improvement feedback is as follows:
# {feedback_response}

# Please generate new text based on the user requirements and the feedback provided.
#                     """

#                     response = await async_call_llm(model, output_prompt)

#                     print(f"Output response: {response}")