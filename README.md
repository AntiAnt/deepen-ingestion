# deepen-ingestion
Deepen wrapper used to kick off processing jobs. Handle ingestion and storing of audio files processed locally. Has the option to then run summary processing jobs remotely.

## Setup
Env setup using mamba
```
mamba env create -f environment.yml -y
```
activate env
```
mamba activate deepen-ingestion
```
pip install using uv
```
uv pip install -r requirements.txt
```

## Run
Add a run config **do not commit config** as secrets maybe be included.


run ingestion
```
python run deepen_run.py --config-path <PATH TO CONFIG>
```