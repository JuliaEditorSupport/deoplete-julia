"""
This is the main, core file for generating completions for Julia.
"""


import os
##########  Config
julia_cmd = "julia-master"
core_path = os.path.expanduser("~/build/julia-master/base/coreimg.jl")
base_path = os.path.expanduser("~/build/julia-master/base/sysimg.jl")

cache_folder = os.path.abspath(".") #This is where we cache the system libraries, cos they huge to  parse
hard_coded_loadpaths =["../samples"]

###########################################################################################################
###########################################################################################################
import pyparsing as pp
#pp.ParserElement.enablePackrat()
import syntax
import warnings
from warnings import warn
import json

from repoze.lru import lru_cache



###############Exceptions
class ModuleNotFoundError(UserWarning):
    def __init__(self, module_name, loadpaths):
        self.module_name=module_name
        self.loadpaths=loadpaths
    def __str__(self):
        return "Failed to find: " + self.module_name + " in " + ", ".join(self.loadpaths)


class IncludeNotFoundError(UserWarning):
    def __init__(self, path,inner):
        self.path = path
        self.inner = inner
    def __str__(self):
        return "Failed to find include: " + self.path



############## UTIL

def flatten(list_of_lists):
    return [item for sublist in list_of_lists for item in sublist]

############ Path related things

def default_loadpaths():
    import subprocess
    process = subprocess.Popen([julia_cmd,"-e",
        'print(join([Pkg.Dir.path(),LOAD_PATH...],"\n"))'],
        stdout=subprocess.PIPE)
    process_stdout = process.communicate()[0]
    julia_loadpaths = process_stdout.decode('utf-8').split('\n')
    return hard_coded_loadpaths + julia_loadpaths


_loadpaths = default_loadpaths()
def loadpaths():
    for path in _loadpaths:
        yield normalise_path(path)

#TODO: Lookout for changes to LOADPATHS, and attempt to update our own loadpaths

### Manage the current working directory
_working_dirs = ["."] #Managed by Context()

def current_working_dir():
    global _working_dirs
    return _working_dirs[-1]

def normalise_path(path):
    if not os.path.isabs(path):
         path = os.path.abspath(os.path.join(current_working_dir(), path))
    return path

class Context():
    def __init__(self, working_dir):
       self.working_dir = normalise_path(working_dir)
    def __enter__(self):
        global _working_dirs
        _working_dirs.append(self.working_dir)
    def __exit__(self,type,value,traceback):
        global _working_dirs
        _working_dirs.pop()



########### Preprocessing (and includes)

@lru_cache(256)
def load_include(path):
    path = normalise_path(path)
    try:
        with open(path,"r") as fp:
            return fp.read()

    except Exception as e:
        if isinstance(e, IOError):    # FileNotFoundError on Py3.3+ inherits from IOError
            warn(IncludeNotFoundError(path,e))
            return "" #Failed to find include assume it is empty
        else:
            raise



def flatten_includes(text):
    past_includes =set()
    def inner_flatten(text):
        while(True): #Got to allow for for recursive includes
            changed=False
            def subsitute_include(string,loc, tokens):
                path=tokens[0][0][1:-1]
                if path in past_includes:
                    warn("Denied attempt to re-include "+path )
                    return "" #Avoid including something already included, (no infinite loops)
                else:
                    past_includes.add(path)
                    changed=True;
                    print("* expanding", path)
                    directory, file = os.path.split(path)
                    with Context(directory):
                        include_text = load_include(file)
                        return inner_flatten(include_text)


            pp_include = (pp.LineStart()
                        + pp.Literal("include").suppress()
                        + pp.nestedExpr(
                                content=pp.QuotedString('"')
                            ).addParseAction(subsitute_include)

                    )
            text = pp_include.transformString(text)

            if not(changed):
                return text
    return inner_flatten(text)


