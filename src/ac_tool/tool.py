import os
import fpp_interface as fpp
import fpp_json_ast_parser as Parser
import fpp_writer as FppWriter
import json
import utils as Utils
import shutil
import argparse
import sys
from pathlib import Path

TOPOLOGIES_TO_INSTANTIATE = []
WRITTEN_FILE_PIECES = []


def walkModule(data, oldQf):
    module = Parser.ModuleParser(data)
    module.parse()

    if oldQf == "":
        qf = module.module_name
    else:
        qf = oldQf + "." + module.module_name  # qualifier

    module.qf = qf

    for member in module.members():
        if "DefComponentInstance" in member[1]:
            instance = Parser.InstanceParser(member)
            instance.parse()
            instance.qf = qf + "." + instance.instance_name

        if "DefTopology" in member[1]:
            walkTopology(member, qf)

        if "DefModule" in member[1]:
            walkModule(member, qf)

        if "DefConstant" in member[1]:
            constant = Parser.ConstantParser(member)
            constant.parse()

            isTopologyInstance = Utils.constant_to_subtopology_instance(constant)

            if isTopologyInstance:
                isTopologyInstance["qf"] = qf + "." + constant.constant_Id
                TOPOLOGIES_TO_INSTANTIATE.append(isTopologyInstance)

    return qf


def walkTopology(data, module):
    topology = Parser.TopologyParser(data)
    topology.parse()

    if module == "":
        qf = topology.topology_name
    else:
        qf = module + "." + topology.topology_name  # qualifier

    topology.qf = qf

    for member in topology.members():
        if "DefTopology" in member[1]:
            walkTopology(member, qf)

        if "DefModule" in member[1]:
            walkModule(member, qf)

    return qf


def openFppFile(path):
    if not os.path.isabs(path):
        path = Path(path).resolve()

    pathDir = os.path.dirname(path)

    if not os.path.exists(pathDir + "/tmp"):
        try:
            os.mkdir(pathDir + "/tmp")
        except OSError as e:
            print("Creation of the directory %s failed" % (pathDir + "/tmp"))
            sys.exit(1)

    os.chdir(pathDir + "/tmp")

    fpp.fpp_to_json(path)

    # parse json
    with open("fpp-ast.json", "r") as f:
        AST = json.load(f)

    os.chdir(pathDir)
    shutil.rmtree("./tmp", ignore_errors=True)

    return AST


def visitFppFile(path):
    AST = openFppFile(path)

    for i in range(len(AST[0]["members"])):
        if "DefModule" in AST[0]["members"][i][1]:
            walkModule(AST[0]["members"][i], "")

        if "DefTopology" in AST[0]["members"][i][1]:
            walkTopology(AST[0]["members"][i], "")

    return 1


def load_locs():
    # open example-locs.fpp
    with open(FPP_LOCS, "r") as f:
        lines = f.readlines()

    locations = {
        "topologies": [],
        "instances": [],
    }

    for line in lines:
        idx = ""
        if "topology" in line.split(" ")[1]:
            idx = "topologies"
        elif "instance" in line.split(" ")[1]:
            idx = "instances"
        else:
            continue

        # remove quotations and newline
        line = line.replace('"', "").replace("\n", "")

        location = line.split(" ")[-1]

        # check if location is absolute
        if not os.path.isabs(location):
            location = Path(FPP_LOCS).parent / location

        locations[idx].append(
            {
                "name": line.split(" ")[2],
                "location": location,
            }
        )

    return locations


def find_in_locs(locs, type, name):
    for item in locs[type]:
        if item["name"] == name:
            return item["location"]
    return None

