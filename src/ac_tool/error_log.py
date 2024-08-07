import os
import datetime

def create_log_file(dir):
    fileName = "subtopology-logs-" + datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S") + ".txt"
    
    try:
        # create filename
        os.makedirs(dir, exist_ok=True)
        with open(os.path.join(dir, fileName), "w") as f:
            f.write("== Subtopology Autocoder logs ==\n\n")
    except FileExistsError:
        # directory already exists
        pass
    except Exception as e:
        print(f"Error creating log file: {e}")
        return None
    
    pathToFile = os.path.join(dir, fileName)
    return pathToFile

def logOK(logFile, message):
    with open(logFile, "a") as f:
        f.write(f"[✓] {message}\n")
        
def logERR(logFile, message):
    with open(logFile, "a") as f:
        f.write(f"[x] {message}\n")

