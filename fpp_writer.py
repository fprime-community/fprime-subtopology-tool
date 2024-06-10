class FppModule:
    module_name = ""
    
    def __init__(self, module_name):
        self.module_name = module_name
        
    def open(self):
        return f"module {self.module_name} {{"
        
    def close(self):
        return "}"
        
class FppTopology:
    topology_name = ""
    module_name = ""
    
    def __init__(self, topology_name):
        self.topology_name = topology_name
        
    def open(self):
        return f"topology {self.topology_name} {{"
        
    def close(self):
        return "}"
        
class FppInstanceSpec:
    instance_name = ""
    
    def __init__(self, instance_name):
        self.instance_name = instance_name
        
    def write(self):
        return f"instance {self.instance_name}"
    
class FppConnectionGraph:
    connection_graph_name = ""
    
    def __init__(self, connection_graph_name):
        self.connection_graph_name = connection_graph_name
        
    def open(self):
        return f"connections {self.connection_graph_name} {{"
    
    def connect(self, connection):
        return f"    {connection['source']['name']}{connection['source']['num']} -> {connection['dest']['name']}{connection['dest']['num']}"
        
    def close(self):
        return "}"
    
class FppImport:
    import_name = ""
    
    def __init__(self, import_name):
        self.import_name = import_name
        
    def write(self):
        return f"import {self.import_name}"
        
class FppInstance:
    instance_name = ""
    instance_details = {
        "instaceOf": "",
        "base_id": "",
        "queueSize": "",
        "stackSize": "",
        "cpu": "",
        "priority": "",
        "phases": {
            "configObjects": None,
            "configComponents": None,
            "readParameters": None,
            "configConstants": None,
            "tearDownComponents": None,
            "startTasks": None,
            "stopTasks": None,
            "freeThreads": None,
        }
    }
    
    def __init__(self, instance_name, instance_details):
        self.instance_name = instance_name
        self.instance_details = instance_details
        
    def writePhases(self):
        phaseOpen = False
        part = ""
        
        for phase in self.instance_details['phases']:
            if self.instance_details['phases'][phase] is not None and self.instance_details['phases'][phase] != "":
                if not phaseOpen:
                    part += f"{{"
                    phaseOpen = True
                
                part += f'\n    phase Fpp.ToCpp.Phases.{phase} """\n'
                part += self.instance_details['phases'][phase]
                part += '"""'
        
        if phaseOpen:
            part += "}"
            
        return part
        
    def write(self):
        part = f"instance {self.instance_name}: {self.instance_details['instanceOf']} base id {self.instance_details['base_id']}"
        
        if self.instance_details['queueSize'] and self.instance_details['queueSize'] != "":
            part += f"\\ \n    queue size {self.instance_details['queueSize']}"
            
        if self.instance_details['stackSize'] and self.instance_details['stackSize'] != "":
            part += f"\\ \n    stack size {self.instance_details['stackSize']}"
            
        # if self.instance_details['cpu'] and self.instance_details['cpu'] != "":
        #     part += f"\\ \n    cpu {self.instance_details['cpu']}"
            
        if self.instance_details['priority'] and self.instance_details['priority'] != "":
            part += f"\\ \n    priority {self.instance_details['priority']}"
            
        return part + self.writePhases()