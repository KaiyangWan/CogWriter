## Quick Start

### Model Setup

#### Closed Source Models
For closed source models, you need to add your API key to the `llms.py` file.

#### Open Source Models
For open source models, you can directly use the VLLM server:
```bash
vllm serve meta-llama/Llama-3.3-70B-Instruct --tensor-parallel-size 4
```

### Running Experiments

#### CogWriter
```bash
python -u main.py \
    --model "Llama33-70b" \
    --dataset_dir "datasets/short1.json" \
    --output_dir "longGenBench_output/Llama33-70b/output_short1.json" \
    > runningLogs/Llama33-70b/output_short1.log 2>&1 &
```

#### Baseline
```bash
python -u main.py \
    --model "Llama33-70b" \
    --dataset_dir "datasets/short.json" \
    --output_dir "longGenBench_output/Llama33-70b/output_short_baseline.json" \
    > runningLogs/Llama33-70b/output_short_baseline.log --generator baseline 2>&1 &
```

### Evaluation

Results can be found in the `longGenBench_output` folder. To evaluate the results, use the `eval_longGen.py` script:

```bash
python -u eval_longGen.py \
    --data "Llama33-70b/output_short_baseline.json" \
    --csv "Llama33-70b/output_short_baseline.csv" \
    --gpu 4
```