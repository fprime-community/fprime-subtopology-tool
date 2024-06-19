import fpp_json_ast_parser as Parser
import fpp_interface as fpp
import sys
import os
import shutil

def component_to_local(component: Parser.InstanceParser):
    """
    This function checks if a component is local to the topology it is defined in based on
    the instance definition in the topology. In the current version of the tool, this
    function is not used.
    
    Args:
        component: The component to check if it is local to the topology
    
    Returns:
        None
    """
    
    preannotation = component.instance_preannot
    if preannotation is None or preannotation == "" or preannotation == []:
        return

    preannotation = preannotation[0]
    if "!" != preannotation[0] or preannotation == "" or preannotation is None:
        return print(f"[ERR] Component {component.instance_name} is not special")
    else:
        preannotation = preannotation[2:]

    if "local to topology" in preannotation:
        print(f"[INFO] Component {component.instance_name} is local to topology")

    # topology should be the last element of preannotation
    topology = preannotation.split(" ")[-1]

    return {"component": component, "linkedTopology": topology}


def topology_to_instance(topology: Parser.TopologyParser):
    postannotation = topology.topology_postannot

    if postannotation is None or postannotation == []:
        return
    else:
        if "!" != postannotation[0][0]:
            return print(f"[WARN] Topology {topology.topology_name} does not contain magic annotations")
        else:
            pass

    instantiation = postannotation[0][2:].split(" ")
    instanceDetails = {
        "topology_class": topology,
        "topology": "",
        "baseID": "",
        "instanceReplacements": [],
        "configReplacement": {
            "from": "",
            "to": ""
        }
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
                if "with" == instantiation[withIdx] and "{" == instantiation[withIdx + 1]:
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
                        print(
                            f"[ERR] Topology instance {topology.topology_name} has an invalid magic annotation"
                        )
                        # we NEED to hard exit
                        sys.exit(1)
                    if not endBracket:
                        print(
                            f"[ERR] Expected }} to close magic annotation of ${topology.topology_name} instance but found nothing."
                        )
                        sys.exit(1)
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
                        return module_walker(_m, ".".join(qf[1:]), type)
                    elif type in _m[1]:
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
    if "/" in file:
        directory = file[: file.rfind("/")]
        if not os.path.exists(directory):
            os.makedirs(directory)
                
    with open(file, "w") as f:
        f.write(content)

    try:
        postFormat = fpp.fpp_format(file)

        # overwrite the file with the formatted version
        f = open(file, "w")
        f.write(postFormat)
        f.close()
    except:
        print("[ERR] fpp-format failed")
        sys.exit(1)
        
    return file
        
def quickFileScan(path):
    """
    Quickly check if a file has magic annotations
    """
    
    with(open(path, "r")) as f:
        lines = f.readlines()
        for line in lines:
            if "@!" in line or "@<!" in line:
                return True
    return False

def updateDependencies(fpp_cache, path, locs: list):
    """
    This function updates the dependency cache files for a module. This tells the future 
    autocoder what the dependencies are for the new subtopology we made.
    
    Args:
        fpp_cache: The path to the fpp cache directory
        path: Path to the fpp file to calculate dependencies for
        locs: List of locs files to use for dependency calculation
    """
    
    try:
        os.mkdir(fpp_cache + "/tmp")
        
        fpp.fpp_depend(fpp_cache + "/tmp", path, locs)
        
        dependencyFiles = ['direct.txt', 'framework.txt', 'generated.txt', 'include.txt', 'unittest.txt', 'stdout.txt']
        
        for file in dependencyFiles:
            with open(fpp_cache + "/tmp/" + file, "r") as f:
                with open(fpp_cache + "/" + file, "a") as out:
                    for line in f:
                        # if ".subtopologies.fpp" in line:
                        #     continue
                        
                        with open(fpp_cache + "/" + file, "r") as check:
                            if line in check:
                                continue
                            
                        out.write(line)
                    
        shutil.rmtree(fpp_cache + "/tmp", ignore_errors=True)
        
        print("[INFO] Updated dependency cache files")
    except Exception as e:
        print(f"[ERR] Failed to update dependency cache files: {e}")
        sys.exit(1)
    
    return 1

def cleanMainFppFile(path, topology):
    """
    Clean up the artifact of the topology in the main fpp file
    """
    
    with open(path, "r") as f:
        lines = f.readlines()
        
    removingTopology = False
    removedTopology = False
    for i in range(len(lines)):
        if f"topology {topology}" in lines[i]:
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
    
def replaceConfig(replacement, toRebuild):
    cFrom = replacement["from"]
    cTo = replacement["to"]
    
    for component in toRebuild['components']:
        elements = component['instance_elements']
        if cFrom in elements['base_id']:
            component['instance_elements']['base_id'].replace(cFrom, cTo)
            
        if cFrom in elements['queue']:
            component['instance_elements']['queue'].replace(cFrom, cTo)
            
        if cFrom in elements['stack']:
            component['instance_elements']['stack'].replace(cFrom, cTo)
            
        if cFrom in elements['cpu']:
            component['instance_elements']['cpu'].replace(cFrom, cTo)
            
        if cFrom in elements['priority']:
            component['instance_elements']['priority'].replace(cFrom, cTo)

    return toRebuild