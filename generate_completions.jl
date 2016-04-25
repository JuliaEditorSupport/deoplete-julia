comps = UTF8String[]
for aa in [collect('A':'Z') collect('a':'z')]
    
    append!(comps,Base.REPLCompletions.completions(string(aa),1)[1])
end
open("julia-omni.vim", "w") do fh
    write(fh, "\" this file is a automatically generated list of default keywords. including functions etc defined in base\n")
    write(fh,  "syn keyword basicLanguageKeywords ")
    write(fh,join(comps," "))
end
