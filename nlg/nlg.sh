sbatch nlg/nlg_job.sbatch --system-prompt "$(cat nlg/prompt.txt)" llama3 "$(cat nlu/nlu_output.out)\n\n$(cat dm/dm_output.out)" --max_seq_length 2000
