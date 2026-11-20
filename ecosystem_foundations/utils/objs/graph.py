
from ..dict_utils import isDict

from ..type_utils import isList


class DirectedGraph:

    def __init__(self):
        self.vertex = set()
        self.edges = {}
        self.back_edges = {}

    def addVertex(self, vertex):
        if not vertex in self.vertex:
            self.vertex.add(vertex)
            self.edges[vertex] = []
            self.back_edges[vertex] = []

    def addEdge(self, src, dst):
        if not src in self.vertex:
            self.addVertex(src)
        if not dst in self.vertex:
            self.addVertex(dst)
        src_edges = self.edges.get(src, [])
        if not isList(src_edges, 0):
            src_edges = []
        src_edges.append(dst)
        self.edges[src] = src_edges
        dst_back_edges = self.back_edges.get(dst, [])
        if not isList(dst_back_edges, 0):
            dst_back_edges = []
        dst_back_edges.append(src)
        self.back_edges[dst] = dst_back_edges

    def getEdges(self, src):
        if src in self.vertex:
            connected_vertex = self.edges.get(src, [])
            return connected_vertex
        else:
            raise KeyError(f"Vertex could not be found: {src}") 

    def getBackEdges(self, src):
        if src in self.vertex:
            connected_vertex = self.back_edges.get(src, [])
            return connected_vertex
        else:
            raise KeyError(f"Vertex could not be found: {src}") 

    def isEmpty(self):
        return len(self.vertex) <= 0

    """
        Gets a list of Root Vertices. A Root Vertex is a Vertex with no Back Edges
    """
    def getRootVertexList(self):
        roots = []
        for v in self.vertex:
            if not isList(self.back_edges.get(v, [])):
                roots.append(v)
            else:
                continue
        return roots

class DataNode:

    def __init__(self, data):
        self.data = data

class DataTraverseNode(DataNode):

    def __init__(self, data, path=[]):
        super.__init__(data)
        self.path = path

class DataDirectedGraph(DirectedGraph):

    def __init__(self):
        super.__init__()
        self.data = {}

    def addDataVertex(self, vertex, data):
        self.addVertex(vertex)
        if data != None:
            self.data[vertex] = data

    def getDataForVertex(self, vertex):
        if vertex in self.vertex:
            return self.data.get(vertex, None)
        else:
            return None

    """
        Depth First Traversal to find all the Data 
    """
    def traverse(self, root, cur_path=[]):
        new_path = []
        if isList(cur_path):
            new_path.extend(cur_path)
        new_path.append(root)
        nodes = []
        nodes.append(DataTraverseNode(self.data.get(root, None), new_path))
        cur_edges = self.edges.get(root, [])
        if isList(cur_edges):
            for dst in cur_edges:
                child_nodes = self.traverse(dst, new_path)
                if isList(child_nodes):
                    nodes.extend(child_nodes)
                else:
                    continue
        return nodes

    """
        Does a Depth First Traverse of every Root Vertex in the graph.
    """
    def traverseGraphFromRoot(self):
        roots = self.getRootVertexList()
        full_list = []
        if isList(roots):
            for r in roots:
                cur = self.traverse(r)
                if isList(cur):
                    full_list.extend(cur)
                else:
                    continue
        return full_list

class EdgeDataNode(DataNode):

    def __init__(self, data, edge_data_dict):
        super.__init__(data)
        if isDict(edge_data_dict):
            self.edgeData = edge_data_dict
        else:
            return {}

class EdgeDataDirectedGraph(DataDirectedGraph):
    """
        This class has Data held at the Vertex AND in the Edges
    """

    def __init__(self):
        super.__init__()
        self.edgeData = {}

    def addEdgeData(self, src, dst, data):
        self.addEdge(src, dst)
        curEdgeData = self.edgeData.get(src, {})
        curEdgeData[dst] = data
        self.edgeData[src] = curEdgeData

    def getEdgeDataForVertex(self, src, dst=None):
        if src in self.vertex:
            data = self.edgeData.get(src, {})
            if dst == None:
                return data
            else:
                return data.get(dst, None)
        else:
            raise KeyError(f"Vertex could not be found: {src}")

    def getEdgeDataFromBackEdge(self, dst):
        backedges = self.getBackEdges(dst)
        data_dict = {}
        for b in backedges:
            data_dict[b] = self.getEdgeDataForVertex(b, dst)
        return data_dict

class EdgeDataWithDependencyDirectedGraph(EdgeDataDirectedGraph):
    """
        This graph represents the foreign key edges for each model configuration
    """

    def __init__(self):
        super().__init__()
        self.inputNodes = set()
        self.outputNodes = set()
        self.dependencies = {}
        self.back_dependencies = {}
        self.dependency_data = {}

    def addDependency(self, dependent, prerequisite):
        if not dependent in self.vertex:
            self.addVertex(dependent)
        if not prerequisite in self.vertex:
            self.addVertex(prerequisite)
        src_dependencies = self.dependencies.get(dependent, [])
        if not isList(src_dependencies, 0):
            src_dependencies = []
        src_dependencies.append(prerequisite)
        self.dependencies[dependent] = src_dependencies
        dst_back_dependencies = self.back_dependencies.get(prerequisite, [])
        if not isList(dst_back_dependencies, 0):
            dst_back_dependencies = []
        dst_back_dependencies.append(dependent)
        self.back_dependencies[prerequisite] = dst_back_dependencies

    def addDependencyData(self, dependent, prerequisite, data):
        self.addDependency(dependent, prerequisite)
        curDepData = self.dependency_data.get(dependent, {})
        curDepData[prerequisite] = data
        self.dependency_data[dependent] = curDepData

    def getDependencyData(self, dependent, prerequisite=None):
        if dependent in self.vertex:
            data = self.edgeData.get(dependent, {})
            if prerequisite == None:
                return data
            else:
                return data.get(prerequisite, None)
        else:
            raise KeyError(f"Vertex could not be found: {src}")

    def getAllInitialNodes(self):
        """
            This gets all the Initial Nodes, that is Input Nodes with a Depth of 0 (or no incoming edges)

            Incoming Edge: 
                - Data Edge => self.back_edge
                - Dependency Edge => self.dependencies
        """
        inputList = list(self.inputNodes)
        rootList = []
        for elem in inputList:
            if not isList(self.back_edges.get(elem, None)) and not isList(self.dependencies.get(elem, None)):
                rootList.append(elem)
            else:
                continue
        return rootList