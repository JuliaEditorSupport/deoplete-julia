**Deprecation Notice:** 
This package is not being maintained.
I recommend moving to using something based on the Language Server Protocol,
and using (LanguageServer.jl)[https://github.com/JuliaEditorSupport/LanguageServer.jl].
I hear https://github.com/autozimu/LanguageClient-neovim works with deomplete, or with nvim-completion-manager.
https://github.com/JuliaEditorSupport/LanguageServer.jl/wiki/Vim-and-Neovim


# Deoplete-Julia 
This package supplements julia-vim by providing syntax completions, through Deoplete.
This is for [NeoVim](https://neovim.io/), rather than orginal Vim.
The transition from Vim to neovim is fairly seamless these days -- it supports basically all vim plugins etc.



Check out the video of it working. (Click the image below)
[![asciicast](https://asciinema.org/a/688g8iyhj1idrtz8ooptr6iso.png)](https://asciinema.org/a/688g8iyhj1idrtz8ooptr6iso)
(Yes, I know that code is not actually correct. Recording demos is hard.)


## Requirements:

 - [NeoVim](https://github.com/neovim/neovim) - like vim, but newer
 - [Deoplete](https://github.com/Shougo/deoplete.nvim) - the completion engine that this is a plugin for
 - [Julia](https://github.com/JuliaLang/julia) -- the julia programming language
    - v0.5 is the only version strongly supported, 
	- support for 0.6+ will not be coming
    - This is not compatible with 0.4
	- Because this interacts with the AST and reflection on a tightish level it is dependent on julia's internal representations.
    	- It may have been better to display marginally less information, but be more stable, by depending only on the docstrings (/internal help), and on the result of `methods` 

### Suggested

 - [julia-vim](https://github.com/JuliaLang/julia-vim) - syntax highlighting and LaTeX/Unicode replacement
    - deoplete-julia does not at all interact with julia-vim, and that is kinda a nice thing. They do different task but work together well.
	- julia-vim runs just fine in NeoVim

## Installation
Use your prefered Vim package manager, eg Vundle.

```vimscript
Plugin 'Shougo/deoplete.nvim'
Plugin 'JuliaEditorSupport/deoplete-julia'
```

Do not forget to enable deoplete in your `.nvimrc` if you've not used it before.

```vimscript
let g:deoplete#enable_at_startup = 1
```


The first time a you `using` a module, will take a little longer as it caches the names from that module (in particular the first time you edit a file at all will take longer, as it builds the cache of names for `Base`).
This cache should rebuild when the module is editted.

You shouldn't notice the cache being generated -- it won't hang, but julia completions will not work til it is done.


