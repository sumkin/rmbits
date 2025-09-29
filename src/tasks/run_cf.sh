export GUROBI_HOME="/home/ay49514/gurobi811/linux64"
export PATH="/home/ay49514/miniconda3/bin:$PATH"
export PATH="/home/ay49514/local:$PATH"
export PATH="/home/ay49514/local/lib:$PATH"
export PATH="/home/ay49514/local/include:$PATH"
export PATH="${PATH}:${GUROBI_HOME}/bin"
export PATH="/home/ay49514/rmbits/src:$PATH"

export PYTHONPATH="/home/ay49514/rmbits/src:$PYTHONPATH"
export PYTHONPATH="/home/ay49514/rmbits/src/datamanager:$PYTHONPATH"
export PYTHONPATH="/home/ay49514/rmbits/src/utils:$PYTHONPATH"
export PYTHONPATH="/home/ay49514/rmbits/src/forecaster:$PYTHONPATH"
export PYTHONPATH="/home/ay49514/rmbits/src/optimizer:$PYTHONPATH"

export LD_LIBRARY_PATH="${LD_LIBRARY_PATH}:${GUROBI_HOME}/lib"

python3 /home/ay49514/rmbits/src/tasks/weekly/s3cf2csv.py



