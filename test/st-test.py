import os
import subprocess

"""
Test cases for the ac-tool, that uses fpp-to-json to be able to parse fpp files. This allows
for the generation of other fpp files that define subtopology instances.

ex1:
    Tests a simple case where a single subtopology is instantiated
    
ex2:
    Tests a case where a subtopology is instantiated multiple times
    
ex3:
    Test a case with a mix of local and global component instances
"""


def run_test_ex(num):
    exName = f"ex{num}"
    try:
        os.chdir(exName)
    except FileNotFoundError:
        print(f"[text/{exName}] Directory not found")
        return

    # Run the ac-tool
    try:
        cmdArgs = [
            "python3",
            "../../src/ac_tool/tool.py",
            "--locs",
            "locs.fpp",
            "--f",
            "main.fpp",
            "--p",
            "out.out.fpp",
            "--t",
        ]
        subprocess.call(cmdArgs)
    except KeyError as e:
        print(f"[ERR] {e}")
        return

    with open("st-locs.fpp", "r") as f:
        with open("out.out.fpp", "a") as out:
            out.write(f.read())

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
    os.chdir("..")

    assert tf


def test_ex1():
    run_test_ex(1)


def test_ex2():
    run_test_ex(2)


def test_ex3():
    run_test_ex(3)
