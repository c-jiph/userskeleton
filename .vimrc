set title
set laststatus=2
set ci
set pi
set ai
set mouse=a

set ignorecase
set smartcase
set swb=useopen

let g:ConqueTerm_CWInsert = 1
let g:ConqueTerm_CloseOnEnd = 1


map <F7> :new<CR>:ConqueTerm bash<CR>
imap <F7> :new<CR><ESC>:ConqueTerm bash<CR>


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
