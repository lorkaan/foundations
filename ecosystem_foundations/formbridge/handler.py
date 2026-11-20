

from ..utils.objs.heap import MinHeap

from .config_graph import DirectedFormConfigGraph

from ..dynamicforms.form_graph import DirectedFormInstanceGraph

class InputConfigDataProcessor:

    @classmethod
    def handle_input(cls, config, dataDict):
        pass

class FormDataProcessor:

    _configGraph_cls = DirectedFormConfigGraph

    _priority_queue_cls = MinHeap

    @classmethod
    def process(cls, config, data):
        pass

    @classmethod
    def evaluate(cls, configGraph):
        if isinstance(configGraph, cls._configGraph_cls):
            depth_record = {}
            priorityQ = cls._priority_queue_cls()
            rootNodes = configGraph.getAllInitialNodes()
            for node in rootNodes:
                depth_record[node] = 0
                priorityQ.add(node, 0)
            while priorityQ.peek() != None:
                cur_depth, curVertexID = priorityQ.next()
                depth_record[curVertexID] = cur_depth
                config_node = configGraph.getDataForVertex(curVertexID)
                result = cls.process(config_node, {}) # Need to fix this so it actually has data

        else:
            raise TypeError(f"Expected a DirectedFormConfigGraph, instead got: {type(configGraph)}")
    

    @classmethod
    def processForm(cls, instance_id):
        instanceDataGraph = DirectedFormInstanceGraph.createFromFormInstance(instance_id)
        if isinstance(instanceDataGraph, DirectedFormInstanceGraph) and not instanceDataGraph.isEmpty():
            # Data is given in a Graph
            config_graph = DirectedFormConfigGraph.createFromFormInstance()
            # I need to do something with the instanceDataGraph
            cls.evaluate(config_graph)
        else:
            raise TypeError(f"No Instance Graph can be created for Form Instance ID: {instance_id}")