
from ..utils.objs.heap import MinHeap

from ..utils.dict_utils import isDict

from .protocol import FieldConfigProtocol, HiddenNodeConfigProtocol, InputNodeConfigProtocol, NodeConfigProtocol, OutputNodeConfigProtocol, SourceProtocol, SourceType

from ..utils.type_utils import isList, isString

from .models import FormDataVertex

from .config_graph import DirectedFormConfigGraph

from ..dynamicforms.form_graph import DirectedFormInstanceGraph, FormGroupData

from ..utils.objs.graph import DataTraverseNode, EdgeDataWithDependencyDirectedGraph
import uuid
import logging


class DataToNodeResolver:

    logger = logging.getLogger(__name__)

    @classmethod
    def resolveDataToInputNode(cls, config_node, data_node):
        if not isinstance(data_node, FormGroupData):
            raise TypeError(f"Expected to get a FormGroupData for data_node, but instead got: {type(data_node)}")
        if not isinstance(config_node, InputNodeConfigProtocol):
            raise TypeError(f"Can not resolve data to a non-input protocol object: {type(config_node)}")
        data_node_ans_dict = data_node.generateAnswerDict() # Generate the Data Dictionary to be queryable by question_code for the resolver
        if isDict(data_node_ans_dict):
            input_field_dict = config_node.getInputFields()
            if isDict(input_field_dict):
                resolved_field_dict = {}
                error_dict = {}
                for k, v in input_field_dict.items():
                    if not isString(k):
                        error_dict[k] = f"Key: {k} is not considered a string for value: {v}"
                        cls.logger.error(error_dict[k])
                        continue
                    if not isinstance(v, FieldConfigProtocol):
                        error_dict[k] = f"Key: {k} is does not have a FieldConfigProtocol for a value: {type(v)} --> {v}"
                        cls.logger.error(error_dict[k])
                        continue
                    cur_source = v.getSource()
                    if isinstance(cur_source, SourceProtocol) and SourceProtocol.isValid(cur_source):
                        if cur_source.src_type == SourceType.ANSWER:
                            # Answer from Data
                            resolved_field_dict[k] = data_node_ans_dict.get(cur_source.question_code, None)
                        elif cur_source.src_type == SourceType.LITERAL:
                            resolved_field_dict[k] = cur_source.value
                        else:
                            # This is not something that can be resolved to an actual value at present, so do nothing so the update doesnt change it
                            continue
                    else:
                        error_dict[k] = f"Key: {k} did not produce a valid SourceProtocol: {type(cur_source)} --> {cur_source}"
                        cls.logger.error(error_dict[k])
                        continue
                return resolved_field_dict, error_dict
            else:
                raise TypeError(f"No Input Fields to get from this Node: {config_node}")
        else:
            raise TypeError(f"No Data to be obtained from this data_node: {data_node}")

class NodeExecutionHandler:

    _context_incoming_data_key = "input_data"

    @classmethod
    def handleInputNodeConfig(cls, node, **context):
        if not isinstance(node, InputNodeConfigProtocol):
            raise TypeError(f'Tried to handle InputNode, but got: {node}')
        input_data = context.get("input_data", None)

    @classmethod
    def handleOutputNodeConfig(cls, node, **context):
        if not isinstance(node, OutputNodeConfigProtocol):
            raise TypeError(f'Tried to handle OutputNode, but got: {node}')
        input_data = context.get("input_data", None)

    @classmethod
    def handleHiddenNodeConfig(cls, node, **context):
        if not isinstance(node, HiddenNodeConfigProtocol):
            raise TypeError(f'Tried to handle HiddenNode, but got: {node}')
        input_data = context.get("input_data", None)

    _node_classes = {
        InputNodeConfigProtocol : {
            "func": handleInputNodeConfig,
            "context_keys": ["input_data"]
        },
        OutputNodeConfigProtocol: {
            "func": handleOutputNodeConfig,
            "context_keys": ["input_data"]
        },
        HiddenNodeConfigProtocol: {
            "func": handleHiddenNodeConfig,
            "context_keys": ["input_data"]
        }
    }
        

    @classmethod
    def execute(cls, node, **context):
        if isinstance(node, NodeConfigProtocol):
            node_handler = cls._node_classes.get(node.__class__, None)
            if isDict(node_handler, keys=["func", "context_key"]):
                node_handler_execute_func = node_handler.get("func", None)
                if callable(node_handler_execute_func):
                    new_context = {}
                    context_keys = node_handler.get("context_keys", [])
                    for c in context_keys:
                        new_context[c] = context.get(c, None)
                    return node_handler_execute_func(node, **new_context)
                else:
                    raise ValueError(f"Node: {node} does not have a handler defined")
            else:
                raise ValueError(f"Node: {node} does not have an execute config defined")
        else:
            raise TypeError(f"Expected object of NodeConfigProtocol type, instead got: {node}")

