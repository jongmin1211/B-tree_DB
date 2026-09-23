import sys
import struct
import os
from math import *

class Node:
    def __init__(self, m :int = 1, p : list = None, r : int = -1, isLeaf = True, offset : int = None):
        self.m = m  # # of keys
        self.p = p  # array of [key, left chile node] or [key, value]
        self.r = r  # a pointer to the rightmost child node or right sibling node. if rightmost leaf node : -1
        self.isLeaf = isLeaf
        self.offset = offset # self pointer. in memory only : readNode() fills it from the offset
                             # it was asked to seek to, so it is never stored in the file.
        # no parent pointer. the path from root is tracked by findLeaf() and passed to split().
class FreeNode:
    def __init__(self, offset, nextOffset = -1):
        self.offset = offset            # in memory only, like Node.offset
        self.nextOffset = nextOffset    # 8 bytes    
# file function : readNode, readFreeNode, allocOffset, releaseOffset
def readFreeNode(offset) -> FreeNode:
        f.seek(HEADER_SIZE + offset)
        data = f.read(NODE_SIZE)
        #data read error
        if len(data) != NODE_SIZE:
            raise ValueError("Invalid freeNode size while reading")
        nextOffset = struct.unpack('<q', data[:8])[0]

        return FreeNode(offset, nextOffset)     # offset : the one we seeked to, not read from file
def writeFreeNode(f, freeNode):
        f.seek(HEADER_SIZE + freeNode.offset)
        data = struct.pack(FREENODE_FORMAT, freeNode.nextOffset)
        f.write(data)
def readNode(offset) -> Node:
        #if node is modified, do not read file
        if offset in modified:
            if modified[offset][1] == 'del':
                raise Exception("invalid access : deleted Node") 
            return modified[offset][0]
        
        f.seek(HEADER_SIZE + offset)
        data = f.read(NODE_SIZE)
        #data read error
        if len(data) != NODE_SIZE:
            raise ValueError("Invalid node size while reading")
        m, isLeaf, r, *p = struct.unpack(NODE_FORMAT, data)
        p = [list(pair) for pair in zip(p[::2], p[1::2])][:m] # make pair, drop unused slots

        return Node(m, p, r, isLeaf, offset)
def writeNode(f, node):
            flat = [x for row in node.p for x in row]
            flat += [0] * ((N - 1) * 2 - len(flat))         # pad unused slots
            f.seek(HEADER_SIZE + node.offset)
            data = struct.pack(NODE_FORMAT, node.m, node.isLeaf, node.r, *flat)
            f.write(data)
# alloc deleted node's offset. if doesnt exist, alloc new offset.
def allocOffset() -> int :
    global freeHeadOffset, newOffset
    # no FreeNode
    if freeHeadOffset == -1:
        newOffset += NODE_SIZE
        return newOffset - NODE_SIZE
    else:
        freeNode = readFreeNode(freeHeadOffset)
        # update freeHeadOffset
        freeHeadOffset = freeNode.nextOffset
        return freeNode.offset
def releaseOffset(f, offset): # release offset and make link to linked list of FreeNode.
    global freeHeadOffset

    if freeHeadOffset == -1:  
        freeHeadOffset = offset
        writeFreeNode(f, FreeNode(offset))       
    else:
        freeNode = readFreeNode(freeHeadOffset)
        while(True):
            if freeNode.nextOffset == -1:
                freeNode.nextOffset = offset
                writeFreeNode(f, freeNode)
                writeFreeNode(f, FreeNode(offset))
                break
            else:
                freeNode = readFreeNode(freeNode.nextOffset)
                writeFreeNode(f, FreeNode(offset))
# write changing of Node to file
def patchHeader(f):
        f.seek(0)
        data = struct.pack('<qqqq', newOffset, freeHeadOffset, rootOffset, N)
        f.write(data)
