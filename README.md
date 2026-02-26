# gcp-iam-evidence-collector

`gcp-iam-evidence-collector` is a Python CLI that retrieves a Google Cloud project's IAM bindings and writes per-principal JSON evidence files. 

It takes the GCP projectId and an output directory as input.

It organizes its output under `<outpud-dir>/by_principal/user`, `by_principal/group`, and `by_principal/serviceAccount`, with each JSON document containing the principal name, target project ID, and that principal's granted roles.

 ## Setup


## Setup

```bash

python -m pip install -e '.[dev]'

```

## Run

```

python src/main.py --project-id <PROJECT_ID> --output-dir <OUTPUT_DIR>

```

## Test

```bash
python -m pytest -q
```