def preprocess(raw_text):
    #TODO: Not handling `requires` or `reloads` right now
    text=flatten_includes(raw_text)
    return text


############## Loading
#See also https://github.com/JuliaLang/julia/blob/d6df2a0b166d360b24f4cc3631a65e3cc5c56476/base/loading.jl




@lru_cache(256)
def load_module(module_name):
    import os.path

    for lpath in loadpaths():
        with Context(lpath):
            fn = os.path.join(lpath,module_name+".jl")
            try:

                with  open(fn,'r') as fp:
                    raw_text = fp.read()
                return preprocess(raw_text)
            except Exception as e:
                if isinstance(e, IOError):    # FileNotFoundError on Py3.3+ inherits from IOError
                    pass                #No problem try the next
                else:
                    raise


    warn(ModuleNotFoundError(module_name, loadpaths))
    return "" #Failed to find module, assume it is emot


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
    text = load_module(module_name)
    return syntax.get_exports(text)

def import_module(module_name):
    text = load_module(module_name)
    return [module_name+"."+id for id in syntax.get_nonexports(text)]

def using_module(module_name):
    return importall_module(module_name)+import_module(module_name)


def using_system_pseudomodules(imgpath, module_name):
    # Everything is slightly different to the normal path for using a module,
    # as we do not resolve the name into the path, and we do not want to fail silently
    with Context(os.path.dirname(imgpath)):
        with open(imgpath,"r") as fp:
            #warnings.filterwarnings("error") #HACK: to get warnings to throw
            text = preprocess(fp.read())
            exports = syntax.get_exports(text)
            nonexports =  [module_name+"."+id for id in syntax.get_nonexports(text)]

            #warnings.filterwarnings("default")
            return exports + nonexports

def using_system_pseudomodules_cached(module_name):
    cache_filename = os.path.join(cache_folder,"_"+module_name+"_cache.json")
    try:
        with open(cache_filename,"r") as fp:
           return json.load(fp)
    except Exception as e:
        if isinstance(e, IOError):    # FileNotFoundError on Py3.3+ inherits from IOError
            #recreate Cache
            if module_name=="Core":
                completions = using_system_pseudomodules(core_path, module_name)
            elif module_name=="Base":
                completions = using_system_pseudomodules(base_path, module_name)
            else:
                raise(ModuleNotFoundError(module_name,"system pseudo-modules"))

            with open(cache_filename,"w") as fp:
                json.dump(completions,fp)
            return completions
        else:
            raise


"""
Given some text, from the current file,
return all the completions -- ie all identifiers currently in scope
"""
def get_completions(main_text):
    with Context(os.curdir):
        main_text=preprocess(main_text)

        #TODO : this needs to be reorganised, probably mostly into the syntax module.
        #TODO : I suspect you can mix all the styles in one line. I am currently ignoring that possiblily
        #TODO : explict imports eg `import a.x`
        #TODO : relative import eg `importall .FFTW`
        def get_modules(import_type):
            pp_imp = (pp.Literal(import_type).suppress()
                    + pp.delimitedList(syntax.pp_identifier)
                    )

            parsed_imps = pp_imp.scanString(main_text)
            return syntax._matched_only(parsed_imps)

        completions=syntax.RESERVED_WORDS #Reseved words are always completable
        completions += syntax.get_nonexports(main_text)
        completions += using_system_pseudomodules_cached("Base")
        completions += using_system_pseudomodules_cached("Core")
        completions += flatten([using_module(mod) for mod in get_modules("using")])
        completions += flatten([importall_module(mod) for mod in get_modules("importall")])
        completions += flatten([import_module(mod) for mod in get_modules("import")])
        return set(completions)



###################testing
"""
import os
os.chdir("../samples")

def prl(ss):
    ss= list(ss)
    ss.sort()
    print(ss)


prl(get_completions(open("main.jl","r").read()))
print(preprocess(open("main.jl","r").read()))
"""