def topology_to_instance(topology_in):
    toRebuild = {"imports": [], "instances": [], "connections": [], "components": []}

    locations = load_locs()
    topology_file = find_in_locs(locations, "topologies", topology_in["topology"])
    topology_file = openFppFile(topology_file)

    st_Class = Utils.module_walker(
        topology_file[0]["members"],
        topology_in["topology"],
        "DefTopology",
        Parser.TopologyParser,
    )

    for member in st_Class.members():
        if "SpecCompInstance" in member[1]:
            instance = Parser.InstanceSpecParser(member)
            instance.parse()
            toRebuild["instances"].append(instance)

        if "SpecConnectionGraph" in member[1]:
            connection = Parser.ConnectionGraphParser(member)
            connection.parse()
            toRebuild["connections"].append(connection)

        if "SpecTopImport" in member[1]:
            imp = Parser.TopologyImport(member)
            imp.parse()
            toRebuild["imports"].append(imp)

    numReplaced = 0
    toRebuild["locals"] = []
    for instance in toRebuild["instances"]:
        preannot = instance.instance_preannot
        replaced = False
        isLocal = False

        if preannot is not None and len(preannot) > 0:
            if "! is local" == preannot[0]:
                isLocal = True

        for replacement in topology_in["instanceReplacements"]:
            if instance.instance_name in replacement["toReplace"] and not isLocal:
                numReplaced = numReplaced + 1
                instance.instance_name = replacement["replacer"]
                replaced = True
                break

        if not replaced and isLocal:
            toRebuild["locals"].append(instance.instance_name)

    if numReplaced != len(topology_in["instanceReplacements"]):
        print(
            f"[ERR] Failed to replace all component instances in topology instance {topology_in['qf']}. You may have tried to replace an instance that does not exist or is local to {topology_in['topology']}."
        )
        sys.exit(1)

    for instance in toRebuild["instances"]:
        if instance.instance_name in toRebuild["locals"]:
            try:
                instance_file = find_in_locs(
                    locations, "instances", instance.instance_name
                )
                instance_file = openFppFile(instance_file)
            except Exception as e:
                print(
                    f"[ERR] Failed to open instance file location for {instance.instance_name}. This most likely means that your instance is not properly qualified in your file."
                )
                sys.exit(1)

            compInst = Utils.module_walker(
                instance_file[0]["members"],
                instance.instance_name,
                "DefComponentInstance",
                Parser.InstanceParser,
            )

            compInst.qf = topology_in["topology"] + "." + compInst.instance_name

            toRebuild["components"].append(compInst)

    for connections in toRebuild["connections"]:
        for connection in connections.cg_connections:
            source = ".".join(connection["source"]["name"].split(".")[:-1])
            sourcePort = connection["source"]["name"].split(".")[-1]

            dest = ".".join(connection["dest"]["name"].split(".")[:-1])
            destPort = connection["dest"]["name"].split(".")[-1]

            for instance in topology_in["instanceReplacements"]:
                if source == instance["toReplace"]:
                    source = instance["replacer"]

                if dest == instance["toReplace"]:
                    dest = instance["replacer"]

            for instance in toRebuild["instances"]:
                if source in toRebuild["locals"]:
                    source = f"__{topology_in['qf'].split('.')[-1]}_instances.{source.split('.')[-1]}"

                if dest in toRebuild["locals"]:
                    dest = f"__{topology_in['qf'].split('.')[-1]}_instances.{dest.split('.')[-1]}"

            connection["source"]["name"] = source + "." + sourcePort
            connection["dest"]["name"] = dest + "." + destPort

    if (
        topology_in["configReplacement"]["from"] != ""
        and topology_in["configReplacement"]["to"] != ""
    ):
        toRebuild = Utils.replaceConfig(topology_in["configReplacement"], toRebuild)

    generateFppFile(toRebuild, topology_in)


def generateFppFile(toRebuild, topology_in):
    modules_to_generate = topology_in["qf"].split(".")
    topology_to_generate = modules_to_generate.pop()

    fileContent = ""
    moduleClosures = ""
    
    for module in modules_to_generate:
        fileContent += FppWriter.FppModule(module).open() + "\n"
        moduleClosures += FppWriter.FppModule(module).close() + "\n"

    if len(toRebuild["components"]) > 0:
        localModule = FppWriter.FppModule(f"__{topology_to_generate}_instances")
        fileContent += localModule.open() + "\n"

        # write base id
        fileContent += (
            FppWriter.FppConstant("LOCAL_BASE_ID", topology_in["baseID"]).write() + "\n"
        )

        for component in toRebuild["components"]:
            component.instance_elements["base_id"] += "+ LOCAL_BASE_ID"
            Utils.phase_rewriter(component, topology_in)
            fileContent += component.write() + "\n"

        fileContent += localModule.close() + "\n"

    fileContent += (
        FppWriter.FppModule(topology_in["topology"].split(".")[-1]).open() + "\n"
    )

    fileContent += FppWriter.FppTopology(topology_to_generate).open() + "\n"

    if len(toRebuild["imports"]) > 0:
        for imp in toRebuild["imports"]:
            fileContent += imp.write() + "\n"

    if len(toRebuild["instances"]) > 0:
        for instance in toRebuild["instances"]:
            if instance.instance_name in toRebuild["locals"]:
                instance.instance_name = f"__{topology_to_generate}_instances.{instance.instance_name.split('.')[-1]}"
            fileContent += instance.write() + "\n"

    if len(toRebuild["connections"]) > 0:
        for connection in toRebuild["connections"]:
            fileContent += connection.write() + "\n"

    fileContent += "}\n}\n"
    fileContent += moduleClosures

    WRITTEN_FILE_PIECES.append(fileContent)


