# julia-vim-completions
Julia doesn't have good VIM completions to my knowledge.
You can get a little way using julia-vim, then turning on syntax competions based on highlighting.

But we want more.
In this repo that is being explored.

Currently, the focus is on YCM.
But there are other approaches

## YCM
https://github.com/Valloric/YouCompleteMe
This is Almost ready to go, (for first actual test)
it just needs the 

Do a rough Parse of the files and it's includes.
Its not a perfect parse, infact it is very poor.
The goal right now is get ~80% of completions that are expected.
The easy ones.
It will probably never find functions that are declared using macros.


Do a grep for TODO to find what is not done, yet.


## Staticly generated completions.
The Julia REPL can produce completions,
Create a julia script that imports your libraries,
then ask the Base.REPL what completions exist.
Current experiments on this are located in te _generated_with_julia_ folder



## Chaos Running Julia
Liverun execute as much code as possible, so that we do know the things in context, by askign the background running session.

I'm not sure why an approach like:


```lang=irc
10:41 < Frames> Why can't I have syntax completion in vim?...
10:44 < Frames> I am very tempted to make a hacky method that attempts to send
                every line to a REPL in the background, and catchs all
                exceptions and has a 5ms timeout (per line). and then asked the
                REPL for a list of completions.
11:03 < Frames> Or actually, shouldn't it just be liniking
https://github.com/JuliaLang/julia/blob/master/base/REPLCompletions.jl us to
                the completion list in vim?
```

wouldn't work.
But right now a bit busy to make something dynamic.
