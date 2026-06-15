# VSCode Jupyter Notebooks

The assignments in ICM will require you to know how to use Jupyter notebooks, an easy tool for combining Markdown and executable Python codeblocks. You can read the official documentation [here](https://code.visualstudio.com/docs/datascience/jupyter-notebooks). The following section provides useful tips and troubleshooting common pitfalls when using Jupyter with VSCode. 

## Setup Instructions

- Ensure you have a recent [Python 3 release](https://www.python.org/downloads/)

- Ensure that [Pyquist is installed correctly](https://github.com/gclef-cmu/pyquist#installation)
  - In short : Activate/create your desired virtual environment and use `pip install pyquist`.

For deeper troubleshooting see the official guides: Python virtual environments (https://docs.python.org/3/library/venv.html) and VS Code Jupyter Notebooks (https://code.visualstudio.com/docs/datascience/jupyter-notebooks).
## Common Pitfalls 


### TLDR:
- VS Code shows interpreters as relative paths (e.g., `venv/bin/python3`) or absolute system paths (e.g., `/usr/bin/python3`). A leading `/` means the global/system interpreter.
- Keep the venv folder at the workspace root so VS Code discovers it reliably.
- If you can't find an old venv, it's okay to just make a new one and reinstall pyquist. 



### Package Import Failure

If imports fail in a notebook, use this short checklist to find the cause quickly:

- Confirm the kernel/interpreter: in a notebook cell run:

	```python
	import sys
	print(sys.executable)
	print(sys.path)
	```

	The `sys.executable` must point to your venv's Python and `sys.path` should include the venv site-packages directory.
- Check whether the package is installed into that interpreter:

	```bash
	python -m pip show <package>
	python -m pip list | grep <package>
	```

- Install into the correct venv if missing:

	```bash
	source venv/bin/activate
	pip install <package>
	```

- Restart the kernel after installs (`Restart Kernel and Run All`) and run the top cells first.
- If the package imports in the terminal but not in the notebook, re-select the notebook kernel to match the terminal interpreter (or re-register the ipykernel as shown earlier).
- Check for common issues: file name conflicts (e.g., a script named the same as the package), missing `__init__.py` for local packages, or multiple Python installs causing PATH confusion.


### Virtual Environment Selection

-   Select interpreter: open the Command Palette (`Cmd/Ctrl+Shift+P`) → `Python: Select Interpreter` and choose the `venv` interpreter (macOS/Linux: `venv/bin/python`; Windows: `venv\\Scripts\\python.exe`).
- Workspace vs. user scope: VS Code stores interpreter settings per-workspace in `.vscode/settings.json`. If you switch folders, re-check the active workspace before selecting the interpreter.
- **If the venv is missing from the list**:
	- Ensure the venv folder exists at the workspace root and contains the python binary.
	- You can create a new venv from the interpreter selection dialog (`Cmd/Ctrl+Shift+P --> Python : Create Environment`).
	- Use `Enter interpreter path...` in the selector and pick the exact binary.
	- If using WSL/Dev Containers/Remote, verify you selected the remote interpreter (remote indicator in the status bar).

Notebook kernel vs interpreter:

- Open a notebook and check `Select Kernel` in the top-right — the chosen kernel must point to the same interpreter. A kernel can be a separate named environment.
- If the kernel is missing, install and register it from the venv:

```bash
source venv/bin/activate
pip install ipykernel
python -m ipykernel install --user --name=venv --display-name "venv"
```

Check your interpreter version in the VS Code terminal (ensure it's the same as interpreter):

```bash
which python             # macOS / Linux
python -c "import sys; print(sys.executable)"
python -m pip list       # shows packages for that interpreter
```


## Virtual Environments vs. Jupyter Kernels

A virtual environment is an isolated Python installation with its own packages; a Jupyter kernel is how a notebook picks which Python interpreter to run.

- Virtual environment: creates an isolated `venv` folder where you install packages for the project.
- Jupyter kernel: the selected kernel tells the notebook which Python interpreter (and therefore which venv) will execute code cells.

How to make them match:

- In VS Code, select the project interpreter (`Command Palette → Python: Select Interpreter`) and choose `./venv/bin/python`.
- Then open your notebook and in the top-right `Select Kernel` choose the kernel that points to the same interpreter (the kernel name usually includes the path or the venv name).
- If the venv is not shown as a kernel, install `ipykernel` into the venv and register it:

	```bash
    source venv/bin/activate
	pip install ipykernel
	python -m ipykernel install --user --name=venv --display-name "venv"
	```

Reference: [Jupyter kernels documentation](https://jupyter.org/documentation) and VS Code kernel selection docs (https://code.visualstudio.com/docs/datascience/jupyter-notebooks#_select-and-change-kernels).

## Pyquist Advice

- In notebooks: always confirm the kernel matches the venv where `pyquist` is installed using ```import sys; print(sys.executable)```.
- If you see `ModuleNotFoundError` for `pyquist` in a notebook but it imports in the terminal, the kernel and interpreter are different—re-select the kernel or re-register the ipykernel in that venv.

Further reading and troubleshooting:

- VS Code Jupyter troubleshooting: https://code.visualstudio.com/docs/datascience/jupyter-notebooks#_troubleshooting
- Pip basics: https://pip.pypa.io/en/stable/user_guide/