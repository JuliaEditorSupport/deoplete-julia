# ============================================================================
# FILE: desctag.py
# AUTHOR: Lyndon White <lyndon.white at research.uwa.edu.au
#         Felipe Morales <hel.sheep at gmail.com>
#         Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
# ============================================================================

import re
from collections import namedtuple
from os.path import exists, getmtime, getsize
from .base import Base
import codecs
TagsCacheItem = namedtuple('TagsCacheItem', 'mtime candidates')

def readtagfile(f):
    # Replace deocomplete.util.parse_file_pattern(f, '^[^!][^\t]+'))
    for line in f:
        if not(line.strip()): continue

        entries = line.split("\t")
        try:
            word, file, address = entries[0:3]
            fields = dict([ff.split(":",1) for ff in entries[3:-1]])
            fields = dict([(kk.strip(),vv.strip()) for kk,vv in fields.items()])

            yield {'word':word,
                   'dup':1,
                   'kind':fields.get('kind',""),
                   'menu':fields.get('module',"")+"."+fields.get('string',""),
                   'info':(fields.get('module',"")+"."+fields.get('string',"") + "\n"+
                           codecs.decode(fields.get("doc",""), "unicode-escape"))
                   }
        except ValueError as ee:
            if line[0]=='!':
                pass
            else:
                raise(ValueError("On line: " + line +"\n",ee))



class Source(Base):

    def __init__(self, vim):
        Base.__init__(self, vim)

        self.name = 'desctag'
        self.mark = '[D]'

        self.__cache = {}

    def on_buffer(self, context):
        self.__make_cache(context)

    def gather_candidates(self, context):
        self.__make_cache(context)

        candidates = dict()
        for filename in [x for x in self.__get_tagfiles() if x in self.__cache]:
            for cand in  self.__cache[filename].candidates:
                candidates[cand['word']] = candidates.get(cand['word'],[])
                candidates[cand['word']].append(cand)


        p = re.compile('(?:{})$'.format(context['keyword_patterns']))
        return [cand for word in candidates.keys() if p.match(word) for cand in candidates[word]]


    def __make_cache(self, context):
       for filename in self.__get_tagfiles():
            mtime = getmtime(filename)
            if filename not in self.__cache or self.__cache[
                    filename].mtime != mtime:
                with open(filename, 'r', errors='replace') as f:
                    self.__cache[filename] = TagsCacheItem(mtime, list(readtagfile(f)))



    def __get_tagfiles(self):
        include_files = self.vim.call(
            'neoinclude#include#get_tag_files') if self.vim.call(
                'exists', '*neoinclude#include#get_tag_files') else []
        return [x for x in self.vim.call(
                'map', self.vim.call('tagfiles') + include_files,
                'fnamemodify(v:val, ":p")')
                if exists(x)]
