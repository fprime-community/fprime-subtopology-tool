import fpp_json_ast_parser as Parser
import fpp_interface as fpp
import os
import shutil
import tool as MainTool


def topology_to_instance(topology: Parser.TopologyParser):
    """
    Turn a topology provided by the parser into a topology instance that can be written to
    an fpp file.

    Args:
        topology: The topology to turn into an instance

    Returns:
        instanceDetails: The instance details for the topology
    """
    postannotation = topology.topology_postannot

    if postannotation is None or postannotation == []:
        return
    else:
        if "!" != postannotation[0][0]:
            return print(
                f"[WARN] Topology {topology.topology_name} does not contain magic annotations"
            )
        else:
            pass

    instantiation = postannotation[0][2:].split(" ")
    instanceDetails = {
        "topology_class": topology,
        "topology": "",
        "baseID": "",
        "instanceReplacements": [],
        "configReplacement": {"from": "", "to": ""},
    }

    if "is" == instantiation[0]:
        # topology may be an instance
        instanceDetails["topology"] = instantiation[1]

        if "base" == instantiation[2] and "id" == instantiation[3]:
            withIdx = 5
            for i in range(4, len(instantiation)):
                if "with" != instantiation[i]:
                    instanceDetails["baseID"] += instantiation[i]
                else:
                    withIdx = i
                    break
            if withIdx < len(instantiation):
                if (
                    "with" == instantiation[withIdx]
                    and "{" == instantiation[withIdx + 1]
                ):
                    expectBracket = False
                    error = False
                    endBracket = False
                    for i in range(1, len(postannotation)):
                        if "!" != postannotation[i][0]:
                            print(
                                f"[ERR] Expected ! to start the magic annotation but found {postannotation[i]}"
                            )
                            error = True
                        else:
                            postannotation[i] = postannotation[i][2:]

                        if "}" == postannotation[i]:
                            endBracket = True
                            break
                        elif expectBracket:
                            print(f"[ERR] Expected }} but found {postannotation[i]}")
                            error = True
                        else:
                            toReplace = None
                            replacer = None
                            equalIdx = postannotation[i].find("=")

                            if equalIdx == -1:
                                print(
                                    f"[ERR] Expected = in instance replacement list but found {postannotation[i]}"
                                )
                                error = True
                                break

                            toReplace = postannotation[i][:equalIdx].strip()
                            replacer = postannotation[i][equalIdx + 1 :].strip()

                            commaExists = replacer.find(",")

                            if commaExists != -1:
                                replacer = replacer[:commaExists]
                            else:
                                expectBracket = True

                            if "Config" in toReplace:
                                instanceDetails["configReplacement"]["from"] = toReplace
                                instanceDetails["configReplacement"]["to"] = replacer
                            else:
                                instanceDetails["instanceReplacements"].append(
                                    {"toReplace": toReplace, "replacer": replacer}
                                )

                    if error:
                        raise Exception(
                            f"[ERR] Topology instance {topology.topology_name} has an invalid magic annotation"
                        )
                        # we NEED to hard exit
                    if not endBracket:
                        raise Exception(
                            f"[ERR] Expected }} to close magic annotation of {topology.topology_name} instance but found nothing."
                        )
    return instanceDetails


def module_walker(AST, qf, type, type_parser):
    """
    This function walks through the JSON AST of a module and returns the AST for a
    specific element type with the qualified name qf.

    Args:
        AST: The JSON AST of the module
        qf: The qualified name of the element to find (i.e. module.member.member)
        type: The type of element to find (i.e. DefTopology, DefComponentInstance)
        type_parser: The parser for the element type (i.e. Parser.TopologyParser)

    Returns:
        The AST for the element with the qualified name qf
    """

    qf = qf.split(".")
    for m in AST:
        if "DefModule" in m[1]:
            module = Parser.ModuleParser(m)
            module.parse()

            if module.module_name == qf[0] and len(qf) > 1:
                for _m in module.members():
                    if "DefModule" in _m[1]:
                        moduleDeeper = Parser.ModuleParser(_m)
                        moduleDeeper.parse()

                        if moduleDeeper.module_name == qf[1] and len(qf) > 2:
                            return module_walker(
                                moduleDeeper.members(),
                                ".".join(qf[1:]),
                                type,
                                type_parser,
                            )
                    if type in _m[1]:
                        _type = type_parser(_m)
                        _type.parse()

                        if _type.qf == qf[1]:
                            return _type
            elif module.module_name == qf[0] and len(qf) == 1:
                return m


