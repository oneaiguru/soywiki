
"let s:client_script = "zenwiki_client " . shellescape($DRB_URI) . " "
let s:client_script = "ruby -Ilib bin/zenwiki_client " . shellescape($DRB_URI) . " "
let s:save_command = s:client_script . "save_page "
let s:list_pages_command = s:client_script . "list_pages "
let s:load_page_command = s:client_script . "load_page "

func! s:create_main_window() 
  setlocal modifiable 
  let s:main_window_bufnr = bufnr('%')
  call s:main_window_mappings()
  write
endfunction


func! s:save_page()
  let page = join(getline(1,'$'), "\n")
  call system(s:save_command, page)
  echo "Saved"
  redraw
endfunc

func! s:list_pages()
  call s:page_list_window()
endfunc


" -------------------------------------------------------------------------------
" select Page

func! s:get_page_list()
  redraw
  let res = system(s:list_pages_command)
  let s:pages = split(res, "\n", '')
endfunction


function! s:page_list_window()
  call s:get_page_list()
  topleft split page-list-buffer
  setlocal buftype=nofile
  setlocal noswapfile
  setlocal modifiable
  resize 1
  inoremap <silent> <buffer> <cr> <Esc>:call <SID>select_page()<CR> 
  inoremap <silent> <buffer> <esc> <Esc>:q<cr>
  setlocal completefunc=CompletePage
  " c-p clears the line
  call setline(1, "Select page: ")
  normal $
  call feedkeys("a\<c-x>\<c-u>\<c-p>", 't')
endfunction

function! CompletePage(findstart, base)
  if !exists("s:pages")
    call s:get_page_list()
  endif
  if a:findstart
    " locate the start of the word
    let line = getline('.')
    let start = col('.') - 1
    while start > 0 && line[start - 1] =~ '\a'
      let start -= 1
    endwhile
    return start
  else
    " find pages matching with "a:base"
    let res = []
    for m in s:pages
      if m =~ a:base . '\c'
        call add(res, m)
      endif
    endfor
    return res
  endif
endfun

function! s:select_page()
  let page = get(split(getline(line('.')), ": "), 1)
  close
  " check if page is a real page
  if (index(s:pages, page) == -1)
    return
  endif

  let s:page = page
  " load page into buffer
  let command = s:load_page_command . shellescape(s:page)
  write!
  let res = system(command)
  1,$delete
  put! =res
  execute "normal Gdd\<c-y>" 
  normal G
  write
  normal z.
  redraw
  echom "Current page: ". s:page 
endfunction

"------------------------------------------------------------------------

func! s:main_window_mappings()
  " these are global
  noremap <leader>m :call <SID>list_pages()<CR>
  " todo mapping for new page (don't just create a new vim buffer)
endfunc 

autocmd BufWritePost zenwiki-buffer call s:save_page() 

" syntax color camelcase
match Comment /\C\<[A-Z][a-z]\+[A-Z]\w*\>/


call s:create_main_window()



