import sys
import subprocess
import os


def calculateDependencies(input_file, locs_file) -> str:
    """
    This function calculates the dependencies for an fpp file using fprime-util to get
    the location of the build cache fpp-depend.
    
    Args:
        input_file: The input fpp file to calculate dependencies for
        locs_file: The locs.fpp file to use for dependency calculation
        
    Returns:
        A string of dependencies for the input file
    """
    
    # run fprime-util info
    print(f"[fpp] Calculating fpp dependencies for {input_file}...")

    try:
        fprimeUtil = subprocess.run(
            ["fprime-util", "info"], check=True, stdout=subprocess.PIPE
        )
        buildCache = fprimeUtil.stdout.decode("utf-8").split(" ")[-1].strip()

        # check if build cache is valid
        if not buildCache:
            raise subprocess.CalledProcessError(1, "fprime-util info")
        elif not buildCache.startswith("/"):
            raise ValueError("Invalid build cache path")
        elif not os.path.exists(buildCache):
            raise FileNotFoundError("Build cache does not exist")

        print(f"[fpp] Using build cache: {buildCache}")
    except subprocess.CalledProcessError as e:
        print(f"[ERR] fprime-util info failed with error: {e}")
        return 1
    
    # run fpp-depend
    dependencies = None
    try:
        fppDep = subprocess.run(
            ["fpp-depend", locs_file, input_file],
            check=True,
            stdout=subprocess.PIPE,
        )
        if not fppDep.stdout:
            print("[INFO] No dependencies found for input file")
        else:
            dependencies = ",".join(fppDep.stdout.decode("utf-8").split("\n"))[:-1]
    except subprocess.CalledProcessError as e:
        print(f"[ERR] fpp-depend failed with error: {e}")
        return 1

    return dependencies


def fpp_to_json(input_file):
    """
    This function runs fpp-to-json on an fpp file to generate a JSON AST.
    
    Args:
        input_file: The input fpp file to run fpp-to-json on
        
    Returns:
        None
    """
    
    # run fpp
    print(f"[fpp] Running fpp-to-json for {input_file}...")

    try:
        fppToJSON = subprocess.run(
            ["fpp-to-json", input_file, "-s"], check=True, stdout=subprocess.PIPE
        )
    except subprocess.CalledProcessError as e:
        print(f"[ERR] fpp-to-json failed with error: {e}")
        return 1


def fpp_format(input_file):
    """
    This function runs fpp-format on an fpp file to format the file.
    
    Args:
        input_file: The input fpp file to run fpp-format on
        
    Returns:
        None
    """
    
    # run fpp-format
    print(f"[fpp] Running fpp-format for {input_file}...")

    try:
        fppFormat = subprocess.run(
            ["fpp-format", input_file], check=True, stdout=subprocess.PIPE
        )
        return fppFormat.stdout.decode("utf-8")
    except subprocess.CalledProcessError as e:
        print(f"[ERR] fpp-format failed with error: {e}")
        return 1
    
def fpp_locate_defs(input_file, locs_file):
    """
    This function runs fpp-locate-defs on an fpp file to locate definitions.
    
    Args:
        input_file: The input fpp file to run fpp-locate-defs on
        locs_file:  The locs.fpp file used to find the base directory to base def locations
                    off of
    """

    print(f"[fpp] Running fpp-locate-defs for {input_file}...")
    
    locs_file = os.path.abspath(locs_file)
    base_dir = os.path.dirname(locs_file)
    
    try:
        fppLocateDefs = subprocess.run(
            ["fpp-locate-defs", input_file, "-d", base_dir], check=True, stdout=subprocess.PIPE
        )
        return fppLocateDefs.stdout.decode("utf-8")
    except subprocess.CalledProcessError as e:
        print(f"[ERR] fpp-locate-defs failed with error: {e}")
        return 1