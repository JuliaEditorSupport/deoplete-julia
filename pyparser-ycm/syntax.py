import pyparsing as pp


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


#TODO Use actual scoping, to determine what is at global scope, rather than looking for things lont intented

def get_vars(top_scoped_text):
    #TODO match var ' a'
    #TODO match var `b` in `a,b=2,3`
    #TODO match var `b` in `a=2;b=2`
    #TODO match var `(a,b)`
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