class PathEncapsulation:
    """
        This is a storage system for Handling Path Encapsulation. Once the data paths are initially created via Input Nodes, 
        you can create new Data spreading out in a scoped manner. This will allow for D on Path [A, B, D], created on input nodes,
        to recognize Computations Nodes that spread out from A and B. 

        Currently lacks boundry checking. It does not check automatically check if a Node from A and C is within the current path of [A, B, D]
    """

    def __init__(self):
        self.config_space = {}  # Only 1 config per data encapsulation: Keyed by Execution Vertex ID and then is a dictionary of ConfigID: VertexID
        self.descendents = {}   # List of ExecutionVertexIDs that can be used to update, Keyed by ExecutionVertexID
        self.ancestors = {}     # List of ExecutionVertexIDs that can be used to traverse, Keyed by ExecutionVertexID

    def addConfigToSpace(self, execution_id, config_id, parent_id=None):
        curSpace = self.config_space.get(execution_id, {})
        isNewEntry = parent_id != None and not isDict(curSpace)
        if isNewEntry:
            if not isDict(curSpace, nonEmpty=False):
                curSpace = {}
            curSpace.update(self.config_space.get(parent_id, {}))
        curSpace.update({config_id: execution_id})
        self.config_space[execution_id] = curSpace
        if isNewEntry:
            a_list = self.ancestors.get(parent_id, [])
            new_ancestor_list = []
            if isList(a_list):
                new_ancestor_list.extend(a_list)
            new_ancestor_list.append(parent_id)
            self.ancestors[execution_id] = new_ancestor_list
            for a in new_ancestor_list:
                past_d_list = self.descendents.get(a, [])
                past_d_list.append(execution_id)
                self.descendents[a] = past_d_list
        else:
            d_list = self.descendents.get(execution_id, [])
            for d in d_list:
                curSpace = self.config_space.get(d, {})
                curSpace.update({config_id: execution_id})
                self.config_space[d] = curSpace

    def getAncestors(self, execution_id):
        return self.ancestors.get(execution_id, [])

    def getDescendents(self, execution_id):
        return self.descendents.get(execution_id, [])

    def getConfigSpace(self, execution_id):
        return self.config_space.get(execution_id, {})

class NodeDiscovery:

    def __init__(self, src_id, dst_config_id):
        self.src_id = src_id
        self.dst_config_id = dst_config_id

