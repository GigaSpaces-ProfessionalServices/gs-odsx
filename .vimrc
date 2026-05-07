" Enable returning to last editing position
au BufReadPost * if line("'\"") > 0 && line("'\"") <= line("$") | exe "normal! g'\"" | endif
" Enabling search highlighting
set hlsearch
" Setting TAB to 2 spaces
filetype plugin indent on
" On pressing tab, insert 2 spaces
set expandtab
" show existing tab with 2 spaces width
set tabstop=2
set softtabstop=2
" when indenting with '>', use 2 spaces width
set shiftwidth=2
if &diff
  colorscheme pablo
endif
" Enable true‑color support if your terminal/Vim supports it
if has("termguicolors")
  set termguicolors
endif

" Turn on syntax highlighting and pick a neutral base scheme
syntax on
colorscheme default      " or replace “default” with your favorite light/dark theme
set background=dark      " or “light” if you use a light theme

" Always redefine diff highlights to softer, pastel tones
highlight DiffAdd    guifg=NONE guibg=#335533 ctermfg=NONE ctermbg=22
highlight DiffChange guifg=NONE guibg=#554411 ctermfg=NONE ctermbg=136
highlight DiffDelete guifg=NONE guibg=#553333 ctermfg=NONE ctermbg=52
highlight DiffText   guifg=NONE guibg=#443355 ctermfg=NONE ctermbg=66

" Ensure your diffs use these colors even if you switch colorschemes
augroup DiffColors
  autocmd!
  autocmd ColorScheme * highlight DiffAdd    guifg=NONE guibg=#335533 ctermfg=NONE ctermbg=22
  autocmd ColorScheme * highlight DiffChange guifg=NONE guibg=#554411 ctermfg=NONE ctermbg=136
  autocmd ColorScheme * highlight DiffDelete guifg=NONE guibg=#553333 ctermfg=NONE ctermbg=52
  autocmd ColorScheme * highlight DiffText   guifg=NONE guibg=#443355 ctermfg=NONE ctermbg=66
augroup END