def main():
    """
    Entry point to the tool. Uses argparse to parse command line arguments.

    Args:
        --locs [path]:          path to locs.fpp file
        --f, --file [path]:     path to file to check for subtopology instances
        --p, --path [path]:     path to the output file
        --c, --cache [path]:    path to the fpp cache folder

    Return:
        If no subtopology instances in the given file, an exception will be raised
        Otherwise, there will be a proper sys.exit(0)
    """
    print("[HELLO] Subtopology autocoder called.")
    parser = argparse.ArgumentParser(description="Generate FPP files for subtopologies")
    parser.add_argument("--locs", help="location of locs.fpp file", required=True)

    parser.add_argument("--f", "--file", help="fpp file to process", required=True)

    parser.add_argument("--p", "--path", help="path to output directory", required=True)

    parser.add_argument(
        "--c", "--cache", help="path to fpp cache folder", required=False
    )

    parser.add_argument(
        "--t",
        "--test",
        help="bypasses dependency management for testing",
        action=argparse.BooleanOptionalAction,
    )

    parsed, _ = parser.parse_known_args()

    global FPP_LOCS
    global FPP_OUTPUT
    global FPP_CACHE
    global FPP_INPUT
    global IN_TEST

    FPP_LOCS = parsed.locs
    FPP_OUTPUT = parsed.p
    FPP_CACHE = parsed.c
    FPP_INPUT = parsed.f
    IN_TEST = parsed.t or False

    if not os.path.isabs(FPP_LOCS):
        FPP_LOCS = Path(FPP_LOCS).resolve()

    if not os.path.isabs(FPP_OUTPUT):
        FPP_OUTPUT = Path(FPP_OUTPUT).resolve()

    if not IN_TEST:
        if not os.path.isabs(FPP_CACHE):
            FPP_CACHE = Path(FPP_CACHE).resolve()

    try:
        if not Utils.quickFileScan(parsed.f):
            raise Exception("File does not contain magic annotations")

        visitFppFile(parsed.f)
        if len(TOPOLOGIES_TO_INSTANTIATE) > 0:
            for topology in TOPOLOGIES_TO_INSTANTIATE:
                topology_to_instance(topology)
        else:
            raise Exception("No topologies to instantiate")

        try:
            Utils.writeFppFile(
                f"{FPP_OUTPUT}",
                "\n".join(WRITTEN_FILE_PIECES),
            )
        except Exception as e:
            raise Exception(f"Failed to write final subtopologies file: {e}")

        try:
            newLocs = fpp.fpp_locate_defs(FPP_OUTPUT, FPP_LOCS)
            dirOfOutput = os.path.dirname(FPP_OUTPUT)

            Utils.writeFppFile(
                f"{dirOfOutput}/st-locs.fpp",
                newLocs,
            )
        except Exception as e:
            raise Exception(f"Failed to write new locs file: {e}")

        if not IN_TEST:
            Utils.updateDependencies(
                FPP_CACHE, FPP_OUTPUT, [FPP_LOCS, f"{dirOfOutput}/st-locs.fpp"]
            )

        TOPOLOGIES_TO_INSTANTIATE.clear()
        WRITTEN_FILE_PIECES.clear()
        FPP_LOCS = ""
        FPP_OUTPUT = ""
        FPP_CACHE = ""
        FPP_INPUT = ""

        print(f"[DONE] file {parsed.f} processed successfully by subtopology ac")
    except Exception as e:
        print(f"[MESSAGE] {e}")
        raise
        sys.exit(1)


if __name__ == "__main__":
    main()