def patchNode(f, modified : dict[int, list]):
    for key in modified:
        node, stat = modified[key]
        if stat == 'del':
            releaseOffset(f, node.offset)
        if stat == 'mod':
            writeNode(f, node)
def patch(modified):
        patchNode(f, modified)
        patchHeader(f)

def findLeaf(n :Node, key, path :list = None, trace :list[Node, int] = None):
    # path : if given, the offsets of every node visited above the returned leaf are appended

    # find the Node that key should exist
    if n.isLeaf:
        if trace is not None:
            return n, trace
        else: return n

    if path is not None:
        path.append(n)       # remember how we got here, in place of node.parent
    
    # case2 : if key < tree's key : go left child
    for i, entry in enumerate(n.p):
        if key < entry[0]:
            if trace is not None: trace.append([n, i])
            return findLeaf(readNode(entry[1]), key, path, trace)
            
    # case3 : key is >= every key in this node : go rightmost child
    if trace is not None: trace.append([n, n.m])
    return findLeaf(readNode(n.r), key, path, trace)

def search(leaf, key):
    # if key exist in leaf return value. else return None
    for k, v in leaf.p:
        if k == key:
            return v
    return None

def split(n :Node, path : list):   # when node overflowed, split node and make parent node, keep left node and create right node.
    # path : ancestor offsets of n, root first (from findLeaf). pop() gives n's parent.
    global rootOffset
    mid = n.m//2

    rightNode = Node(isLeaf=n.isLeaf, r = n.r, offset=allocOffset())
    rightNode.p = n.p[mid:]
    rightNode.m = len(rightNode.p)

    n.p = n.p[:mid]
    n.m = len(n.p)
    n.r = rightNode.offset
    # node split

    newKey = rightNode.p[0][0]
    if not n.isLeaf:
        n.r = rightNode.p.pop(0)[1]
        rightNode.m -= 1


    # n is root, create new root node
    if not path: 
        parent = Node(1, [[newKey, n.offset]], rightNode.offset, False, allocOffset())
        rootOffset = parent.offset

    else:
        parent = readNode(path.pop().offset)
        for i in range(len(parent.p)):
            if (i == len(parent.p) - 1) and (newKey > parent.p[i][0]):
                # key should be inserted to last key
                # change r too
                parent.p.append([newKey, n.offset])
                parent.r = rightNode.offset
                break
            elif newKey < parent.p[i][0]:
                parent.p.insert(i, [newKey, n.offset])
                parent.p[i+1][1] = rightNode.offset
                break
        parent.m = len(parent.p)

        if parent.m > N - 1:
            split(parent, path)     # same path, one level shorter

    for x in (n, rightNode, parent):
        modified[x.offset] = [x, 'mod']

    return




# bptree function
def create(ifile, N):
    N = int(N)
    with open(ifile, 'wb') as f:
        data = struct.pack('<qqqq', 0, -1, -1, N)
        f.write(data)

def _insert(key, value):
    global rootOffset

    if rootOffset == -1:           #root doesnt exist, tree empty
        # create root
        root = Node(m = 1, p = [[key,value]], r = -1, offset=allocOffset())
        modified[root.offset] = [root, 'mod']
        rootOffset = root.offset
        return
    
    else:
        root = readNode(rootOffset)
        path : list = []                        # ancestors of the target leaf, in place of node.parent
        targetNode = findLeaf(root, key, path)
        for i in range(targetNode.m):
            if targetNode.p[i][0] == key:
                # if duplicated key, do not modify, return
                return
            elif targetNode.p[i][0] < key:
                continue
            else:
                targetNode.p.insert(i, [key, value])
                targetNode.m += 1
                modified[targetNode.offset] = [targetNode, 'mod']
                if targetNode.m + 1 > N:
                    split(targetNode, path)
                    return
                return
        # key is biggest
        targetNode.p.append([key, value])
        targetNode.m += 1
        modified[targetNode.offset] = [targetNode, 'mod']
        if targetNode.m + 1 > N:
            split(targetNode, path)
            return
        return
