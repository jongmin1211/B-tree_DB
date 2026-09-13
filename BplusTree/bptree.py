import sys
import struct

class node:
    def __init__(self, m :int = 1, p : list = None, r : int = None, isLeaf = True, parent : int = None):
        self.m = m  # # of keys
        self.p = p  # array of [key, left chile node] or [key, value]
        self.r = r  # a pointer to the rightmost child node or right sibling node
        self.isLeaf = isLeaf
        self.parent = parent # pointer for parent. if root: None
        

def readNode(ifile, offset) -> node:
    with open(ifile, 'rb') as f:
        f.seek(rootOffset + offset)
        data = f.read(NODE_SIZE)
        #data read error
        if len(data) != NODE_SIZE:
            raise ValueError("Invalid node size while reading")
        m, isLeaf, parent, r, *p = struct.unpack(NODE_FORMAT, data)
        p = list(zip(p[::2], p[1::2])) # make pair

        return node(m, p, r, isLeaf, parent)

def keyFind(n :node, key) -> node: # find the locate of key and return that node
    if n.isLeaf:
        return n
    else : 
        for i in n.p:
            treeKey = i[0]
            if key < treeKey:
                keyFind(readNode(ifile, i[1]), key)
            keyFind(n.r, key)

def split(n):
    mid = n.m//2
    rightNode = node(isLeaf=n.isLeaf, parent=n.parent, r = n.r)
    rightNode.p = n.p[mid:]
    n.p = n.p[:mid]
    rightNode.m = len(rightNode.p)
    n.m = len(n.p)
    n.r = rightNode
    #node split
    rightNode.p[0]
            

# bptree function
def create(ifile, maxNumOfChild):
    with open(ifile, 'wb') as f:
        f.write(bytes([maxNumOfChild]))
    
def insert(ifile,  key, value):
    with open(ifile, 'r+b') as f:
        numberOfChild = f.read(1)[0]
        if rootOffset == b'':           #root doesnt exist, tree empty
            node(m = 1, p = [key,value], r = None)
            ifile.write()
            return
        else:
            n:node
            targetNode = keyFind(n, key)
            for i in range(targetNode.m - 1):
                if targetNode.p[i][0] == key:
                    print(f"duplicated key. key : {key}, value : {value}")
                    return
                if targetNode.p[i][0] < key:
                    continue
                else:
                    targetNode.m += 1
                    targetNode.p.insert(i, [key, value])
                    n.r = targetNode.r
                    targetNode.r = n

                    #do split
                    if n.m+1 > numberOfChild:
                        mid = n.m//2
                        rightNode = node()
                        rightNode.p = n.p[mid:]
                        n.p = n.p[:mid]
                        rightNode.m = len(rightNode.p)
                        n.m = len(n.p)
                        n.r = rightNode
                        #node split
                        rightNode.p[0]


                n.r = targetNode.r
                targetNode.r = n
            


def delete(ifile, key):...
def search(ifile, key):
    root = readNode(ifile, rootOffset)
    
def search(ifile, start, end):...




#main
cmd = sys.argv
if len(cmd) < 3 or len(cmd) > 5:
    exit(1)
else:
    if(cmd[1]) == '-c':
        create(*cmd[2:])
    ifile = cmd[2]
    with open(ifile, 'r') as f:
        #file meta data
        newOffset     : int   = f.read()  # 8 byte
        freeHeadOffset: int   = f.read()  # 8 byte
        rootOffset    : int   = f.read()  # 8 byte
        maxNumOfChild    : int   = f.read()  # 4 byte

    NODE_SIZE = 25 + (maxNumOfChild - 1) * 16
    NODE_FORMAT = '<QBQQ' + (maxNumOfChild - 1) * 'QQ'
    modified = []              #list of modified node
    match(cmd[1]):
        case('-i'): insert(*cmd[2:])
        case('-d'): delete(*cmd[2:])
        case('-s'): search(*cmd[2:])
    for i in modified:
        with open(ifile, 'r+b'):
                ...