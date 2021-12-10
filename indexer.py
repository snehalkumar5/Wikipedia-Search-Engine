import config
import xml.sax
import os
import sys
import time
import re
from nltk.stem import SnowballStemmer

stemmer = SnowballStemmer('english')
# stemmer = Stemmer.Stemmer('english')
get_info = re.compile(config.REG_INFO)
get_cats = re.compile(config.REG_CAT)
get_refs = re.compile(config.REG_REF)
get_links = re.compile(config.REG_LINK)
get_toks = re.compile(config.REG_TOKEN)

class SaxParser(xml.sax.ContentHandler):
    def __init__(self, idx_dir, title_dir):
        self.dir_idx = idx_dir
        self.dir_title = title_dir
        self.pg_titles = {}
        self.index = {}
        self.fileno = 0
        self.current_data = []
        self.page_count = 0
        self.stemmed_words = {}
        self.curattr = ""
        self.title_flag = False
        self.all_tokens = {}
        self.tags = ['page','title','text','id']
        self.text_flag = False
        self.map = {"title":0,"body":1,"info":2,"cat":3,"link":4,"ref":5,"f":6}

    def startElement(self, tag, attr):
        if tag in self.tags:
            if tag == self.tags[0]:
                self.page_count += 1
            elif tag == self.tags[1]:
                self.title_flag = True
            elif tag == self.tags[2]:
                self.text_flag = True
        self.curattr = attr

    def endElement(self, tag):
        if tag == "mediawiki":
            print("Time taken: ",time.time() - start_time)
            self.write_inv_index()
            self.index = {}
            self.pg_titles = {}
        elif tag == self.tags[1]:
            self.title_flag = False
        elif tag == self.tags[2]:
            txt = " ".join(self.current_data)
            body_tokens = self.get_processed_text(txt)
            self.add_to_index(body_tokens, self.page_count, self.map["body"])
            info_tokens = self.infobox(txt)
            self.add_to_index(info_tokens, self.page_count, self.map["info"])
            split_text = re.split(get_cats, txt, 1)
            if len(split_text) > 1:
                self.add_to_index(self.get_processed_text(split_text[1]), self.page_count, self.map["cat"])
            split_text = re.split(get_links, txt, 1)
            if len(split_text) > 1:
                split_text = re.split(r"==|\[\[", split_text[1], 1)
                self.add_to_index(self.get_processed_text(split_text[0]), self.page_count, self.map["link"])
            split_text = re.split(get_refs, txt, 1)
            if len(split_text) > 1:
                self.add_to_index(self.get_processed_text(re.split(r"==|<|\[\[", split_text[1])[0]), self.page_count, self.map["ref"])
            for s in re.findall(r'<ref(.+?)>', txt):
                self.add_to_index(self.get_processed_text(s), self.page_count, self.map["ref"])
            if self.page_count % 1000 == 0:
                print(f"Processed till page:{self.page_count}")
            self.text_flag = False
            if self.page_count % 100000 == 0:
                self.write_inv_index()
                self.index = {}
                self.pg_titles = {}
        self.current_data = []
    
    def check_enc(self,token):
        try:
            token = token.encode(encoding='utf-8')
            token = token.decode('ascii')
        except UnicodeDecodeError:
            return False
        else:
            return True
    
    def characters(self, content):
        if self.text_flag:
            self.current_data.append(content)
            return
        if self.title_flag:
            self.pg_titles[self.page_count] = content
            tokens = self.get_processed_text(content, True)
            self.add_to_index(tokens, self.page_count, self.map["title"])
    
    def isinvalid_token(self, token):
        if token is None or not token:
            return True
        if token in config.mystops:
            return True
        if not self.check_enc(token):
            return True
        if len(token) >5 and token[0].isdigit():
            return True 
        return False
    
    def get_processed_text(self, text, add_tokens=False):
        procs = []
        def stem(token):
            if token in self.stemmed_words:
                return self.stemmed_words[token]
            else:
                self.stemmed_words[token] = stemmer.stem(token)
            return self.stemmed_words[token]
        if not text:
            return procs
        tokenized_text = " ".join(re.split(config.REG_TOKEN, text)).split()
        tokens = [token for token in tokenized_text if token.isalnum() and token not in config.all_stopwords]
        procs = [stem(token) for token in tokens]
        return procs
    
    def infobox(self, text)->list:
        tokens = []
        idx = [r.start() for r in re.finditer(get_info, text)]
        n = len(text)
        for st in idx:
            # st = r.start()
            cnt, ed = 0, -1
            for i in range(st, n-1):
                ck = text[i:i+2]
                if ck == "{{":
                    cnt = cnt+1
                elif ck == "}}":
                    cnt = cnt-1
                if cnt!=0:
                    continue
                ed = i
                break
            tmp = self.get_processed_text(text[st:ed+2])
            # print(tmp)
            tokens += tmp
        return tokens
    
    def add_to_index(self, tokens, pg_id, field_id):
        for token in tokens:
            if self.isinvalid_token(token):
                continue
            else:
                if token not in self.index:
                    self.index[token] = {}
                if pg_id not in self.index[token]:
                    # self.index[token][pg_id] = self.map['title']
                    self.index[token][pg_id] = [0 for _ in range(6)]
                self.index[token][pg_id][field_id] += 1

    def write_inv_index(self):
        with open(f"{self.dir_title}/{self.fileno}.txt", "w") as f:
            data = ""
            srt_pgs = sorted(self.pg_titles.items())
            for page_id, title in srt_pgs:
                data += f"{page_id} {title}\n"
            f.write(data)

        print("Writing Inverted Index")
        with open(f"{self.dir_idx}/{self.fileno}.txt", "w") as f:
            lines = []
            srt_idx = sorted(self.index.items())
            for token, page_ids in srt_idx:
                # print(token,page_ids)
                lot = []
                for pgid, val in self.index[token].items():
                    value = ""
                    for fld,cnt in enumerate(self.index[token][pgid]):
                        if cnt == 1:
                            value += config.rev_map[fld].lower()
                        elif cnt > 1:
                            value += f"{config.rev_map[fld]}{cnt}"
                if value:
                    q = hex(pgid)
                    lot.append(f'{q[2:]}={value}')
                pres = ';'.join(lot)
                lines.append(f'{token};{pres}')
            f.write("\n".join(lines))
        self.stemmed_words={}
        self.fileno += 1

def get_dir(dir_name):
    a_dir = dir_name
    a_dir = a_dir[:-1] if a_dir[-1] == '/' else a_dir
    if not os.path.isdir(a_dir):
        os.mkdir(a_dir)
    return a_dir

if __name__ == "__main__":
    start_time = time.time()
    if len(sys.argv) != 4:
        print("Wrong arguments")
        quit()
    dump = sys.argv[1]
    idx_dir = get_dir(sys.argv[2])
    title_dir = get_dir(sys.argv[3])
    parser = xml.sax.make_parser()
    parser.setFeature(xml.sax.handler.feature_namespaces, 0)
    Handler = SaxParser(idx_dir,title_dir)
    parser.setContentHandler(Handler)
    parser.parse(dump)
