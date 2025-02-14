# CogWriter

CogWriter is a cognitive writing framework designed to improve LLMs' capabilities in generating high-quality long-form text under strict requirements.

## Overview

CogWriter implements a novel cognitive writing approach that:
- Breaks down complex writing tasks into manageable components
- Employs specialized agents for planning and generation
- Ensures coherence and requirement adherence in long-form content

## Table of Contents

- [Installation](#installation)
- [Architecture](#architecture)
- [Usage](#usage)
  - [Model Setup](#model-setup)
  - [Running Experiments](#running-experiments)
  - [Evaluation](#evaluation)
- [Configuration](#configuration)

## Installation

### Environment Setup
```bash
# Create and activate conda environment
conda create -n cogwriter python=3.12
conda activate cogwriter

# Install dependencies
pip install -r requirements.txt
```


## File Structure

```
.
├── CogWriter_model/            # Core framework implementation
│   ├── Agents/                 # Specialized cognitive agents
│   │   ├── GenerationAgent.py  # Content generation agent
│   │   └── PlanningAgent.py    # Strategic planning agent
│   ├── BaselineGen.py          # Baseline generation implementation
│   └── CogWriter.py            # Main framework orchestrator
├── datasets/                   # Input datasets
├── llms/                       # LLM interface implementations
├── utils/                      # Utility functions
├── longGenBench_output/        # Generation results and evaluations
└── runningLogs/                # Execution logs
```

## Usage

### Model Setup

**Closed Source Models**
```python
# Configure API key in llms/llms.py
API_KEY = "your-api-key-here"
```

**Open Source Models**
```bash
# Start VLLM server
vllm serve meta-llama/Llama-3.3-70B-Instruct --tensor-parallel-size 4
```

### Running Experiments

**CogWriter Framework**
```bash
python main.py \
    --model "Llama33-70b" \
    --dataset_dir "datasets/short.json" \
    --output_dir "longGenBench_output/Llama33-70b/output_short.json"
```

**Baseline Generation**
```bash
python main.py \
    --model "Llama33-70b" \
    --dataset_dir "datasets/short.json" \
    --output_dir "longGenBench_output/Llama33-70b/output_short_baseline.json" \
    --generator baseline
```

### Evaluation

```bash
python eval_longGen.py \
    --data "Llama33-70b/output_short_baseline.json" \
    --csv "Llama33-70b/output_short_baseline.csv" \
    --gpu 4
```

## Configuration

### Core Parameters
| Parameter | Description | Default |
|-----------|-------------|---------|
| `--model` | Language model identifier | Required |
| `--dataset_dir` | Input dataset path | Required |
| `--output_dir` | Results output path | Required |
| `--generator` | Generation method (`cogwriter`/`baseline`) | `cogwriter` |

### Evaluation Parameters
| Parameter | Description |
|-----------|-------------|
| `--gpu` | Number of GPUs for evaluation |
| `--data` | Path to results JSON file |
| `--csv` | Path for evaluation metrics CSV |

