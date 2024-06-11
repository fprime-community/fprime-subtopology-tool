import sys
import subprocess
import os


def calculateDependencies(input_file):
    # run fprime-util info
    print(f"[fpp] Calculating fpp dependencies for {input_file}...")

    try:
        fprimeUtil = subprocess.run(
            ["fprime-util", "info"], check=True, stdout=subprocess.PIPE
        )
        buildCache = fprimeUtil.stdout.decode("utf-8").split(" ")[-1].strip()

        # check if build cache is valid
        if not buildCache:
            print("[ERR] fprime-util info did not return a valid build cache")
            sys.exit(1)
        elif not buildCache.startswith("/"):
            print(
                "[ERR] fprime-util info did not return an absolute path for build cache"
            )
            sys.exit(1)
        elif not os.path.exists(buildCache):
            print("[ERR] fprime-util info returned a non-existent build cache")
            sys.exit(1)

        print(f"[fpp] Using build cache: {buildCache}")
    except subprocess.CalledProcessError as e:
        print(f"[ERR] fprime-util info failed with error: {e}")
        sys.exit(1)

    # run fpp-depend
    dependencies = None
    try:
        fppDep = subprocess.run(
            ["fpp-depend", buildCache + "/locs.fpp", input_file],
            check=True,
            stdout=subprocess.PIPE,
        )
        if not fppDep.stdout:
            print("[INFO] No dependencies found for input file")
        else:
            dependencies = ",".join(fppDep.stdout.decode("utf-8").split("\n"))[:-1]
    except subprocess.CalledProcessError as e:
        print(f"[ERR] fpp-depend failed with error: {e}")
        sys.exit(1)

    print(dependencies)
    return dependencies


def fpp_to_json(input_file):
    # run fpp
    print(f"[fpp] Running fpp-to-json for {input_file}...")

    try:
        fppToJSON = subprocess.run(
            ["fpp-to-json", input_file, "-s"], check=True, stdout=subprocess.PIPE
        )
        print(f"[fpp] fpp-to-json succeeded")
    except subprocess.CalledProcessError as e:
        print(f"[ERR] fpp-to-json failed with error: {e}")
        sys.exit(1)


def fpp_format(input_file):
    # run fpp-format
    print(f"[fpp] Running fpp-format for {input_file}...")

    try:
        fppFormat = subprocess.run(
            ["fpp-format", input_file], check=True, stdout=subprocess.PIPE
        )
        return fppFormat.stdout.decode("utf-8")
    except subprocess.CalledProcessError as e:
        print(f"[ERR] fpp-format failed with error: {e}")
        sys.exit(1)
