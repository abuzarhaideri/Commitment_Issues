PYTHON ?= python3
ARGS ?=

.PHONY: setup run test demo clean package rehearse
setup:
	$(PYTHON) -c "import sys; assert sys.version_info >= (3,11), 'Python 3.11+ is required'"
	$(PYTHON) -m venv .venv
	.venv/bin/python -c "import harness.main; print('Setup complete (standard library only)')"

run:
	.venv/bin/python -m harness.main --evaluation $(ARGS)

test:
	.venv/bin/python -m unittest discover -s tests -v

demo:
	.venv/bin/python -m harness.main --demo

package:
	.venv/bin/python tools/submission.py

rehearse:
	.venv/bin/python tools/rehearse_submission.py

clean:
	$(PYTHON) -c "import pathlib, shutil; [shutil.rmtree(p) for p in pathlib.Path('.').rglob('__pycache__') if '.venv' not in p.parts]"

.PHONY: benchmark-free
benchmark-free:
	.venv/bin/python benchmarks/run_free.py $(ARGS)

.PHONY: reliability
reliability:
	.venv/bin/python tools/reliability_check.py
