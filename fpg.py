from argparse import ArgumentParser
from itertools import (chain, combinations)
from collections import defaultdict

def read_data(filepath):
    """
    Return itemsets & trans array from the file
    """
    trans = []
    with open(filepath) as fp:
        for line in fp:
            trans.append(frozenset({x.strip() for x in line.split(',')}))
    itemsets = {frozenset([y]) for x in trans for y in x}

    return itemsets, trans

def count_freq(count_dict, set_list, trans):
    """
    Count itemsets in transctions and update the count_dict
    """
    for x in set_list:
        count_dict[x] = 0
    for x in set_list:
        for y in trans:
            if x.issubset(y):
                count_dict[x] = count_dict[x] + 1

def support(count_dict, item, trans):
    """
    Return support of the item
    Notice: count_dict need to be init. before this function by count_freq()
    """
    item_frozenset = frozenset(item)
    return 1.0*count_dict.get(item_frozenset, 0)/len(trans)

class Node(dict):
    """
    Node is identified and hashed by the name. Therefore, nodes in the same tree must with different names.
    Root node does not has name.
    """

    def __init__(self, name=None, parent=None):
        self.name = name
        self.parent = parent # Node
        self.child = {} # str => Node
        self.count = 0

    def __str__(self):
        return "Node:", self.name

    def is_root(self):
        return self.name == None

    def __hash__(self):
        return hash(self.name)

    def __lt__(self, other):
        return self.count < other.count

    def connect(self, child):
        """
        Connect parent and child nodes by setting attr. of nodes
        """
        self.child[child] = child
        child.parent = self
        child.count = child.count + 1

def subset(ori):
    ret = list(chain.from_iterable([combinations(ori, i) for i in xrange(1, len(ori)+1)]))
    return [frozenset(x) for x in ret]

def traceback_mincount(traceback):
    """
    Return list of tuple (subset, mincount) of nodes
    """
    item_node = traceback[0]
    # sort traceback nodes
    sorted_traceback = sorted([node for node in traceback[1:]])
    # generate subset of traceback nodes
    traceback_subset = subset({node.name for node in traceback[1:]})
    # generate return list
    ret = []
    for x in traceback_subset:
        for y in sorted_traceback:
            # compare the smallest count of traceback[1:] and count of item node
            if y.name in x:
                mincount = y.count if y.count<item_node.count else item_node.count
                ret.append((x.union({item_node.name}), mincount))
                break
    return ret

def traceback_to_patterns(traceback_list, minsup, trans):
    """
    Return dict. of freq. patterns according to a list of traceback. eg. {forzenset pattern: count}
    traceback: list contains all nodes from item node to the one before root node. eg. [node...]
    """
    patterns = defaultdict(int)
    # count all subsets
    for traceback in traceback_list:
        for ss, mincount in traceback_mincount(traceback):
            patterns[ss] = patterns[ss] + mincount
    # check minsup
    for k, v in patterns.copy().iteritems():
        if 1.0*v/len(trans) < minsup:
            del patterns[k]
    return patterns

def cmd():
    # Parse options
    parser = ArgumentParser()
    parser.add_argument('-f', '--file', help='Input csv file path (data separating with comma)', dest='filepath', required=True)
    parser.add_argument('-s', '--minsup', help='minumum support (0~1)', dest='minsup', default=0.5)
    options = parser.parse_args()

    itemsets, trans = read_data(options.filepath)

    ## FP-Growth Algorithm
    
    ## Create sorted one-item list
    count_dict = {}
    # one item count
    count_freq(count_dict, itemsets, trans)
    # sort one-item by count
    sorted_freq_dict = sorted(count_dict.iteritems(), key=lambda x: x[1], reverse=True)
    # check minsup
    sorted_freq_dict = filter(lambda x: support(count_dict, x[0], trans) >= options.minsup, sorted_freq_dict)
    # assign index of elements in freq_list
    freq_list_index_map = {}
    for i, x in enumerate(sorted_freq_dict):
        freq_list_index_map[x[0]] = i
    print sorted_freq_dict
    print freq_list_index_map

    ## Modify and reorder all trans. according to sorted one-item list
    # create set of freq. one item
    freq_one_item_set = {x for frozenset_count in sorted_freq_dict for x in frozenset_count[0]}
    print freq_one_item_set
    # represent sorted trans. by 2d list
    sorted_trans = [list(trans_set & freq_one_item_set) for trans_set in trans]
    # delete and rearrange trans. by sorted_freq_dict
    for idx, arr in enumerate(sorted_trans):
        sorted_trans[idx] = sorted(arr, key=lambda x: freq_list_index_map[frozenset([x])])
    print sorted_trans

    ## Construct FP-Tree
    horizon_access = defaultdict(list) # {[name...], ...}
    root = Node()
    for tran in sorted_trans:
        cur_node = root
        for x in tran:
            # try to get old node
            next_node = cur_node.child.get(x, None)
            # if new node is created
            if next_node is None:
                next_node = Node(x)
                horizon_access[x].append(next_node)
            # connect and count
            cur_node.connect(next_node)
            # move to next node
            cur_node = next_node

    print "----- TEST ----"
    m1 = Node("m")
    m1.count = 2
    a = Node("a")
    a.count = 3
    c = Node("c")
    c.count = 3
    f = Node("f")
    f.count = 4

    m2 = Node("m")
    m2.count = 1
    b = Node("b")
    b.count = 1

    tracebacks = [[m1,a,c,f], [m2,b,a,c,f]]
    print traceback_to_patterns(tracebacks, options.minsup, trans)

if __name__ == '__main__':
    cmd();