def insert(inputFile):
    #abs path to input file
    INPUT_CSV = os.path.join(HERE, 'data', inputFile)
    with open(INPUT_CSV, 'r') as inputFile:
        for line in inputFile:
            key, value = map(int, line.strip().split(','))
            _insert(key, value)
        return        

def distribute(parent, left, right, n, i):
    minKeys = ceil((N/2)-1) if n.isLeaf else ceil(N/2)-1

    if left and left.m - 1 >= minKeys:
        if n.isLeaf:
            n.p.insert(0, left.p.pop())
            parent.p[i-1][0] = n.p[0][0]
        # 중간 노드일 때 부모를 통한 스핀
        else:
            n.p.insert(0, [parent.p[i-1][0], left.r])
            left.r = left.p[-1][1]
            parent.p[i-1][0] = left.p.pop()[0]

        n.m     += 1
        left.m  -=1
        modified[parent.offset] = [parent, 'mod']
        modified[left.offset]   = [left, 'mod']
        modified[n.offset]      = [n, 'mod']
    elif right and right.m - 1 >= minKeys:
        if n.isLeaf:
            n.p.append(right.p.pop(0))
            parent.p[i][0] = right.p[0][0]

        else:
            n.p.append([parent.p[i][0], n.r])
            n.r = right.p[0][1]
            parent.p[i][0] = right.p.pop(0)[0]

        n.m     += 1
        right.m -= 1
        modified[parent.offset] = [parent, 'mod']
        modified[right.offset]  = [right, 'mod']
        modified[n.offset]      = [n, 'mod']
    else:
        raise RuntimeWarning(f"unexpected node in distribute left : {left}, right : {right}, n : {n}")
def merge(parent, left, right, i, rightmost):
    global rootOffset

    # i is parent.p's index of right node
    if rightmost:
            if left.isLeaf:
                left.m += right.m
                left.p += right.p
                left.r = right.r
                parent.r = left.offset
                parent.p.pop() # pop the seperate key
                parent.m -= 1
            else:
                sepKey = parent.p.pop()[0]
                parent.m -= 1

                left.p.append([sepKey, left.r])
                left.p += right.p
                left.r = right.r

                left.m += right.m + 1

                parent.r = left.offset

            modified[parent.offset] = [parent, 'mod']
            modified[left.offset]   = [left, 'mod']
            modified[right.offset]   = [right, 'del']
    else:
            if left.isLeaf:    
                left.m += right.m
                left.p += right.p
                left.r = right.r
                parent.p[i][1] = left.offset
                parent.p.pop(i-1)
                parent.m -= 1
            else:
                sepKey = parent.p.pop(i-1)[0]
                left.p.append([sepKey, left.r])
                left.p += right.p
                left.r = right.r

                left.m += right.m +1

                parent.p[i-1][1] = left.offset
                parent.m -= 1  

            modified[parent.offset] = [parent, 'mod']
            modified[left.offset]   = [left, 'mod']
            modified[right.offset]   = [right, 'del']  

    # 루트가 비면 루트의 rightchild가 새 루트
    if rootOffset == parent.offset and parent.m == 0:
        modified[rootOffset] = [readNode(rootOffset), 'del']
        rootOffset = parent.r
def rebalance(n, trace):
    global rootOffset

    #if leaf is root, stop
    if not trace:
        return
    
    if n.m < ceil((N-1)/2):
        parent, i = trace.pop()
        left = readNode(parent.p[i-1][1]) if i > 0 else None
        if i + 1 < parent.m:
            right = readNode(parent.p[i+1][1])
        elif i + 1 == parent.m:
            right = readNode(parent.r)
        else: right = None

        left = readNode(parent.p[i-1][1]) if i > 0 else None
        if i + 1 < parent.m:
            right = readNode(parent.p[i+1][1])
        elif i + 1 == parent.m:
            right = readNode(parent.r)
        else: right = None

        extra = 0 if n.isLeaf else 1
        if left and left.m + n.m + extra < N:
            # leaf is rightmost child
            if n.offset == parent.r:
                merge(parent, left, n, i, True)
            else:
                merge(parent, left, n, i, False)

        elif right and right.m + n.m + extra < N:
            # leaf's right sibling is rightmost child
            if right.offset == parent.r:
                merge(parent, n, right, i+1, True)
            else:
                merge(parent, n, right, i+1, False)
        else: distribute(parent, left, right, n, i)

        if parent.m < ceil((N-1)/2):
            rebalance(parent, trace)


