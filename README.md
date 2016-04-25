# julia-vim-omnicomplete
These are Omnicompletions for vim.
From julia.
Right now just a static list of completions, that does not update when you change your file.


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
