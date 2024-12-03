#!/bin/bash
#SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH -N 1

#SBATCH --job-name=hmd_example
#SBATCH --output=nlg/nlg_output.out
#SBATCH --error=nlg/nlg_error.err

#SBATCH --partition edu5
#SBATCH -t 0:5:0
#SBATCH --account=hmd-2024

/data/hmd_2024/run "$@"
