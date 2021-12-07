import sys
import os
import pandas as pd
from optparse import OptionParser

# This function will recursively generate all subset of specified length from a given Set.
def genCombinatrics(itemset, i, el, cur, ans):
    if(el == 0):
        ans.append(tuple(cur))
        return

    rl = len(itemset) - i;
    if(rl < el):
        return
    
    newcur = []
    newcur.extend(cur)
    newcur.append(itemset[i])
    genCombinatrics(itemset, i + 1, el - 1, newcur, ans)
    genCombinatrics(itemset, i + 1, el, cur, ans)


def getCombinatrics(itemset, el):
    ans = []
    if(el > 0):
        genCombinatrics(itemset, 0, el, [], ans)
    return ans


#This function will generate all association for a given set.
def genAssocs(itemset):
    L = len(itemset)
    ans = []
    for i in range(1, L):
        for s1 in getCombinatrics(itemset, i):
            s2 = tuple(set(itemset) - set(s1))
            ans.append((s1, s2))
            #print("%s -> %s"%(s1, s2))
    return ans

def getItemTransMap(trans):
    items = {}
    for tid in trans:
        values = trans[tid]
        for item in values:
            if item not in items:
                items[item] = set()
            items[item].add(tid)
    return items

def EvalAssociations(trans, L, C, maxi, min_confidence):
    N = len(trans)
    for j in range(1, maxi):
        if j > 1:
            itemsets = list(L[j]) 
            for itemset in itemsets: 
                assoc = genAssocs(list(itemset))
                L[j][itemset]['assocs'] = []
                for r in assoc:
                    A = frozenset(r[0])
                    B = frozenset(r[1])
                    # For A->B length1 means size of length of (TransactionA U TransactionB)
                    # lengthB means sizeof TransactionA for which we must to corresponding L item
                    length1 = len(L[j][itemset]['trans'])
                    length2 = len(L[len(A)][A]['trans'])
                    length3 = len(L[len(B)][B]['trans'])
                    length4 = len(L[j][itemset]['trans'])
                    if length1/length2 >= min_confidence:
                        L[j][itemset]['assocs'].append({ 'p' : { 'e' : A, 's' : length2/N },  
                                                         's' : { 'e' : B, 's' : length3/N },
                                                        'confidence' : length1/length2, 
                                                        'support' : length4/N})    


def exec_apriory(transactions, min_support, min_confidence, L, C):
    items = getItemTransMap(transactions)
    i = 0
    
    while i == 0 or len(L[i]) != 0:
        i = i + 1
        C[i] = {}
        L[i] = {}
  
        if i == 1:
            for item in items:
                C[i][frozenset([item])] = { 'support' : float(len(items[item]))/len(transactions), 'trans' : frozenset(items[item]) }
        else:

            length = len(L[i - 1])
            itemsets = list(L[i - 1])

            for j in range(0, len(itemsets)):
                for k in range(j + 1, len(itemsets)):
                    itemset = itemsets[j].union(itemsets[k])
                    if ((itemset not in C[i]) and (len(itemset) == i)):
                        transj = L[i - 1][itemsets[j]]['trans']
                        transk = L[i - 1][itemsets[k]]['trans'] 
                        transi = transj - ( transj - transk )
                        C[i][itemset] = { 'support' : float(len(transi))/len(transactions), 'trans' : transi } 
                         
        for itemset in C[i]:
            if C[i][itemset]['support'] >= min_support:
                L[i][itemset] = C[i][itemset] 
  
    del L[i] 
    EvalAssociations(transactions, L, C, i, min_confidence)  

def print_result(L, C, NT, NI, min_support, min_confidence, fileName):
    maxi = 0
    for i in L:
        if(maxi < i):
            maxi = i


    print("\n---------------------Configuration details---------------------\n")

    print("\tsupport : %s"%(min_support))
    print("\tconfidence : %s"%(min_confidence))
    print("\tdatasetfile : %s"%(fileName))
    print("\tnum_items : %s"%(NI))
    print("\tnum_transactions : %s"%(NT))


    print("\n-----------------------------SUPPORT FOR EACH LEVEL -------------\n")

    cols = [ 'items', 'count', 'support']
    df_data = {
                cols[0]: [],    
                cols[1]: [],    
                cols[2]: []    
              } 

    for i in range(1, maxi + 1):
        for itemset in L[i]:
            df_data[cols[0]].append(itemset)
            df_data[cols[1]].append(len(L[i][itemset]['trans']))
            df_data[cols[2]].append(L[i][itemset]['support'])

    print(pd.DataFrame(df_data).to_string())


    print("\n---------------------------ASSOCIATIONS AND CONFIDENCES------------\n")


    cols = [ 'full_key', 'predecessor', 'support_pred', 'successor', 'support_suc', 'support_full_key', 'confidence' ]

    df_data  = {
                    cols[0] : [],
                    cols[1] : [],
                    cols[2] : [],
                    cols[3] : [],
                    cols[4] : [],
                    cols[5] : [],
                    cols[6] : []
               }

    for i in range(1, maxi + 1):
        for itemset in L[i]:
            values = L[i][itemset]
            if 'assocs' in values:
                assocs = values['assocs']
                for assoc in assocs:
                    fk = itemset
                    sfk = assoc['support'] 
                    p  = assoc['p']['e']
                    sp = assoc['p']['s']
                    s  = assoc['s']['e']
                    ss = assoc['s']['s']
                    c  = assoc['confidence']
                    df_data[cols[0]].append(fk) 
                    df_data[cols[1]].append(p) 
                    df_data[cols[2]].append(sp) 
                    df_data[cols[3]].append(s) 
                    df_data[cols[4]].append(ss) 
                    df_data[cols[5]].append(sfk) 
                    df_data[cols[6]].append(c) 

    print(pd.DataFrame(df_data).to_string())
    
def print_transactions(trans):
    for key in trans:
        print('%s:%s'%(key, trans[key]))


def run_apriory(fileName, min_support, min_confidence):
    trans = {}
    itemset = set()
    i = 1
    with open(fileName, "r") as fp:
        lines = fp.readlines()
        for line in lines:
            key = 'T%d'%(i)
            i = i + 1
            items = [x.strip() for x in line.split(',')]
            trans[key] = items
            itemset = itemset.union(items)

    #print_transactions(trans) 
    L = {}
    C = {}
    exec_apriory(trans, min_support, min_confidence, L, C)
    print_result(L, C, len(trans), len(itemset), min_support, min_confidence, fileName)    

    
if __name__ == '__main__':
    fileName = './data/items.csv'
    min_support = 0.5
    min_confidence = 0.8
    fileName = os.path.abspath(fileName)    
    run_apriory(fileName, min_support, min_confidence)
