import fpp_json_ast_parser as Parser
import fpp_interface as fpp
import sys


def component_to_local(component: Parser.InstanceParser):
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
            return print(f"[ERR] Topology {topology.topology_name} is not special")
        else:
            pass

    instantiation = postannotation[0][2:].split(" ")
    instanceDetails = {
        "topology_class": topology,
        "topology": "",
        "baseID": "",
        "instanceReplacements": [],
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

            if "with" == instantiation[withIdx] and "{" == instantiation[withIdx + 1]:
                expectBracket = False
                error = False
                endBracket = False
                for i in range(1, len(postannotation)):
                    if "!" != postannotation[i][0]:
                        print(
                            f"[ERR] Expected ! to start the special annotation but found {postannotation[i]}"
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

                        instanceDetails["instanceReplacements"].append(
                            {"toReplace": toReplace, "replacer": replacer}
                        )

                if error:
                    return print(
                        f"[ERR] Topology {topology.topology_name} has an invalid postannotation"
                    )
                if not endBracket:
                    return print(
                        f"[ERR] Expected }} to close postannotation but found end of postannotation"
                    )

    return instanceDetails


# locate a qualifier in a module
def module_walker(AST, qf, type, type_parser):
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
