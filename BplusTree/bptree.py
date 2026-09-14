import sys
import struct

class node:
    def __init__(self, m :int = 1, p : list = None, r : int = None, isLeaf = True, parent : int = None, offset : int = None):
        self.m = m  # # of keys
        self.p = p  # array of [key, left chile node] or [key, value]
        self.r = r  # a pointer to the rightmost child node or right sibling node
        self.isLeaf = isLeaf
        self.parent = parent # pointer for parent. if root: None
        self.offset = offset # self pointer
        

def readNode(offset) -> node:
    with open(ifile, 'rb') as f:
        f.seek(rootOffset + offset)
        data = f.read(NODE_SIZE)
        #data read error
        if len(data) != NODE_SIZE:
            raise ValueError("Invalid node size while reading")
        m, isLeaf, parent, r, myOffset, *p = struct.unpack(NODE_FORMAT, data)
        p = list(zip(p[::2], p[1::2])) # make pair

        return node(m, p, r, isLeaf, parent, myOffset)

def genOffset() -> int :...

def keyFind(n :node, key) -> node: # find the locate of key and return that node recursively
    if n.isLeaf:
        return n        # case1 : if n is leaf return the node
    for i in n.p:
        treeKey = i[0]
        if key < treeKey: # case2 : if key < tree's key : go left child
            keyFind(readNode(i[1]), key)
        elif key >= treeKey: # case3 : else go right child
            keyFind(n.r, key)

def split(n :node):   # when node overflowed, split node and make parent node, keep left node and create right node.
    mid = n.m//2
    rightNode = node(isLeaf=n.isLeaf, parent=n.parent, r = n.r, offset=genOffset())
    rightNode.p = n.p[mid:]
    rightNode.m = len(rightNode.p)

    n.p = n.p[:mid]
    n.m = len(n.p)
    n.r = rightNode
    #node split

    newKey = rightNode.p[0]

    if n.parent == None: # n is root, create new root node
        parent = node(1, [newKey, n.offset], rightNode.offset, False, None, genOffset())
    else:
        parent = readNode(n.parent)
        for i in range(len(parent.p)):
            if (i == len(parent.p) - 1) and (newKey > parent.p[i][0]): 
                 # key should be inserted to last key
                 # change r either
                parent.p.append([newKey, n.offset])
                parent.r = rightNode.offset
                break
            if newKey < parent.p[i][0]:
                parent.p.insert(i, [newKey, n.offset])
                parent.p[i+1][1] = rightNode.offset
                break
        if len(parent.p) > N - 1:
            split(parent)

    modified.append(n, rightNode, parent)
    return
    

# bptree function
def create(N):
    with open(ifile, 'wb') as f:
        f.write(bytes([N]))
    
def insert(key, value):
    with open(ifile, 'r+b') as f:
        if rootOffset == b'':           #root doesnt exist, tree empty
            modified.append(node(m = 1, p = [key,value], r = None))
            return
        else:
            root = readNode(rootOffset)
            targetNode = keyFind(root, key)
            for i in range(targetNode.m - 1):
                if targetNode.p[i][0] == key:
                    print(f"duplicated key. key : {key}, value : {value}")
                    return
                if targetNode.p[i][0] < key:
                    continue
                else:
                    split(targetNode)
            


def delete(key):...
def search(key):
    root = readNode(ifile, rootOffset)
    
def search(start, end):...




#main
cmd = sys.argv
if len(cmd) < 3 or len(cmd) > 5:
    exit(1)

if(cmd[1]) == '-c':
    create(*cmd[2:])
ifile = cmd[2]
with open(ifile, 'r') as f:
    #file meta data
    newOffset     : int = struct.unpack('<Q', f.read(8))[0]  # 8 byte
    freeHeadOffset: int = struct.unpack('<Q', f.read(8))[0]  # 8 byte
    rootOffset   : int = struct.unpack('<Q', f.read(8))[0]  # 8 byte
    N             : int = struct.unpack('<Q', f.read(8))[0]  # 8 byte, number of child

NODE_SIZE = 33 + (N - 1) * 16   # node struct : m, isLeaf, parent, r, *p
NODE_FORMAT = '<QBQQQ' + (N - 1) * 'QQ'
modified = []              #list of modified node

match(cmd[1]):
    case('-i'): insert(*cmd[2:])
    case('-d'): delete(*cmd[2:])
    case('-s'): search(*cmd[2:])
for i in modified:
    with open(ifile, 'r+b'):
            ...