# write (with formatting) to fpp file
def writeFppFile(file, content):
    """
    This function writes content to a file and formats the file using fpp-format.

    Args:
        file: The file to write to (i.e. /path/to/file.fpp)
        content: The content to write to the file

    Returns:
        None
    """

    # check if the directory exists
    # if "/" in file:
    #     directory = file[: file.rfind("/")]
    #     if not os.path.exists(directory):
    #         os.makedirs(directory)

    # make directories if they don't exist
    if not os.path.exists(os.path.dirname(file)):
        os.makedirs(os.path.dirname(file))

    with open(file, "w") as f:
        f.write(content)

    try:
        postFormat = fpp.fpp_format(file)

        # overwrite the file with the formatted version
        f = open(file, "w")
        f.write(postFormat)
        f.close()
    except:
        raise Exception("[ERR] fpp-format failed")

    return file


def quickFileScan(path):
    """
    Quickly check if a file has magic annotations
    """

    with open(path, "r") as f:
        lines = f.readlines()
        for line in lines:
            if "@!" in line or "@<!" in line:
                return True
    return False


def updateDependencies(
    fpp_cache, path, locs: list, dependency_replacements, removedTops
):
    """
    This function updates the dependency cache files for a module. This tells the future
    autocoder what the dependencies are for the new subtopology we made.

    Args:
        fpp_cache: The path to the fpp cache directory
        path: Path to the fpp file to calculate dependencies for
        locs: List of locs files to use for dependency calculation
    """

    try:
        if not os.path.exists(fpp_cache + "/tmp"):
            os.mkdir(fpp_cache + "/tmp")

        fpp.fpp_depend(fpp_cache + "/tmp", path, locs)

        dependencyFiles = [
            "direct.txt",
            "framework.txt",
            "generated.txt",
            "include.txt",
            "unittest.txt",
            "stdout.txt",
        ]

        topologyGeneratedFilePostfixes = [
            "TopologyAc.cpp",
            "TopologyAc.hpp",
            "TopologyAppAi.xml",
            "TopologyDictionary.json",
        ]

        FilesToRemove = []

        for removedTop in removedTops:
            FilesToRemove.append(
                list(map(lambda x: removedTop + x, topologyGeneratedFilePostfixes))
            )

        for file in dependencyFiles:
            with open(fpp_cache + "/tmp/" + file, "r") as f:
                with open(fpp_cache + "/" + file, "a") as out:
                    for line in f:
                        if ".subtopologies.fpp" in line:
                            continue

                        if "/ST-Interface/" in line:
                            continue

                        if "/instances.fpp" in line:
                            continue

                        with open(fpp_cache + "/" + file, "r") as check:
                            if line in check:
                                continue

                        out.write(line)

            actContent = []
            with open(fpp_cache + "/" + file, "r") as check:
                for line in check:
                    if "/ST-Interface/" in line:
                        continue

                    lineNeedsToBeRemoved = False
                    for removeSet in FilesToRemove:
                        for remove in removeSet:
                            if remove in line:
                                lineNeedsToBeRemoved = True
                                break

                    if lineNeedsToBeRemoved:
                        continue

                    for replacement in dependency_replacements:
                        if replacement["from"] in line:
                            line = replacement["to"]

                    if line != " NONE ":
                        actContent.append(line)

            actContent = list(filter(lambda x: x != "\n", actContent))

            with open(fpp_cache + "/" + file, "w") as check:
                check.writelines(actContent)

        shutil.rmtree(fpp_cache + "/tmp", ignore_errors=True)

        print("[INFO] Updated dependency cache files")
    except Exception as e:
        raise Exception(f"[ERR] Failed to update dependency cache files: {e}")

    return 1