def _delete(key):

    leaf, trace = findLeaf(readNode(rootOffset), key, trace=[])
    for index,(k,v) in enumerate(leaf.p):
        if k == key:
            leaf.p.pop(index)
            leaf.m -= 1
            break
    else:
        # 없는 키
        return
    modified[leaf.offset] = [leaf, 'mod']
    return rebalance(leaf, trace)



    
        
def delete(deleteFile):
    #TODO
    DELETE_CSV = os.path.join(HERE, 'data', deleteFile)
    with open (DELETE_CSV, 'r') as deleteFile:
        for line in deleteFile:
            key = int(line.strip())
            if rootOffset == -1:
                return
            _delete(key)
        return

def keySearch(key):
    key = int(key)

    if rootOffset == -1:
        return print('NOT FOUND')
    
    root = readNode(rootOffset)
    path = []
    v = search(findLeaf(root, key, path), key)
    for n in path:
        print(*(i[0] for i in n.p), sep=',')
    print("NOT FOUND" if v is None else v)
def rangedSearch(start, end):
    start, end = map(int, (start,end))

    if rootOffset == -1:
        return
    
    root = readNode(rootOffset)

    leaf = findLeaf(root, start, path = [])

    while(True):
        for k,v in leaf.p:
            # 종료조건 : key > end
            if k > end: 
                return
            #key, value 출력
            if k >= start:
                print(k, v, sep=',')


        if leaf.r == -1:
            break
        leaf = readNode(leaf.r)
            



#main
cmd = sys.argv
if len(cmd) < 3 or len(cmd) > 5:
    exit(1)

if(cmd[1]) == '-c':
    create(*cmd[2:])
    exit(0)

ifile = cmd[2]
with open(ifile, 'r+b') as f:
    #file meta data
    newOffset     : int = struct.unpack('<q', f.read(8))[0]  # 8 byte
    freeHeadOffset: int = struct.unpack('<q', f.read(8))[0]  # 8 byte
    rootOffset    : int = struct.unpack('<q', f.read(8))[0]  # 8 byte
    N             : int = struct.unpack('<q', f.read(8))[0]  # 8 byte, number of child
    
    HEADER_SIZE = 32
    NODE_SIZE = 17 + (N - 1) * 16   # node struct : m(8), isLeaf(1), r(8), *p(16 each)
    NODE_FORMAT = '<qBq' + (N - 1) * 'qq'
    PADDING = NODE_SIZE - 8         # freeNode struct : nextOffset(8) + padding to NODE_SIZE
    FREENODE_FORMAT = f'<q{PADDING}x'

    #file directory absolute path
    HERE        = os.path.dirname(os.path.abspath(__file__))
    BPTREE      = os.path.join(HERE, 'bptree.py')
    INDEX_DAT   = os.path.join(HERE, 'test_index.dat')
    INPUT_CSV   = os.path.join(HERE, 'data', 'input.csv')
    DELETE_CSV  = os.path.join(HERE, 'data', 'delete.csv')
    modified : dict[int, list] = dict()                # dictionary of modified node {offset : [node, 'stat']}

    match(cmd[1]):
        case('-i'): insert(*cmd[3:])
        case('-d'): delete(*cmd[3:])
        case('-s'): keySearch(*cmd[3:])
        case('-r'): rangedSearch(*cmd[3:])

    #write modification to file
    patch(modified)


