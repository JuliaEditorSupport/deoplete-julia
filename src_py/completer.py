
##########  Config
julia_cmd = "julia-master"
core_path = "~/build/julia-master/base/coreimg.jl"
base_path = "~/build/julia-master/base/sysimg.jl"

hard_coded_loadpaths =["../samples"]
############main program

############## UTIL
def flatten(list_of_lists):
    return [item for sublist in list_of_lists for item in sublist]
############ Path related things

import os
import pyparsing as pp


def default_loadpaths():
    import subprocess
    process = subprocess.Popen([julia_cmd,"-e",
        'print(join([Pkg.Dir.path(),LOAD_PATH...],"\n"))'],
        stdout=subprocess.PIPE)
    process_stdout = process.communicate()[0]
    julia_loadpaths = process_stdout.decode('utf-8').split('\n')
    return hard_coded_loadpaths + julia_loadpaths


loadpaths = default_loadpaths()
"""
_working_dirs = [] #Managed by Context()

def current_working_dir():
    global _working_dirs
    return _working_dirs[-1]

class Context():
    def __init__(self, working_dir):
        self.working_dir = working_dir
    def __enter__(self)
        global _working_dirs
        _working_dirs.push(self.working_dir)
    def __exit__(self,type,value,traceback)
        global _working_dirs
        _working_dirs.pop()

"""

########## Finding Identifiers

RESERVED_WORDS = [ "abstract", "baremodule", "begin", "bitstype", "break", "catch", "ccall", "const", "continue", "do", "else", "elseif", "end", "export", "finally", "for", "function", "global", "if", "immutable", "import", "importall", "in", "let", "local", "macro", "module", "quote", "return", "try", "type", "typealias", "using", "while"]
pp_reserved_word = pp.Or([pp.Literal(ww) for ww in RESERVED_WORDS])
pp_identifier = (pp.NotAny(pp_reserved_word)
                + pp.Word(pp.alphanums + "@" + "!"+"_"))

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
                + pp_identifier
               )
    parsed_vars = pp_vars.scanString(top_scoped_text)
    return _matched_only(parsed_vars)


def get_macros(top_scoped_text):
    pp_macros = (pp.LineStart()
                 + pp.Literal("macro").suppress()
                 + pp_identifier)
    parsed_macros = pp_macros.scanString(top_scoped_text)
    macros = _matched_only(parsed_macros)
    return ["@"+macro for macro in macros]


def get_functions_and_types(top_scoped_text):
    pp_functions = (pp.LineStart()
                 + (pp.Literal("function")
                        | pp.Literal("type")
                        | pp.Literal("immutable")
                        | pp.Literal("abstract")
                        | pp.Literal("typealias")).suppress()
                 + pp_identifier)
    parsed_functions = pp_functions.scanString(top_scoped_text)
    functions = _matched_only(parsed_functions)
    return functions


def get_nonexports(raw_text):
     #TODO scope first here
    top_scoped_text = raw_text
    return (get_vars(top_scoped_text)
            + get_macros(top_scoped_text)
            + get_functions_and_types(top_scoped_text))

########### Preprocessing (and includes)

def load_include(path):
    with open(path,"r") as fp:
        return fp.read()


def flatten_includes(text):
    past_includes =set()
    while(True): #Got to allow for for recursive includes
        changed=False
        def subsitute_include(string,loc, tokens):
            path=tokens[0][0][1:-1]
            if path in past_includes:
                return "" #Avoid including something already included, (no infinite loops)
            else:
                past_includes.add(path)
                changed=True;
                return load_include(path)

        pp_include = (pp.Literal("include").suppress()
                       + pp.nestedExpr(
                            content=pp.QuotedString('"')
                        ).addParseAction(subsitute_include)

                   )
        text = pp_include.transformString(text )

        if not(changed):
             return text


def preprocess(raw_text):
    #TODO: Not handling `requires` or `reloads` right now
    text=flatten_includes(raw_text)
    return text


############## Loading
#See also https://github.com/JuliaLang/julia/blob/d6df2a0b166d360b24f4cc3631a65e3cc5c56476/base/loading.jl


class ModuleNotFoundError(Exception):
    def __init__(self, module_name, loadpaths):
        self.module_name=module_name
        self.loadpaths=loadpaths
    def __str__(self):
        return "Failed to find: " + self.module_name + " in " + ", ".join(self.loadpaths)



def load_module(module_name):
    import os.path

    for lpath in loadpaths:
        fn = os.path.join(lpath,module_name+".jl")
        try:

            with  open(fn,'r') as fp:
                raw_text = fp.read()
            return preprocess(raw_text)
        except FileNotFoundError:
            pass #No problem try the next

    raise ModuleNotFoundError(module_name, loadpaths)


########## Using/Import/Importall

"""
Import Command  What is brought into scope  Available for method extension
using MyModule                |  All exported names (x and y), MyModule.x, MyModule.y and MyModule.p
using MyModule.x, MyModule.p  |  x and p
using MyModule: x, p          |  x and p
import MyModule               |  MyModule.x, MyModule.y and MyModule.p
import MyModule.x, MyModule.p |  x and p
import MyModule: x, p         |  x and p
importall MyModule            |  All exported names (x and y)

using Module = importall Module + import Module
"""
def importall_module(module_name):
    raw_text = load_module(module_name)
    return get_exports(raw_text)

def import_module(module_name):
    raw_text = load_module(module_name)
    return [module_name+"."+id for id in get_nonexports(raw_text)]

def using_module(module_name):
    return importall_module(module_name)+import_module(module_name)


def using_system_pseudomodules(imgpath, module_name):
    pass
#    with open(imgpath,"r"):
#        raw_text
#    return get [module_name+"."+id for id in get_nonexports(raw_text)]

"""
Given some text, from the current file,
return all the completions -- ie all identifiers currently in scope
"""
def get_completions(main_text):
    main_text=preprocess(main_text)
    #TODO : I suspect you can mix all the styles in one line. I am currently ignoring that possiblily
    #TODO : explict imports
    #TODO : system libraries
    def get_modules(import_type):
        pp_imp = (pp.Literal(import_type).suppress()
                   + pp.delimitedList(pp_identifier)
                  )

        parsed_imps = pp_imp.scanString(main_text)
        return _matched_only(parsed_imps)

    completions=RESERVED_WORDS #Reseved words are always completable
    completions += flatten([using_module(mod) for mod in get_modules("using")])
    completions += flatten([importall_module(mod) for mod in get_modules("importall")])
    completions += flatten([import_module(mod) for mod in get_modules("import")])

    return set(completions)



###################testing
import os
os.chdir("../samples")

def prl(ss):
    ss= list(ss)
    ss.sort()
    print(ss)


prl(get_completions(open("../samples/main.jl","r").read()))



