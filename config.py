# Configuration settings
import nltk
nltk.download("stopwords")
from nltk.corpus import stopwords
import sys
import os

BLOCKSIZE = 1000
TITLES_PER_PAGE = 10000
TOTAL_DOCS = 22000000

output = "./queries_op.txt"      
idx_dir = "./mergedIndex/"

stem_words = {}
cur_stopwords = set()
all_stopwords = stopwords.words('english')
mystops = ["www","https","http","com","ref","use","title","date","imag","reflist","defaultsort","use","list","jpg","descript","redirect","categori",
    "name","refer","author","url","infobox","site","web", "also","org","publish",
    "cite","websit","caption",]
mapp = {"t": 0, "b": 1, "i": 2, "c": 3, "l": 4, "r": 5, "f": 6}
rev_map = {0: "T", 1: "B", 2: "I", 3: "C", 4: "L", 5: "R", 6: "F"}

puncts = '\n\r!"#$&*+,-./;?@^_~)({}[]|=<>\\'
REG_TOKEN = r'[^A-Za-z0-9]+'
REG_INFO = r'{{Infobox|{{infobox|{{ Infobox| {{ infobox'
REG_CAT = r'\[\[Category|\[\[ Category'
REG_REF = r'==References==|== References ==|== references ==|==references=='
REG_LINK = r'==External links==|== External links =='
