
Here we will generate cTags using Reflection from julia.

When  jltags.jl given a filename, it outputs tags for all identifiers we believe to be inscope from modules that were `using`ed or `importall`ed.
Unlike regex based solutions, this does capture identifiers declared using macros.