def cleanMainFppFile(path):
    """
    Clean up the artifact of the topology in the main fpp file. This removes the
    duplicate definitions error with the build.
    """

    with open(path, "r") as f:
        lines = f.readlines()

    removingTopology = False
    removedTopology = False
    for i in range(len(lines)):
        if f"topology" in lines[i] and "@<!" in lines[i + 1]:
            lines[i] = ""
            removingTopology = True
            removedTopology = True
            continue

        if removingTopology and "@<!" in lines[i]:
            lines[i] = ""
            continue

        if removingTopology and lines[i] == "":
            removingTopology = False
            continue

    with open(path, "w") as f:
        f.writelines(lines)

    if removedTopology:
        return 1
    else:
        return 0


def removeFromMainLocs(path, qf):
    """
    Remove the subtopology instance from the locs file
    """

    with open(path, "r") as f:
        lines = f.readlines()

    for i in range(len(lines)):
        if qf in lines[i]:
            lines[i] = ""
            break

    with open(path, "w") as f:
        f.writelines(lines)


def replaceConfig(replacement, toRebuild):
    """
    This function replaces instances of the config module in the subtopology with a new
    configuration module.

    Args:
        replacement: The replacement {from: "Config", to: "NewConfig"}
        toRebuild: The subtopology to rebuild
    """
    cFrom = replacement["from"]
    cTo = replacement["to"]

    for component in toRebuild["components"]:
        elements = component["instance_elements"]
        if cFrom in elements["base_id"]:
            component["instance_elements"]["base_id"].replace(cFrom, cTo)

        if cFrom in elements["queue"]:
            component["instance_elements"]["queue"].replace(cFrom, cTo)

        if cFrom in elements["stack"]:
            component["instance_elements"]["stack"].replace(cFrom, cTo)

        if cFrom in elements["cpu"]:
            component["instance_elements"]["cpu"].replace(cFrom, cTo)

        if cFrom in elements["priority"]:
            component["instance_elements"]["priority"].replace(cFrom, cTo)

    return toRebuild


def phase_rewriter(component: Parser.InstanceParser, topology_in):
    """
    Phases may utilize component-specific functions that are not qualified properly when
    the subtopology is instantiated. This function rewrites the phase function calls to
    use the proper qualified function name.

    Args:
        component: The component to rewrite the phase function calls for
        topology_in: The topology instance to rewrite the phase function calls for
    """

    modules_to_generate = topology_in["qf"].split(".")
    topology_to_generate = modules_to_generate.pop()
    instance_name = component.instance_name.split(".")[-1]
    new_function_name = f"__{topology_to_generate}_instances_{instance_name}"

    for phase in component.instance_elements["phases"]:
        if (
            component.instance_elements["phases"][phase] is not None
            and component.instance_elements["phases"][phase] != ""
        ):
            print(
                f"[INFO] Rewriting phase {phase} function calls for {component.qf}..."
            )
            code = component.instance_elements["phases"][phase]

            word = ""
            stateFound = False
            stateVar = ""
            for character in code:
                if character in [
                    "\n",
                    "\t",
                    " ",
                    ".",
                    "(",
                    ")",
                    "{",
                    "}",
                    ";",
                    ",",
                    ":",
                ]:
                    if f"_{instance_name}" in word:
                        # we have found the function name
                        code = code.replace(word, new_function_name)
                        word = ""
                        continue

                    if "state" in word and stateFound == False:
                        stateFound = True
                        stateVar += "state"

                        word = ""
                        continue

                    if (
                        character
                        in [
                            "\n",
                            "\t",
                            " ",
                            "(",
                            ")",
                            "{",
                            "}",
                            ";",
                            ",",
                            ":",
                        ]
                        and stateFound
                    ):
                        stateFound = False
                        stateVar += "." + word
                        continue

                    if stateFound:
                        stateVar += "." + word
                        word = ""
                        continue

                    if stateFound == False and stateVar != "":
                        splitted = stateVar.split(".")
                        if stateVar[-1] == ".":
                            splitted.pop()

                        actualVariable = splitted[-1]
                        newState = (
                            f"state.st.{topology_to_generate}State.{actualVariable}"
                        )

                        code = code.replace(stateVar, newState)

                        stateVar = ""

                word += character
            component.instance_elements["phases"][phase] = code


