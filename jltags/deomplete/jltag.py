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
import subprocess
import codecs
TagsCacheItem = namedtuple('TagsCacheItem', 'mtime candidates')

def readtagfile(f):
    # Replace deocomplete.util.parse_file_pattern(f, '^[^!][^\t]+'))
    for line in f:
        if not(line.strip()) or line[0]=='!'  : continue

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
            raise(ValueError("On line: " + line +"\n",ee))


JULIA_PATH = "/home/ubuntu/build/julia-master/julia"
JLTAG_PATH = "/mnt/julia-vim-completions/jltags/jltag.jl"

def get_refered_tagfiles(vim):
    current_filename = vim.call('expand','%:p')
    #vim.command("echom \"jltag: %s\"" % current_filename)
    jltag_proc = subprocess.Popen([JULIA_PATH, JLTAG_PATH, "refer", current_filename],
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)

    for line in jltag_proc.stderr.readlines():
        vim.command("echom \"jltag Tagger: %s\"" % line.decode('utf-8').strip())

    tagfiles=[line.decode('utf-8').strip() for line in jltag_proc.stdout.readlines()]
    return tagfiles



class Source(Base):

    def __init__(self, vim):
        Base.__init__(self, vim)

        self.name = 'jltag'
        self.mark = '[J]'
        self.filetypes = ['julia']
        self.__cache = {}

    def on_event(self, context):
        if 'tag' in context['sources']:
            self.vim.command("echom \"jltag: Warning deocomple-source 'tag' and  'jltag' probably should not mix.\"")
        self.__make_cache(context)

    def gather_candidates(self, context):
        if len(self.__cache)==0:
            self.__make_cache()

        candidates = dict()
        for filename in self.__cache.keys():
            for cand in  self.__cache[filename].candidates:
                candidates[cand['word']] = candidates.get(cand['word'],[])
                candidates[cand['word']].append(cand)

        p = re.compile('(?:{})$'.format(context['keyword_patterns']))
        return [cand for word in candidates.keys() if p.match(word) for cand in candidates[word]]


    def __make_cache(self):
        for filename in self.__get_tagfiles():
            mtime = getmtime(filename)
            if filename not in self.__cache or self.__cache[filename].mtime != mtime:
                with open(filename, 'r', errors='replace') as f:
                    tags = list(readtagfile(f))
                    self.vim.command("echom \"jltag: %s, with %s tags\"" % (filename,len(tags)))
                    self.__cache[filename] = TagsCacheItem(mtime,tags)

        self.vim.command("echom \"jltag: Cache Made\"")


    def __get_tagfiles(self):
        refered_tagfiles = get_refered_tagfiles(self.vim)

        include_files = self.vim.call(
            'neoinclude#include#get_tag_files') if self.vim.call(
                'exists', '*neoinclude#include#get_tag_files') else []
        return [x for x in self.vim.call(
                'map', self.vim.call('tagfiles') + include_files + refered_tagfiles,
                'fnamemodify(v:val, ":p")')
                if exists(x)]


