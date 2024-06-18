import os
import fpp_interface as fpp
import fpp_json_ast_parser as Parser
import fpp_writer as FppWriter
import json
import utils as Utils
import shutil
import argparse
import sys

TOPOLOGIES_TO_INSTANTIATE = []
WRITTEN_FILE_PIECES = []

def walkModule(data, oldQf):
    module = Parser.ModuleParser(data)
    module.parse()

    if oldQf == "":
        qf = module.module_name
    else:
        qf = oldQf + "." + module.module_name  # qualifier

    for member in module.members():
        if "DefComponentInstance" in member[1]:
            instance = Parser.InstanceParser(member)
            instance.parse()

        if "DefTopology" in member[1]:
            walkTopology(member, qf)

        if "DefModule" in member[1]:
            walkModule(member, qf)

    return qf


def walkTopology(data, module):
    topology = Parser.TopologyParser(data)
    topology.parse()

    if module == "":
        qf = topology.topology_name
    else:
        qf = module + "." + topology.topology_name  # qualifier

    isInstantiable = Utils.topology_to_instance(topology)

    if isInstantiable:
        isInstantiable["qf"] = qf
        TOPOLOGIES_TO_INSTANTIATE.append(isInstantiable)

    for member in topology.members():
        if "DefTopology" in member[1]:
            walkTopology(member, qf)

        if "DefModule" in member[1]:
            walkModule(member, qf)

    return qf


def openFppFile(path):
    # create temporary dir
    
    # get directory of path without file
    # check if path is absolute
    if not os.path.isabs(path):
        path = os.path.abspath(path)
        
    pathDir = os.path.dirname(path)
        
    if not os.path.exists(pathDir + "/tmp"):
        try:
            os.mkdir(pathDir + "/tmp")
        except OSError:
            print ("Creation of the directory %s failed" % pathDir + "/tmp")
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
            location = os.path.abspath(location)

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
    topology = topology_in["topology_class"]
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
                    if instance.instance_name in replacement["toReplace"]:
                        numReplaced = numReplaced + 1
                        instance.instance_name = replacement["replacer"]
                        replaced = True
                        break

        if not replaced and isLocal:
            toRebuild["locals"].append(instance.instance_name)

    if numReplaced != len(topology_in["instanceReplacements"]):
        print(
            f"[ERR] Failed to replace all component instances in topology instance {topology_in['qf']}. You may have tried to alis an instance that does not exist or is not local to {topology_in['topology']}."
        )
        sys.exit(1)

    for instance in toRebuild["instances"]:
        if instance.instance_name in toRebuild["locals"]:
            instance_file = find_in_locs(locations, "instances", instance.instance_name)
            instance_file = openFppFile(instance_file)

            toRebuild["components"].append(
                Utils.module_walker(
                    instance_file[0]["members"],
                    instance.instance_name,
                    "DefComponentInstance",
                    Parser.InstanceParser,
                )
            )

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

                if source in toRebuild["locals"]:
                    source = f"__{topology_in['qf'].split('.')[-1]}_instances.{source.split('.')[-1]}"

                if dest in toRebuild["locals"]:
                    dest = f"__{topology_in['qf'].split('.')[-1]}_instances.{dest.split('.')[-1]}"

            connection["source"]["name"] = source + "." + sourcePort
            connection["dest"]["name"] = dest + "." + destPort

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
        fileContent += FppWriter.FppConstant("LOCAL_BASE_ID", topology_in['baseID']).write() + "\n"

        for component in toRebuild["components"]:
            component.instance_elements["base_id"] += "+ LOCAL_BASE_ID"
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
        --loca [path]:      path to locs.fpp file
        --f, --file [path]: path to file to check for subtopology instances
        --p, --path [path]: path to the output file
        
    Return:
        If no subtopology instances in the given file, an exception will be raised
        Otherwise, there will be a proper sys.exit(0)
    """
    print("[HELLO] Subtopology autocoder called.")
    parser = argparse.ArgumentParser(description="Generate FPP files for subtopologies")
    parser.add_argument(
        "--locs",
        help="location of locs.fpp file",
        required=True
    )
    
    parser.add_argument(
        "--f",
        "--file",
        help="fpp file to process",
        required=True
    )
    
    parser.add_argument(
        "--p",
        "--path",
        help="path to output directory",
        required=True
    )
    
    parsed, _ = parser.parse_known_args()
    
    global FPP_LOCS
    global FPP_OUTPUT
    FPP_LOCS = parsed.locs
    FPP_OUTPUT = parsed.p
    
    if not os.path.isabs(FPP_LOCS):
        FPP_LOCS = os.path.abspath(FPP_LOCS)
        
    if not os.path.isabs(FPP_OUTPUT):
        FPP_OUTPUT = os.path.abspath(FPP_OUTPUT)
    
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
                '\n'.join(WRITTEN_FILE_PIECES),
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
            

        TOPOLOGIES_TO_INSTANTIATE.clear()
        FPP_LOCS = ""
        
        print(f"[DONE] file {parsed.f} processed successfully by subtopology ac")
    except Exception as e:
        print(f"[ERR] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
    
