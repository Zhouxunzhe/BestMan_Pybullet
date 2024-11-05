import os
import pickle
import subprocess

def submodule_call(env_name, script_path, input_data):
    
    input_data = pickle.dumps(input_data)
    script_path = os.path.join('..', script_path)
    result = subprocess.run(
        ['conda', 'run', '--no-capture-output', '-n', env_name, 'python', script_path],
        input=input_data,
        capture_output=True
    )
    if result.returncode != 0:
        print(f"[Submodule call] \033[31merror\033[0m: Error occurred: {result.stderr.decode()}")
    result = pickle.loads(result.stdout)
    return result
    