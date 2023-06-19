set title
set laststatus=2
set ruler
set ci
set pi
set ai
set mouse=a

set ignorecase
set smartcase
set swb=useopen

set pastetoggle=<C-P>

:set background=dark

if has("syntax")
  syn on
  filetype on
  au BufNewFile,BufRead *.maxj set filetype=java
endif

set cul
autocmd InsertEnter * set nocul
autocmd InsertLeave * set cul
