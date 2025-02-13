from CogWriter_model.Agents.PlanningAgent import PlanningAgent
from CogWriter_model.Agents.GenerationAgent import GenerationAgent
from CogWriter_model.BaselineGen import BaselineGen


class CogWriter(BaselineGen):

    @staticmethod
    async def async_generate(model, example, semaphore):
        # First create the hierarchy/plan
        example = await PlanningAgent.async_create_hierarchy(model, example, semaphore)
        # Then generate the content
        example = await GenerationAgent.async_generate(model, example, semaphore)
        return example