def removeEmptyTopology(file, main_file, locs, topology):
    """
    Remove the empty topology from the main fpp file
    """

    subtopology = MainTool.openFppFile(file, locs, True)

    theTopology = module_walker(
        subtopology[0]["members"], topology, "DefTopology", Parser.TopologyParser
    )

    cgs = 0
    for member in theTopology.members():
        if "SpecConnectionGraph" in member[1]:
            cgs += 1

    if cgs == 0:
        with open(file, "r") as f:
            lines = f.readlines()

        removingTopology = False
        removedTopology = False

        topology = topology.split(".")[-1]

        for i in range(len(lines)):
            if f"topology {topology}" in lines[i]:
                removingTopology = True
                removedTopology = False
                lines[i] = ""
                continue

            if removingTopology and "}" in lines[i]:
                removingTopology = False
                removedTopology = True
                lines[i] = ""
                continue

            if removingTopology:
                lines[i] = ""
                continue

        with open(file, "w") as f:
            f.writelines(lines)

        with open(main_file, "r") as f:
            lines = f.readlines()

        for i in range(len(lines)):
            if f"import {topology}" in lines[i]:
                lines[i] = ""
                break

        with open(main_file, "w") as f:
            f.writelines(lines)

        return 1

    return 0


# def subtopologyStatesAPI(topName):
#     return f"

#     // SubtopologyStates API
#     namespace {topName} {{
#         void
#     "


def generateACStateStruct(hpp_files, topologies):
    print("[INFO] Generating SubtopologyStates.hpp file...")
    structTypes = []
    dirToSave = hpp_files[0].split("/")[:-1]

    pathToSave = "/".join(dirToSave) + "/SubtopologyStates.hpp"
    
    hppName = ""

    for topology in topologies:
        topName = topology["qf"].split(".")[-1]
        oldTopName = topology["topology"].split(".")[-1]
        
        hppName = topology["qf"].split(".")[0]

        for hpp_file in hpp_files:
            if topName in hpp_file:
                with open(hpp_file, "r") as f:
                    lines = f.readlines()

                for i in range(len(lines)):
                    if f"struct {oldTopName}State" in lines[i]:
                        structTypes.append(
                            {
                                "topology": topName,
                                "struct": f"{oldTopName}State",
                                "file": hpp_file,
                            }
                        )

                        break

    ifndef = f"#ifndef {hppName}SUBTOPOLOGY_STATES_HPP\n"
    define = f"#define {hppName}SUBTOPOLOGY_STATES_HPP\n"
    endif = f"\n#endif // {hppName}SUBTOPOLOGY_STATES_HPP\n"
    
    if len(structTypes) == 0:
        struct = "struct SubtopologyStates {\n};"

        with open(pathToSave, "w") as f:
            f.write(ifndef)
            f.write(define)
            f.write(struct)
            f.write(endif)

        return pathToSave

    else:
        hpp_files_include = []
        struct = "struct SubtopologyStates {\n"

        for structType in structTypes:
            if len(structTypes) > 1:
                for i in range(0, structTypes.index(structType)):
                    if structType[i] == structType:
                        pass
                    elif structType["struct"] == structTypes[i]["struct"]:
                        continue
                
            hpp_files_include.append(
                f"#include \"{structType['file'].split('/')[-1]}\"" + "\n"
            )

            struct += structType["struct"] + f" {structType['topology']}State;\n"

        struct += "};"

        try:
            with open(pathToSave, "w") as f:
                f.write(ifndef)
                f.write(define)
                f.writelines(hpp_files_include)
                f.write(struct)
                f.write(endif)
        except Exception as e:
            raise Exception(f"[ERR] Failed to generate SubtopologyStates.hpp file: {e}")

        return pathToSave