class ExecutionGraph(EdgeDataWithDependencyDirectedGraph):
    """
        This keeps the Edge Data, but also includes dependency edges, which also have data.

        Refactor this to remove the Large Functions ---> Specifically, the large __init__() function body
    """

    logger = logging.getLogger(__name__)

    MAX_ID_RETRY = 5

    def __init__(self, formInstanceGraph, configGraph):
        if not isinstance(formInstanceGraph, DirectedFormInstanceGraph):
            raise TypeError(f"Expected to have a DirectedFormInstanceGraph for formInstanceGraph, instead got: {type(formInstanceGraph)}")
        if not isinstance(configGraph, DirectedFormConfigGraph):
            raise TypeError(f"Expected to get a DirectedFormConfigGraph for configGraph, but instead got: {type(configGraph)}")
        super().__init__()
        self.parentEdge = {}
        self.childEdge = {}
        self.paths = PathEncapsulation() # Represent the config_id, execution_id parents that are on the data path connected to a given Node.
        
        # This needs to change to represent the traversal though the parent/child relationship.
        self.input_nodes = set()    # This represents all nodes that encapsulated by any path

        self.priorityQ = MinHeap()  # This is supposed to be a data structure that I can push elements to, and consume elements for to complete the graph from given input nodes

        data_to_input_map = {}
        map_instance_to_config = {}

        data_node_list = formInstanceGraph.traverseGraphFromRoot() # This produces objects of type: DataTraverseNode
        if isList(data_node_list):
            for data_node in data_node_list:
                if isinstance(data_node, DataTraverseNode) and isinstance(data_node.data, FormGroupData):
                    config_node_ids = self.__class__.getConfigNodeIdList(data_node.data.code)
                    if isList(config_node_ids):
                        for config_node_id in config_node_ids:
                            # Track which Node belongs to who
                            self.addToInputExecutionGraph(configGraph, config_node_id, data_node, data_to_input_map, map_instance_to_config)
                    else:
                        continue    # There is no corresponding configuration
                else:
                    continue    # No Data to be found here.

        # Initialize the PriorityQ to do the Node discovery from the Input Nodes build above from the FormGroupInstance Data Graph
        for execution_id, config_id in map_instance_to_config.items(): # Change this to mutable structure that can go until empty
            edges = configGraph.getEdges(config_id)
            if not isList(edges):    # No Edges on this Node
                continue
            for dst in edges:
                self.priorityQ.add(NodeDiscovery(execution_id, dst), 0)
            self.input_nodes.add(execution_id)  # Add the Input Node to list of input nodes

        # Do Not Forget. Dependency Edges are not processed as yet.
        dependency_map = {}

        # Build the Graph via the Config Graph Edges from the various Input Nodes
        while self.priorityQ.peek() != None:    # This is looping through seen nodes to find edges, but should store unseen/unprocessed nodes?
            discovery_data, depth = self.priorityQ.next()
            if not isinstance(discovery_data, NodeDiscovery):
                continue
            pathCheck = self.paths.getConfigSpace(discovery_data.src_id) 
            backedges = configGraph.getBackEdges(discovery_data.dst_config_id)
            processed_backedges = set() # This is a set of nodes that have been processed that the dst node on this edge has a backedge for
            data_input_created_flag = True
            for be in backedges:    # This is a list of CONFIG BackedEdges
                backedge_execute_id = pathCheck.get(be, None)
                if backedge_execute_id == None:
                    # There is a backedge that has not been processed yet.
                    self.priorityQ.add(discovery_data, depth+1)
                    data_input_created_flag = False
                    break
                    # This backedge is in this data path
                else:
                    processed_backedges.add(backedge_execute_id, be) # (Backedge -> (k, be), thus edge is (be, k) )
            if data_input_created_flag:
                connected_node = configGraph.getDataForVertex(discovery_data.dst_config_id)    # Get the node info from Config graph for this specific data
                if connected_node == None:  # There was an edge specified, but there is no corresponding vertex
                    raise ValueError(f"No node found in the Config graph for edge: {config_id}, {k} that has value: {v}")
                try:
                    new_node_id = self.generateExecutionNodeID()
                except Exception as e:
                    self.__class__.logger.error(e)
                    raise e
                self.addDataVertex(new_node_id, {
                    "config_id": discovery_data.dst_config_id,
                    "data": connected_node
                })
                for execute_backedge_dst, config_backedge_id in processed_backedges:
                    self.addEdgeData(execute_backedge_dst, new_node_id, configGraph.getEdgeDataForVertex(config_backedge_id, discovery_data.dst_config_id))
                self.paths.addConfigToSpace(new_node_id, discovery_data.dst_config_id, discovery_data.src_id)  
                nextEdges = configGraph.getEdges(discovery_data.dst_config_id)
                if not isList(nextEdges):    # No Edges on this Node
                    continue
                for dst in nextEdges:
                    self.priorityQ.add(NodeDiscovery(new_node_id, dst), depth+1)
                cur_dep_data = configGraph.getDependencyData(discovery_data.dst_config_id)
                if not isDict(cur_dep_data):
                    continue
                else:
                    dependency_map[new_node_id] = cur_dep_data
        for exe_id, dep_config in dependency_map.items():
            if not isDict(dep_config):
                continue
            node_data_encapsulation = self.paths.getConfigSpace(exe_id)
            if not isDict(node_data_encapsulation):
                self.__class__.logger.error(f"Could not find an Encapsulation for: {exe_id}")
                continue
            for config_dep_id, dep_name in dep_config.items():
                prerequisite_exe_id = node_data_encapsulation.get(config_dep_id, None)
                if prerequisite_exe_id == None:
                    self.__class__.logger.error(f"Can not find data in the node encapsulation for: {config_dep_id}")
                    continue
                else:
                    self.addDependencyData(exe_id, prerequisite_exe_id, dep_name)


    def execute(self, node_executor):
        """
            Note: This does not handle Dependency Edges as yet as they are not built into the system.

            This function currently does not return anything as this system is designed to specifically alter databases
            but it might be an idea to actually return a value that can be checked at least.
        """
        if not isinstance(node_executor, NodeExecutionHandler) and not issubclass(node_executor, NodeExecutionHandler):
            raise TypeError(f"Expected a NodeExecutionhandler object or subclass, instead got: {node_executor} --> {type(node_executor)}")
        if self.priorityQ.peek() != None:
            # The PriorityQueue is not empty
            raise ValueError(f"PriorityQueue has not been emptied. Please flush. Peek: {self.priorityQ.peek()}")
        else:
            # Start the evaluation at the input nodes and traverse similar to the Build Traversal
            for node_id in self.input_nodes:
                self.priorityQ.add(node_id, 0)  # Initialize the Priority Queue
            processed_nodes = set()
            seen_nodes = set()

            output_values = {}  # Stores the Output Values keyed by node_id. 

            while self.priorityQ.peek() != None:
                cur_node_id, depth = self.priorityQ.next()
                if cur_node_id in processed_nodes:
                    continue
                else:
                    if not cur_node_id in seen_nodes:
                        seen_nodes.add(cur_node_id)
                    incoming_edge_data = self.getEdgeDataFromBackEdge(cur_node_id)
                    dependency_edge_data = self.getDependencyData(cur_node_id)
                    incoming_data = {}
                    all_incoming_nodes_processed = True
                    if isDict(incoming_edge_data):
                        for k, v in incoming_edge_data.items():
                            if k in processed_nodes:
                                if isString(v):
                                    incoming_data[v] = output_values.get(k, None)
                                else:
                                    self.__class__.logger.error(f"Expected Edge Data to be a non-empty string, but instead got: {type(v)} --> {v}")
                                    continue
                            else:
                                # The nodes that are dependent are not processed yet.
                                all_incoming_nodes_processed = False
                                break
                    if isDict(dependency_edge_data):
                        for k, v in dependency_edge_data.items():
                            if k in processed_nodes:
                                if isString(v):
                                    incoming_data[v] = output_values.get(k, None)
                                else:
                                    self.__class__.logger.error(f"Expected Edge Dependency to be a non-empty string, but instead got: {type(v)} --> {v}")
                                    continue
                            else:
                                # The nodes that are dependent are not processed yet.
                                all_incoming_nodes_processed = False
                                break
                    if not all_incoming_nodes_processed:
                        self.priorityQ.add(node_id, depth+1)
                    else:
                        # All Incoming Node are processed
                        cur_node = self.getDataForVertex(cur_node_id)

                        # Build Context
                        cur_context = {}
                        cur_context[node_executor.__class__._context_incoming_data_key] = incoming_data

                        # Actually Execute
                        cur_node_output = node_executor.execute(cur_node, **cur_context)
                        output_values[cur_node_id] = cur_node_output
                        processed_nodes.add(cur_node_id)

                        # Add the Edges from this Node into the Priority Queue at a higher depth. 
                        nextEdges = self.getEdges(cur_node_id)
                        if isList(nextEdges):
                            for ne in nextEdges:
                                if ne in seen_nodes or ne in processed_nodes:   # Do not add if already seen (in queue already) or processed (was in queue and now removed) 
                                    continue
                                else:
                                    self.priorityQ.add(ne, depth+1)
                

    # --- Parent / Child Relationships ---#

    # This is used to keep the structure for Parent and Child in the Input nodes so those variables can be evaluated at execution      
    def addParentChildEdge(self, parent_id, child_id):
        if not parent_id in self.vertex:
            self.addVertex(parent_id)
        if not child_id in self.vertex:
            self.addVertex(child_id)
        children = self.parentEdge.get(parent_id, [])
        if not isList(children, 0):
            children = []
        children.append(child_id)
        self.parentEdge[parent_id] = children
        parents = self.childEdge.get(child_id, [])
        if not isList(parents, 0):
            parents = []
        parents.append(parent_id)
        self.childEdge[child_id] = parents

    def getParents(self, child_id):
        if not child_id in self.vertex:
            raise ValueError(f"Given Child ID is not a Vertex: {child_id}: {type(child_id)}")
        return self.parentEdge.get(child_id, [])

    def getChildren(self, parent_id):
        if not parent_id in self.vertex:
            raise ValueError(f"Given Parent ID is not a Vertex: {parent_id}: {type(parent_id)}")
        return self.childEdge.get(parent_id, [])

    # --- Creating the Node IDs for this Graph that are Unique as there could be multiple Input Nodes with the same Config, and thus multiple data paths --- #

    def generateExecutionNodeID(self):
        random_id = uuid.uuid4()
        if isinstance(self.vertex, set):
            # Do checking
            if random_id in self.vertex:
                for i in range(self.__class__.MAX_ID_RETRY):
                    random_id = uuid.uuid4()
                    if not random_id in self.vertex:
                        return random_id
                    else:
                        continue
                raise ValueError(f"Can not generate a Unique UUID within: {i} Retries")
            else:
                return random_id
        else:
            return random_id

    @classmethod
    def getConfigNodeIdList(cls, formGroupCode):
        """
            This will get the Node IDs, which are vertex in the Config Graph, for any given FormGroup ID
        """
        return FormDataVertex.objects.filter(form_group__code=formGroupCode).value_list("id", flat=True)

    # --- Helper Function for creating an Input Execution Graph Node used to initialize the Vertex Traversal Buildout ---#

    def addToInputExecutionGraph(self, config_graph, config_node_id, data_node, data_to_input_map, map_instance_to_config):
        """
            Adds the Execution graph based on the config graph, and the data at the specific node

            @param execution_graph {ExecutionGraph} The Graph to add to.
            @param config_graph {DirectedFormConfigGraph}    The Graph that holds all the configurations. Passed so edge relationships can be found
            @param config_node_id {uuid}   The ID of the specific Configuration Node that links to this Data
            @Pparam data_node {FormGroupData} The specific data context that can be resolved into this configuration node.
        """
        if not isDict(data_to_input_map, nonEmpty=True):
            raise TypeError(f"Expected a Dictionary, possibly empty, for the data_to_input_map: got {type(data_to_input_map)}")
        if not isDict(map_instance_to_config, nonEmpty=True):
                    raise TypeError(f"Expected a Dictionary, possibly empty, for the data_to_input_map: got {type(map_instance_to_config)}")
        if not isinstance(config_graph, DirectedFormConfigGraph):
            raise TypeError(f"Expected to get a DirectedFormConfigGraph for config_graph, but instead got: {type(config_graph)}")
        if not isinstance(data_node, DataTraverseNode) or not isinstance(data_node.data, FormGroupData):
            raise TypeError(f"Expected to get a DataTraverseNode with FormGroupData for data_node, but instead got: {type(data_node)} --> {getattr(data_node, "code", None)}")
        
        config_node = config_graph.getDataForVertex(config_node_id)
        if not isinstance(config_node, InputNodeConfigProtocol):
            raise TypeError(f"Config Node for {config_node_id} could not be found in the correct InputNodeConfigProtocol formart:  {config_node} --> {type(config_node)}")
        resolved_data, errors = DataToNodeResolver.resolveDataToInputNode(config_node, data_node.data)
        if isDict(errors):
            raise ValueError(f"There were errors found processing {config_node_id}\n{[f"\t{k}: {v}\n" for k, v in errors.items()]}")
        resolved_mappings = config_node.getInputFields().update(resolved_data)
        resolved_input = config_node.getInputFields().update(resolved_mappings)
        execution_data = {
            "input": resolved_input,
            "operations": config_node.getOperations(),
            "output": config_node.getOutput()
        }
        # Produce new Unique Vertex ID, needs to be done this way sine 1 config can be used by multiple data nodes, and not every data node has a config node equivalent
        try:
            new_node_id = self.generateExecutionNodeID()
        except Exception as e:
            self.__class__.logger.error(e)
            raise e
        self.addDataVertex(new_node_id, {   # Build the prototype execution data node here, formalize later
            "config_id": config_node_id,
            "data": execution_data
        })
        data_to_input_map[data_node.data.id] = new_node_id
        map_instance_to_config[new_node_id] = config_node_id
        if isList(data_node.path, 2):   # Only need to create edge if path is 2 or greater in length
            newParentID = data_to_input_map.get(data_node.path[-2], None)  # Get not this node, but the node that came before this one.
            if newParentID == None:
                raise ValueError(f"Can not find parent ID for path: {data_node.path}\nGiven the following data_to_input mapping: {[f"\n\t{k}: {v}" for k, v in self.data_to_input_map.items()]}")
            self.addParentChildEdge(newParentID, new_node_id)   # This creates the parent - child edges for the input so that it can be traversed
            self.paths.addConfigToSpace(new_node_id, config_node_id, newParentID)
        else:
            # Base Case for Setting New Execution Code Paths
            self.paths.addConfigToSpace(new_node_id, config_node_id)
        