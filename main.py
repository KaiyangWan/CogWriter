import argparse
import logging
from CogWriter_model.CogWriter import CogWriter
from CogWriter_model.BaselineGen import BaselineGen
import json
import asyncio
import os
from tqdm.asyncio import tqdm

async def process_example(model, example, semaphore, checkpoint_dir, generator_type="cogwriter"):
    # Create a unique identifier for this example
    example_id = example.get('id', str(example))
    checkpoint_file = os.path.join(checkpoint_dir, f'checkpoint_{str(hash(example_id))}.json')
    
    # Check if checkpoint exists
    if os.path.exists(checkpoint_file):
        try:
            with open(checkpoint_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Error loading checkpoint for {example_id}: {e}")

    # Retry logic
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Generate text using the specified generator
            if generator_type == "cogwriter":
                processed_example = await CogWriter.async_generate(model, example, semaphore)
            else:
                processed_example = await BaselineGen.async_generate(model, example, semaphore)
            
            # Save checkpoint
            try:
                with open(checkpoint_file, 'w', encoding='utf-8') as f:
                    json.dump(processed_example, f)
            except Exception as e:
                logging.error(f"Error saving checkpoint for {example_id}: {e}")
            
            return processed_example
            
        except Exception as e:
            retry_count += 1
            if retry_count == max_retries:
                logging.error(f"Failed to process example {example_id} after {max_retries} attempts: {e}")
                raise
            logging.warning(f"Attempt {retry_count} failed for example {example_id}: {e}. Retrying...")
            await asyncio.sleep(1 * retry_count)  # Exponential backoff

async def main():
    # Create an argument parser
    parser = argparse.ArgumentParser(description="Example script with command-line arguments.")
    
    # Add arguments
    parser.add_argument("--model", type=str, help="Specify the model name", required=True)
    parser.add_argument("--dataset_dir", type=str, help="Specify the dataset directory", required=True)
    parser.add_argument("--output_dir", type=str, help="Specify the output directory", required=True)
    parser.add_argument("--generator", type=str, choices=["cogwriter", "baseline"], default="cogwriter",
                      help="Specify the generator type: 'cogwriter' for CogWriter or 'baseline' for BaselineGen (default: cogwriter)")
    
    # Parse the command-line arguments
    args = parser.parse_args()
    model = args.model
    dataset_dir = args.dataset_dir
    generator_type = args.generator
    
    # Load the dataset
    dataset = []
    logging.info(f"Loading dataset from {dataset_dir}")
    with open(dataset_dir, 'r', encoding="utf-8") as file:
        dataset = json.load(file)

    print(len(dataset))
    
    # Create checkpoint directory based on model name, generator type and dataset
    model_name = os.path.basename(model)
    dataset_name = os.path.splitext(os.path.basename(dataset_dir))[0]
    checkpoint_dir = os.path.join("longGenBench_output", model_name, f"{generator_type}_checkpoints_{dataset_name}")
    os.makedirs(checkpoint_dir, exist_ok=True)
    
    # Create semaphore to limit concurrent tasks
    semaphore = asyncio.Semaphore(100)
    
    # Process examples concurrently
    tasks = [process_example(model, example, semaphore, checkpoint_dir, generator_type) for example in dataset]
    final_outputs = await tqdm.gather(*tasks, desc=f"Processing {dataset_name}")
    
    # Check for exceptions and raise if any found
    for output in final_outputs:
        if isinstance(output, Exception):
            raise output
    
    # Write the output list to a json file
    logging.info(f"Writing output to {args.output_dir}")
    with open(args.output_dir, 'w') as file:
        json.dump(final_outputs, file)

if __name__ == "__main__":
    # Configure logging show timestamp
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
        ]
    )

    # Entry point of the script
    asyncio.run(main())
