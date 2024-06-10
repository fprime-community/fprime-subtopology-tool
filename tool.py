import os
import fpp_interface as fpp
import fpp_json_ast_parser as Parser
import fpp_writer as FppWriter
import json
import utils as Utils
import shutil

FPP_FILES_LOCATED_IN = "../ex3-ac"

LOCALLY_DEFINED_INSTANCES = []
TOPOLOGIES_TO_INSTANTIATE = []

def walkModule(data, oldQf):
    module = Parser.ModuleParser(data)
    module.parse()
    
    if oldQf == "":
        qf = module.module_name
    else:
        qf = oldQf + "." + module.module_name # qualifier
    
    for member in module.members():
        if "DefComponentInstance" in member[1]:
            instance = Parser.InstanceParser(member)
            instance.parse()
            
            isLocal = Utils.component_to_local(instance)
            if isLocal:
                isLocal['qf'] = qf
                LOCALLY_DEFINED_INSTANCES.append(isLocal)
        
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
        qf = module + "." + topology.topology_name # qualifier
    
    isInstantiable = Utils.topology_to_instance(topology)
    
    if isInstantiable:
        isInstantiable['qf'] = qf
        TOPOLOGIES_TO_INSTANTIATE.append(isInstantiable)
        
    for member in topology.members():
        if "DefTopology" in member[1]:
            walkTopology(member, qf)
            
        if "DefModule" in member[1]:
            walkModule(member, qf)
    
    return qf

def visitFppFile(path):
    # create temporary dir
    try:
        os.mkdir("tmp")
        os.chdir("tmp")
    except FileExistsError:
        os.chdir("tmp")
    
    fpp.fpp_to_json("../" + path)
    
    # parse json
    with open("fpp-ast.json", "r") as f:
        AST = json.load(f)
        
    for i in range(len(AST[0]['members'])):
        if "DefModule" in AST[0]['members'][i][1]:
            walkModule(AST[0]['members'][i], "")
            
        if "DefTopology" in AST[0]['members'][i][1]:
            walkTopology(AST[0]['members'][i], "")
        
    os.chdir("..")
    shutil.rmtree("tmp", ignore_errors=True)

def getFppFiles():
    fpp_files = []
    for root, dirs, files in os.walk(FPP_FILES_LOCATED_IN):
        for file in files:
            if file.endswith(".fpp"):
                fpp_files.append(os.path.join(root, file))
    return fpp_files

def main():
    files = getFppFiles()
    for file in files:
        visitFppFile(file)
        
    print(LOCALLY_DEFINED_INSTANCES)
    print(TOPOLOGIES_TO_INSTANTIATE)
    
if __name__ == "__main__":
    main()