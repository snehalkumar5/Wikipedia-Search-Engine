# Wikipedia Search Engine

An efficient and scalable search engine for Wikipedia pages.

Consists of two main stages:
1. Creation of inverted index
2. Mechanism of query searches

Software optimized for search time, search relevancy, indexing time and indexing size.

## Files structure
1. indexer.py
This file uses the wiki dump and generates the index files. 
While parsing the dump xml file using saxparser, it processes the content and writes inverted indexes. The files are created in blocks to satisfy memory constraints
Run command: 
```
$ python3 indexer.py dump.xml <index_dir> <title_dir>
```
 
These index files are combined into 19382 sorted files to get the final index
3. config.py 
This file contains the configs and tokens for the other files
4. search.py
This file takes in queries and runs search for them in the index. It tokenises the queries before performing binary searching on the sorted index to get the result
Run command: 
```
$ python3 search.py queries_op.txt
```

## Functionality:
The search engine is built by going through the following stages:
1. XML Parsing
2. Tokenization
3. Case folding
4. Stop words removal
5. Stemming
6. Inverted Index creation
7. Optimization and query

