import os
import fpp_interface as fpp
import fpp_json_ast_parser as Parser
import fpp_writer as FppWriter
import tool as MainTool
import json
import utils as Utils
import shutil
import argparse
import sys
from pathlib import Path

def quickInterfaceCheck(pathToFile, topologyName):
    with open(pathToFile, "r") as f:
        fileContents = f.read()
        
    for line in fileContents.split("\n"):
        if f"connections Interface_{topologyName}" in line:
            return True
    return False

def clean_cg_from_file(cg_name, path_to_file, include):
    with open(path_to_file, "r") as f:
        fileContents = f.read()
       
    deleting = False   
    for line in fileContents.split("\n"):
        if f"connections {cg_name}" in line and "{" in line:
            fileContents = fileContents.replace(line, "")
            deleting = True
            continue
        if deleting:
            if "}" in line:
                deleting = False
                
                if "_" in cg_name:
                    fileContents = fileContents.replace(line, include)
                    continue
            fileContents = fileContents.replace(line, "")


    Utils.writeFppFile(path_to_file, fileContents)

    # with open(path_to_file, "w") as f:
    #     f.write(fileContents)

def include_file_writer(pathToFile, cg: FppWriter.FppConnectionGraph, instances):
    toWrite = ""
    
    for instance in instances:
        toWrite += instance.write() + "\n"
        
    toWrite += "\n"
    toWrite += cg.open() + "\n" + cg.connect_from_db() + "\n" + cg.close() + "\n"
    
    pathToFile = os.path.join(os.getcwd(), pathToFile.split("/")[-1])
            
    with open(pathToFile, "w") as f:
        f.write(toWrite)
        
    return f'include "./{os.path.basename(pathToFile)}"'
    
def instance_already_specified(instances, instance_name):
    for instance in instances:
        if instance.instance_name in instance_name or instance_name in instance.instance_name:
            return True
    return False

def interface_replacer(subtopology: Parser.TopologyParser, main_topology: Parser.TopologyParser, topology_name: str, ST_Interfaces):    
    subtopology_cg = None
    main_topology_cg = None
    
    new_cg = FppWriter.FppConnectionGraph(f"Interface_{topology_name}")
    
    instances = []
        
    for member in subtopology.members():
        if "SpecConnectionGraph" in member[1]:
            cg:Parser.ConnectionGraphParser = Parser.ConnectionGraphParser(member)
            cg.parse()
            
            if cg.cg_name == "Interface":
                subtopology_cg = cg
                break
            
    for member in main_topology.members():
        if "SpecConnectionGraph" in member[1]:
            cg:Parser.ConnectionGraphParser = Parser.ConnectionGraphParser(member)
            cg.parse()
            
            if cg.cg_name == f"Interface_{topology_name}":
                main_topology_cg = cg
                break
            
    if subtopology_cg is None:
        print(f"[WARN] Subtopology has no Interface connection graph")
        return
    if main_topology_cg is None:
        print(f"[WARN] Main topology has no Interface_{topology_name} connection graph")
        return
    
    for connection in subtopology_cg.cg_connections:
        if ST_Interfaces['in'].instance_name in connection["source"]["name"]:
            if connection["source"]['name'].split("_")[-1] != "in":
                raise Exception("Invalid input connection in subtopology")
            
            output_dest = ''.join(connection["source"]['name'].split("_")[:-1]) + connection['source']['num']
            replaceWith = connection['dest']
            
            instName = '.'.join(replaceWith['name'].split(".")[:-1])
            if not instance_already_specified(instances, instName):
                instances.append(FppWriter.FppInstanceSpec(instName))
                        
            for connection in main_topology_cg.cg_connections:
                if output_dest in connection["dest"]["name"]:
                    new_cg.save_connection({"source": connection["source"], "dest": replaceWith})
                    break
                
        if ST_Interfaces['out'].instance_name in connection["dest"]["name"]:
            input_source = connection['dest']['name'] + "_out" + connection['dest']['num']
            replaceWith = connection['source']
            
            instName = '.'.join(replaceWith['name'].split(".")[:-1])
            if not instance_already_specified(instances, instName):
                instances.append(FppWriter.FppInstanceSpec(instName))
            
            for connection in main_topology_cg.connections():
                if input_source in connection["dest"]["name"]:
                    new_cg.save_connection({"source": replaceWith, "dest": connection["dest"]})
                    break
                    
    return new_cg, instances

def interface_entrypoint(pathToSubtopology, pathToMainTopology, locs, topologyName, ST_Interfaces):    
    subtopology = MainTool.openFppFile(pathToSubtopology, locs, True)
    main_topology = MainTool.openFppFile(pathToMainTopology, locs, True)
    
    stqf = ""
    mtqf = ""
    
    for i in range(len(subtopology[0]["members"])):
        if "DefModule" in subtopology[0]["members"][i][1]:
            module = Parser.ModuleParser(subtopology[0]["members"][i])
            module.parse()
            
            stqf = module.module_name
                        
            subtopology = Utils.module_walker(
                subtopology[0]["members"], 
                f"{stqf}.{topologyName}", 
                "DefTopology", 
                Parser.TopologyParser
            )

    for i in range(len(main_topology[0]["members"])):
        if "DefModule" in main_topology[0]["members"][i][1]:
            module = Parser.ModuleParser(main_topology[0]["members"][i])
            module.parse()
            
            mtqf = module.module_name
                        
            main_topology = Utils.module_walker(main_topology[0]["members"], f"{mtqf}.{mtqf}", "DefTopology", Parser.TopologyParser)
            
    new_cg, instances = interface_replacer(subtopology, main_topology, topologyName, ST_Interfaces)
    
    if new_cg is None or new_cg.connections == []:
        raise Exception("[ERR] Interface replacement failed")
        
    include_file = include_file_writer(f"./{topologyName}_interface.fppi", new_cg, instances)
    
    clean_cg_from_file(f"Interface_{topologyName}", pathToMainTopology, include_file)
    clean_cg_from_file(f"Interface", pathToSubtopology, include_file)