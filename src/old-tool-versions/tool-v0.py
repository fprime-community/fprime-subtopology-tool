import os
import sys
import argparse
import fpp_interface as fpp
import fpp_json_ast_parser as Parser
import fpp_writer as FppWriter
import json


def component_to_local(component: Parser.InstanceParser):
    preannotation = component.instance_preannot[0]

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
    instanceDetails = {"topology": "", "baseID": "", "instanceReplacements": []}

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


def subtopologyParse(args):

    if not os.path.exists(args.input):
        print(f"[ERR] Input file {args.input} not found")
        sys.exit(1)

    # fpp.calculateDependencies(args.input)
    fpp.fpp_to_json(args.input)

    # open json file
    f = open("fpp-ast.json", "r")
    subtopologyFile = json.load(f)

    # print(subtopologyFile[0]['members'][0])

    localComponents = []
    instanceTopologies = []

    for i in range(len(subtopologyFile[0]["members"])):
        if "DefModule" in subtopologyFile[0]["members"][i][1]:
            module = Parser.ModuleParser(subtopologyFile[0]["members"][i])
            module.parse()

            for member in module.members():
                if "DefComponentInstance" in member[1]:
                    component = Parser.InstanceParser(member)
                    component.parse()
                    isLocal = component_to_local(component)

                    if type(isLocal) is dict:
                        localComponents.append(isLocal)

                if "DefTopology" in member[1]:
                    topology = Parser.TopologyParser(member)
                    topology.parse()

                    isInstance = topology_to_instance(topology)

                    if type(isInstance) is dict:
                        instanceTopologies.append(isInstance)

                    for member in topology.members():
                        print(member)
                        if "SpecConnectionGraph" in member[1]:
                            connectionGraph = Parser.ConnectionGraphParser(member)
                            connectionGraph.parse()

                            for connection in connectionGraph.cg_connections:
                                print(
                                    f"[INFO] Connection: {connection['source']['name']}{connection['source']['num']} -> {connection['dest']['name']}{connection['dest']['num']}"
                                )

    print(f"[INFO] Local components: {localComponents}")
    print(f"[INFO] Instance topologies: {instanceTopologies}")

    f.close()


def FppWriteTest():
    # create a new file called TEST.fpp
    f = open("TEST.fpp", "w")

    # write a module
    module = FppWriter.FppModule("TestModule")
    f.write(module.open() + "\n")

    component = FppWriter.FppInstance(
        "TestComponent",
        {
            "instanceOf": "TestInstance",
            "base_id": "0",
            "queueSize": "10",
            "stackSize": "10",
            "cpu": "0",
            "priority": "0",
            "phases": {
                "configObjects": None,
                "configComponents": None,
                "readParameters": None,
                "configConstants": None,
                "tearDownComponents": None,
                "startTasks": None,
                "stopTasks": None,
                "freeThreads": None,
            },
        },
    )

    f.write(component.write() + "\n")

    topology = FppWriter.FppTopology("TestTopology")
    f.write(topology.open() + "\n")

    instance = FppWriter.FppInstanceSpec("TestInstance")
    f.write(instance.write() + "\n")

    cg = FppWriter.FppConnectionGraph("TestConnectionGraph")
    f.write(cg.open() + "\n")

    f.write(
        cg.connect(
            {
                "source": {"name": "TestComponent.pout", "num": "0"},
                "dest": {"name": "TestComponent.pin", "num": "1"},
            }
        )
        + "\n"
    )

    f.write(cg.close() + "\n")

    f.write(topology.close() + "\n")

    f.write(module.close() + "\n")

    f.close()

    try:
        postFormat = fpp.fpp_format("TEST.fpp")

        # overwrite the file with the formatted version
        f = open("TEST.fpp", "w")
        f.write(postFormat)
        f.close()
    except:
        print("[ERR] fpp-format failed")
        sys.exit(1)


def main(args):
    parser = argparse.ArgumentParser(
        description="ac tool test for subtopologies",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command")

    # Subparser for the 'create' command
    st_subparser = subparsers.add_parser("subtopology", help="Subtopology ac")
    st_subparser.add_argument("--input", help="Input file", required=True, type=str)

    writer_subparser = subparsers.add_parser("write", help="Write ac")

    parsed, unknown = parser.parse_known_args(args)

    if len(unknown) > 0:
        print(f"[ERR] Unknown arguments: {unknown}")
        sys.exit(1)

    if parsed.command == "subtopology":
        subtopologyParse(parsed)

    if parsed.command == "write":
        FppWriteTest()


if __name__ == "__main__":
    main(sys.argv[1:])
