import os
import subprocess
from pathlib import Path
import shutil

"""
Test cases for the ac-tool, that uses fpp-to-json to be able to parse fpp files. This allows
for the generation of other fpp files that define subtopology instances.

ex1:
    Tests a simple case where a single subtopology is instantiated
    Assert TRUE
    
ex2:
    Tests a case where a subtopology is instantiated multiple times
    Assert TRUE
    
ex3:
    Test a case with a mix of local and global component instances
    Assert TRUE
    
ex4:
    Test a case where a local component is tried to be replaced. 
    Assert FALSE
    
ex5:
    Test a syntax error
    Assert FALSE
    
ex6:
    Test a case where the locs file is invalid
    Assert FALSE
"""

def get_to_test_dir():
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)

def run_test_ex(num):
    # get to the test directory
    
    get_to_test_dir()
        
    exName = f"./ex{num}"
    try:
        os.chdir(exName)
    except FileNotFoundError as e:
        print(f"[text/{exName}] Directory not found")
        return
    
    pathToTool = Path("../../src/ac_tool/tool.py").absolute()
    print(pathToTool)

    # Run the ac-tool
    command = None
    try:
        cmdArgs = [
            "python3",
            pathToTool,
            "--locs",
            "locs.fpp",
            "--f",
            "main.fpp",
            "--p",
            "out.out.fpp",
            "--t",
        ]
        command = subprocess.run(cmdArgs, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
                
        if not os.path.exists("out.out.fpp") or not os.path.exists("st-locs.fpp"):
            if os.path.exists("tmp"):
                shutil.rmtree("tmp", ignore_errors=True)
                
            with open("out.out.txt", "w") as f:
                f.write(command.stdout.decode("utf-8"))
        
            with open("out.ref.txt", "r") as f:
                ref = f.read()
                
            if ref == command.stdout.decode("utf-8"):
                os.remove("out.out.txt")
                os.chdir("..")
                return True
            else:
                os.chdir("..")
                return False
        
        with open("st.fpp", "r") as st:
            with open("st-locs.fpp", "r") as f:
                with open("main.out.fpp", "r") as main:
                    with open("out.out.fpp", "w") as out:
                        out.write(st.read())
                        out.write(f.read())
                        out.write(main.read())

        # compare out.out.fpp and out.ref.fpp
        with open("out.out.fpp", "r") as f:
            out = f.read()
        with open("out.ref.fpp", "r") as f:
            ref = f.read()

        tf = False
        if out == ref:
            tf = True
            os.remove("out.out.fpp")
        else:
            tf = False

        os.remove("st-locs.fpp")
        os.remove("main.out.fpp")
        os.chdir("..")

        return tf
    except KeyError as e:
        print(f"[ERR] {e}")
    except subprocess.CalledProcessError as e:
        print(f"[ERR] {e}")


def test_ex1_simple():
    assert run_test_ex(1)

def test_ex2_multiple():
    assert run_test_ex(2)

def test_ex3_mix_local_global():
    assert run_test_ex(3)

def test_ex4_local_replace():
    assert run_test_ex(4)
    
def test_ex5_syntax_err():
    assert run_test_ex(5)
    
def test_ex6_locs_invalid():
    assert run_test_ex(6)