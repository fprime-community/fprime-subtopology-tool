import fpp_json_ast_parser as Parser

def component_to_local(component: Parser.InstanceParser):
    preannotation = component.instance_preannot
    if preannotation is None or preannotation == '' or preannotation == []:
        return
    
    preannotation = preannotation[0]
    if "!" != preannotation[0] or preannotation == '' or preannotation is None:
        return print(f"[ERR] Component {component.instance_name} is not special")
    else:
        preannotation = preannotation[2:]
    
    if "local to topology" in preannotation:
        print(f"[INFO] Component {component.instance_name} is local to topology")
    
    # topology should be the last element of preannotation
    topology = preannotation.split(" ")[-1]
    
    return {
        "component": component,
        "linkedTopology": topology
    }
    
def topology_to_instance(topology: Parser.TopologyParser):
    postannotation = topology.topology_postannot

    if postannotation is None or postannotation == []:
        return
    else:    
        if "!" != postannotation[0][0]:
            return print(f"[ERR] Topology {topology.topology_name} is not special")
        else:
            pass
        
    instantiation = postannotation[0][2:].split(" ")
    instanceDetails = {
        "topology": "",
        "baseID": "",
        "instanceReplacements": []
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
            
            if "with" == instantiation[withIdx] and "{" == instantiation[withIdx+1]:
                expectBracket = False
                error = False
                endBracket = False
                for i in range(1, len(postannotation)):
                    if "!" != postannotation[i][0]:
                        print(f"[ERR] Expected ! to start the special annotation but found {postannotation[i]}")
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
                            print(f"[ERR] Expected = in instance replacement list but found {postannotation[i]}")
                            error = True
                            break
                        
                        toReplace = postannotation[i][:equalIdx].strip()
                        replacer = postannotation[i][equalIdx+1:].strip()
                        
                        commaExists = replacer.find(",")
                                                    
                        if commaExists != -1:
                            replacer = replacer[:commaExists]
                        else:
                            expectBracket = True
                        
                        
                        instanceDetails["instanceReplacements"].append({
                            "toReplace": toReplace,
                            "replacer": replacer
                        })
                    
                if error:
                    return print(f"[ERR] Topology {topology.topology_name} has an invalid postannotation")
                if not endBracket:
                    return print(f"[ERR] Expected }} to close postannotation but found end of postannotation")
    
    return instanceDetails