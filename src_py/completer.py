
##########  Config
julia_cmd = "julia-master"
core_path = "~/build/julia-master/base/coreimg.jl"
base_path = "~/build/julia-master/base/sysimg.jl"

############main program

import pyparsing as pp


def default_loadpaths():
    import subprocess
    process = subprocess.Popen([julia_cmd,"-e",
        'print(join([LOAD_PATH..., Pkg.Dir.path()],"\n"))'],
        stdout=subprocess.PIPE)
    process_stdout = process.communicate()[0]
    return process_stdout.decode('utf-8').split('\n')


loadpaths = default_loadpaths()


RESERVED_WORDS = ["if", "else", "elseif", "while", "for", "begin", "end", "quote", "try", "catch", "return", "local", "abstract", "function", "macro", "ccall", "finally", "typealias", "break", "continue", "type", "global", "module", "using", "import", "export", "const", "let", "bitstype", "do", "in", "baremodule", "importall", "immutable"]
pp_reserved_word = pp.Or([pp.Literal(ww) for ww in RESERVED_WORDS])
pp_identifier = (pp.NotAny(pp_reserved_word)
                + pp.Word(pp.alphanums + "@" + "!"))

TRANSPERENT_PREFIXES = ["@inline", "const"]
pp_transperent_prefix = pp.Optional(pp.Or(
    [pp.Literal(ww) for ww in TRANSPERENT_PREFIXES])).suppress()


def _matched_only(matched):
    return[match for matchgrp in matched
                   for match in matchgrp[0]]


def get_exports(raw_text):
    pp_exports =  (pp.Literal("export").suppress()
                   + pp.delimitedList(pp_identifier)
                  )

    parsed_exports = pp_exports.scanString(raw_text)
    return _matched_only(parsed_exports)

def get_vars(top_scoped_text):

    #HACK: Because scoped blocks in well written code are indented, we are currently using this whitespace sensitivity at start of line to not match stuff in blocks
    #NOmatch ' a'
    #NOmatch:  `b` in `a,b=2,3`
    #NOmatch `b` in `a=2;b=2`
    #NOmatch `(a,b)`
    pp_vars = ( pp.LineStart()
#                + pp_transperent_prefix
                + pp_identifier
               )
    parsed_vars = pp_vars.scanString(top_scoped_text)
    return _matched_only(parsed_vars)

def get_macros(top_scoped_text):
    pp_macros = (pp.LineStart()
                 + pp.Literal("macro")
                 + pp_identifier)
    parsed_macros = pp_macros.scanString(top_scoped_text)
    macros = _matched_only(parsed_macros)
    return ["@"+macro for macro in macros]


def get_nonexports(raw_text):
     #TODO scope first here

    top_scoped_text = raw_text

    return get_vars(top_scoped_text) + get_macros(top_scoped_text)



def using_file(fp, ModuleName):
    raw_text = fp.read()
    print(raw_text)
    print("-"*30)
    print("exports: ", get_exports(raw_text))

    print("nonexports: ", get_nonexports(raw_text))


"""
Import Command  What is brought into scope  Available for method extension
using MyModule                |  All exported names (x and y), MyModule.x, MyModule.y and MyModule.p
using MyModule.x, MyModule.p  |  x and p
using MyModule: x, p          |  x and p
import MyModule.x, MyModule.p |  x and p
import MyModule: x, p         |  x and p
importall MyModule            |  All exported names (x and y)

using Module = importall Module + import Module


"""

using_file(open("../samples/sample.jl","r"),"Sample")



