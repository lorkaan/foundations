import logging

from .protocol import ConfigProtocol, HiddenNodeConfigProtocol, InputNodeConfigProtocol, InputOutputConfigProtocol, OutputNodeConfigProtocol

from ..utils.dict_utils import isDict
from ..utils.type_utils import findBadIndexes, isList, isString, isUUID

from .models import FormGroupModelDataBridge, FormTypeDataEnvironment

from ..dynamicforms.models import FormGroup, FormInstance, FormType

from ..utils.objs.graph import EdgeDataWithDependencyDirectedGraph
import logging

class DirectedFormConfigGraph(EdgeDataWithDependencyDirectedGraph):
    """
        This graph represents the foreign key edges for each model configuration
    """

    def __init__(self):
        super().__init__()

    @classmethod
    def createFromFormType(cls, form_type):
        if isinstance(form_type, FormType):
            qs = form_type.processors.all()
        elif isUUID(form_type):
            qs = FormTypeDataEnvironment.objects.filter(form_type_id=form_type)
        else:
            raise TypeError(f"Expected a FormType instance, or the UUID representing the ID of one. Instead got: {type(form_type)} --> {form_type}")
        if qs.exists():
            graph = cls()
            # fill graph
            curEdgeList = []
            curDependencyList = []
            for env in qs:
                nodes = env.nodes.all()
                if nodes.exists():
                    for node in nodes:
                        if node.is_input and node.is_output:
                            nodeConfig = InputOutputConfigProtocol(**node.config) # Set the Node Config
                            graph.inputNodes.add(node.id)
                            graph.outputNodes.add(node.id)        
                        elif node.is_input:
                            nodeConfig = InputNodeConfigProtocol(**node.config) # Set the Node Config
                            graph.inputNodes.add(node.id)
                        elif node.is_output:
                            nodeConfig = OutputNodeConfigProtocol(**node.config) # Set the Node Config
                            graph.outputNodes.add(node.id)
                        else:
                            # Node is a Hidden or Operations Node
                            nodeConfig = HiddenNodeConfigProtocol(**node.config) # Set the Node Config
                        graph.addDataVertex(node.id, nodeConfig)
                        out_edges = node.outgoing_edges.all()
                        if out_edges.exists():
                            for out_e in out_edges:
                                curEdgeList.append(out_e)
                        deps = node.dependencies.all()
                        if deps.exists():
                            for dep in deps:
                                curDependencyList.append(dep)
                else:
                    continue
            for edge in curEdgeList:
                graph.addEdgeData(edge.src_id, edge.dst_id, edge.name)
            for dep in curDependencyList:
                graph.addDependencyData(dep.dependent_id, dep.prerequisite_id, dep.name)
            return graph
        else:
            return None # There is nothing to do

    @classmethod
    def createFromFormInstance(cls, instance_id):
        form_type = FormInstance.objects.get(
            id=instance_id
        ).form_type
        return cls.createFromFormType(form_type)
