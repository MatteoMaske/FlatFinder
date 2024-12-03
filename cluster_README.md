# Cluster Usage

> First and foremost: you may have to connect to the University VPN to access the cluster if you are working from home.

In the following README you'll understand how
1. upload/download files on the cluster
2. run script and interactive sessions
3. manage the queue, e.g. check your jobs and delete older ones

- [Cluster Usage](#cluster-usage)
  - [File Management](#file-management)
    - [Uploading files](#uploading-files)
    - [Downloading Files](#downloading-files)
  - [Running a Job](#running-a-job)
    - [Running a job from a script](#running-a-job-from-a-script)
    - [Running an interactive sessions](#running-an-interactive-sessions)
  - [Manage your Jobs](#manage-your-jobs)
    - [Check a job id/status](#check-a-job-idstatus)
    - [Delete a job](#delete-a-job)


## File Management

### Uploading files

You can upload a file on the cluster by using the following command:

```bash
scp path/to/your/file first_name.last_name@marzola.disi.unitn.it:"/home/first_name.last_name"
```

where 
- `path/to/your/file` is the path of the file you want to upload
- `first_name.last_name` is what you use during log in.

You can also upload a folder by adding the `-r` argument after the `scp` command.


### Downloading Files

Similarly, you can download a file from the cluster by swapping source and destination, as follows:

```bash
scp first_name.last_name@marzola.disi.unitn.it:"/home/first_name.last_name/path/to/your/file" .
```

where `.` simply specifies that the file will be downloaded in the current folder (the one where you execute the command).


## Running a Job

### Running a job from a script

You can run a job on the cluster from a script by creating a .sbatch file and using the `sbatch` command.

You can use the custom_example.sbatch as reference and use it to execute any python script you want (line 22).

However, remember to call your python script using as it follows:

```bash
PYTHONPATH=$HMD_ROOT/code $PYTHON your_script.py
```

This ensures that you are using the correct python version for our scripts to work.

You can also add `"$@"` to pass additional arguments from the command line.


### Running an interactive sessions

Running from a script is conveninent because you don't know when resources will be allocated. However, if you want to interact with the model (e.g., have a real-time exchange, or test the model with different users) you can create an interactive session, using the following command:

```bash
srun -p edu5 -N 1 -n 1 -c 1 --gres=gpu:1 --account hmd-2024 --pty /bin/bash
```

When the resources will be allocated, you will have your interactive session ready.

At this point, you will have to execute a **mandatory** set of commands to be able to access to the models, as follows:

```bash
HMD_ROOT="/data/hmd_2024/"
VENV_PATH="$HMD_ROOT/venv"
PYTHON="$VENV_PATH/bin/python"
export HF_HOME=$HMD_ROOT
```

Then, you are free to execute your script. For example, you can try our naive pipeline with llama3 by running the following command:

```bash
PYTHONPATH=$HMD_ROOT/code $PYTHON pipeline.py llama3
```


## Manage your Jobs

### Check a job id/status
You can check the id or the status of your jobs by using:

```bash
squeue --me
```

### Delete a job
If you don't need a job anymore, you can delete it by using the following command:

```bash
scancel JOB_ID
```

where `JOB_ID` is the id of the job you want to cancel and can be retrieved using `squeue`.