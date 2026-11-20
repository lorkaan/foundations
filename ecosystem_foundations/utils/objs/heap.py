import math

'''
Created to allow for Heap Specific exceptions to be handled.
(such as needing to stop the heapify recursions for going out heap indecies)

Found another method to do so, so this is depreciated, but left here
in case future use of HeapExceptions is required.
'''
class HeapException(Exception):

    @staticmethod
    def defaultMessage():
        return "Unknown Exception occured with Heap"

    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = HeapException.defaultMessage()

    def __str__(self):
        return f"HeapException: {self.message}"

'''
Represents a HeapNode. That is, a set of data with some weight or priority
associated with it.
'''
class HeapNode:

    '''
    Constructor method for a HeapNode
    '''
    def __init__(self, data, weight):
        self.data = data
        self.weight = weight

    '''
    Returns the data held by this heap node.
    This function exists so that it might be overridden
    in the future to perform some preprocessing of data before
    it is extracted.

    Currently, returns a Tuple representing (weight, data)
    '''
    def getData(self):
        return (self.weight, self.data)

    def __str__(self):
        return f"{self.weight}:{str(self.data)}"

    '''
    Comparison methods of a HeapNode
    '''

    def __lt__(self, other):
        return self.weight < other.weight

    def __le__(self, other):
        return self.weight <= other.weight

    def __gt__(self, other):
        return self.weight > other.weight

    def __ge__(self, other):
        return self.weight >= other.weight

    def __eq__(self, other):
        try:
            return self.weight == other.weight
        except:
            return False

'''
Base class for Heap Implemetation.

Should be overriden by a class that implements
the static method compareNodes
'''
class Heap:

    '''
    Method to override when determining how to
    sort the elements of the Heap.

    This method is considered abstract in this parent class, and thus
    just returns False.

    Returns True if elem1 should be given a higher priority, lower index, than
    elem2.
    '''
    @staticmethod
    def compareNodes(elem1, elem2):
        return False

    '''
    Calls the class's static method for comparing.
    '''
    @classmethod
    def compare(cls, elem1, elem2):
        return cls.compareNodes(elem1, elem2)

    '''
    Gets the Index of the Left Child.
    '''
    @staticmethod
    def getLeftChild(index):
        return index * 2

    '''
    Gets the Index of the Right Child.
    '''
    @staticmethod
    def getRightChild(index):
        return (index * 2) + 1

    '''
    Gets the Index of the Parent.
    '''
    @staticmethod
    def getParent(index):
        return math.floor(index / 2)

    '''
    Gets the Index of the Root.
    '''
    @staticmethod
    def getRootIndex():
        return 1

    '''
    Constructor method for a heap.
    '''
    def __init__(self):
        self.storage = [0]

    def peek(self):
        if len(self.storage) > self.__class__.getRootIndex():
            return self.storage[self.__class__.getRootIndex()]
        else:
            return None

    '''
    Gets the Size of the Heap.
    '''
    def size(self):
        return self.storage[0]

    '''
    Checks if the given index is in the Range of the Heap.
    '''
    def inRange(self, index):
        if index < Heap.getRootIndex() or index > self.size():
            return False
        else:
            return True

    '''
    Swaps the nodes at the given indecies, i and j. The swap only occurs
    if the node at index i should be given a higher priority than the node
    at index j.

    Returns True if the swap occurs, False if either of the indicies are
    out of range or the swap does not occur.
    '''
    def swap(self, i, j):
        if self.inRange(i) and self.inRange(j):
            if self.compare(self.storage[i], self.storage[j]):
                tmp = self.storage[i]
                self.storage[i] = self.storage[j]
                self.storage[j] = tmp
                return True
            else:
                return False
        else:
            return False

    '''
    Performs the Heapify functionality for retaining the heap property
    during an insertion, or add, function.
    '''
    def heapifyUp(self, index):
        parentIndex = Heap.getParent(index)
        if self.swap(index, parentIndex):
            return self.heapifyUp(parentIndex)
        else:
            return

    '''
    Performs the Heapify functionality for retaining the heap property
    during an deletion, or remove, function.
    '''
    def heapifyDown(self, index):
        leftChildIndex = Heap.getLeftChild(index)
        rightChildIndex = Heap.getRightChild(index)
        if self.inRange(leftChildIndex) and self.inRange(rightChildIndex):
            if self.compare(self.storage[leftChildIndex], self.storage[rightChildIndex]):
                # left child is the higher priority
                if self.swap(leftChildIndex, index):
                    return self.heapifyDown(leftChildIndex)
                else:
                    return
            else:
                # right child is the higher priority
                if self.swap(rightChildIndex, index):
                    return self.heapifyDown(rightChildIndex)
                else:
                    return
        else:
            return

    '''
    Performs an add operation on the Heap.
    '''
    def add(self, data, weight=0):
        self.storage.append(HeapNode(data, weight))
        self.storage[0] = self.storage[0] + 1
        self.heapifyUp(self.size())

    '''
    Extracts the next element of the Heap, ensuring the heap property is
    maintained.

    Note: Elements are returned in the following format
        (weight, data)

    Returns the next element in the Heap.
    '''
    def next(self):
        if self.size() <= 0:
            return (None, None)
        elif self.size() == 1:
            self.storage[0] = self.storage[0] - 1
            return self.storage.pop(Heap.getRootIndex()).getData()
        else:
            item = self.storage[Heap.getRootIndex()]
            self.storage[Heap.getRootIndex()] = self.storage.pop(self.size())
            self.storage[0] = self.storage[0] - 1
            self.heapifyDown(Heap.getRootIndex())
            return item.getData()

    def __str__(self):
        heapStr = ""
        for elem in self.storage:
            heapStr = heapStr + str(elem) + "\n"
        return heapStr

'''
Implementation of a Min Heap.
'''
class MinHeap(Heap):

    '''
    The method determinig how priority in the Heap is determined

    Specifically, higher priority is the lower.

    Returns True if elem1 has a higher prioirty than elem2.
    '''
    @staticmethod
    def compareNodes(elem1, elem2):
        return elem1 < elem2

'''
Implementation of a Max Heap
'''
class MaxHeap(Heap):

    '''
    The method determinig how priority in the Heap is determined

    Specifically, higher priority is the higher.

    Returns True if elem1 has a higher prioirty than elem2
    '''
    @staticmethod
    def compareNodes(elem1, elem2):
        return elem1 > elem2