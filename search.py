from nltk.stem import SnowballStemmer
import sys
import os
import time
import multiprocessing as mp
import threading as t
import math
from collections import Counter
import config
config.cur_stopwords = set()
lines=[]
stemmer = SnowballStemmer('english')
rank_wght = [5, 3, 2, 1, 1, 1]
out_fd = None

def get_tokens(token):
    token = token.lower()
    dc = dict.fromkeys(config.puncts, " ")
    token = token.translate(str.maketrans(dc))
    dc = dict.fromkeys("`'", "")
    token = token.translate(str.maketrans(dc))
    tokens = token.split()
    return tokens

def bin_srch(token, lines):
    low = 0
    high = len(lines) - 1
    while low <= high:
        mid = (low + high)//2
        # print(mid)
        mid_line = lines[mid]
        mid_tok = mid_line.split(';',maxsplit=1)
        # print(mid_tok)
        tok = mid_tok[0]
        if tok == token:
            return mid
        elif tok < token:
            low = mid + 1 
        else:
            high = mid - 1
    return -1

def get_docscores(tokens, fields)-> dict:
    index_file = f"{config.idx_dir}{tokens[:3]}.txt"
    if not os.path.isfile(index_file):
        # print("File doesnt exist")
        return {}

    doc_scores = {}
    with open(index_file, "r") as f:
        lines = f.readlines()
    line_id = bin_srch(tokens, lines)
    if line_id != -1 and line_id >= 0:
        my_seg = lines[line_id].strip().split(';')
        part = my_seg[1:]
        n = len(part)
        fr = config.TOTAL_DOCS / n
        idfreq = math.log10(fr)
        for seg in part:
            ck = ""
            doc_id = int(seg.split("=")[0], base=16)
            freq_str = seg.split("=")[1]
            freq, score = 0, 0
            freq_map = [0 for _ in range(6)]
            bonus = 1
            for cnt in freq_str:
                if cnt.isalpha() and cnt.islower():
                    if ck:
                        freq_map[config.mapp[ck]] = freq
                    freq = 0
                    ck = cnt
                elif cnt.isalpha() and cnt.isupper():
                    if ck:
                        freq_map[config.mapp[ck]] = freq
                    freq_map[config.mapp[ck.lower()]] = 1
                    ck = ""
                    freq=0
                else:
                    freq *= 10
                    freq += int(cnt)
            for idx,val in enumerate(freq_map):
                if val>0:
                    if fields == idx:
                        bonus = 10
                    score += (rank_wght[idx]*(1+math.log2(val))*bonus*idfreq)
            if score >= 5:
                if doc_id in doc_scores:
                    doc_scores[doc_id] += score
                    continue
                    # print(score)
                doc_scores[doc_id] = score
    return doc_scores
       
def get_results(query):
    tokens = get_tokens(query)
    print(tokens)
    search_results = []
    field = config.mapp["f"]
    doc_freq = Counter()
    pool = mp.Pool(mp.cpu_count())
    for token in tokens:
        if len(token) > 2:
            if token[1] == ":":
                field = config.mapp[token[0]]
                token = token[2:]
        if token not in config.cur_stopwords:
            token = stemmer.stem(token)
        else:
            continue
        if token not in config.mystops:
            search_results.append(pool.apply_async(get_docscores, args=(token, field)))

    for res in search_results:
        res = res.get()
        # print(res)
        doc_freq = doc_freq+Counter(res)
    topres = doc_freq.most_common(10)
    for doc_id, val in topres:
        doc_id-=1
        title_no = int(doc_id) // config.TITLES_PER_PAGE
        with open(f"./titles/titles/{title_no}.txt", "r") as f:
            lines = f.readlines()
            data = lines[doc_id % config.TITLES_PER_PAGE][:-1].replace(" ", ", ", 1)
            print(data, file=out_fd)

if __name__ == "__main__":
    start_time = time.time()
    q_file = sys.argv[1]
    for w in config.all_stopwords:
        config.cur_stopwords.add(w)
    queries = []
    with open(q_file, "r") as f:
        queries = f.readlines()
    
    out_fd = open(config.output, "w+")

    for query in queries:
        print("\n", file=out_fd)
        start_time = time.time()
        get_results(query)
        print("Time taken: ", time.time() - start_time, file=out_fd)