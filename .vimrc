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

function! CleverTab()
if strpart( getline('.'), 0, col('.')-1 ) =~ '^\s*$'
        return "\<Tab>"
else
        return "\<C-N>"
endfunction

inoremap <Tab> <C-R>=CleverTab()<CR>


:set background=dark

syn on
filetype on
au BufNewFile,BufRead *.maxj set filetype=java

set cul
autocmd InsertEnter * set nocul
autocmd InsertLeave * set cul
