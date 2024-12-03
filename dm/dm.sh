sbatch dm/dm_job.sbatch --system-prompt "$(cat dm/prompt.txt)" llama3 "$(cat nlu/nlu_output.out)" --max_seq_length 2000
