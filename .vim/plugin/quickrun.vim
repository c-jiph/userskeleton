function! SetExecutableBit()
	let fname = expand("%:p")
	checktime
	execute "au FileChangedShell " . fname . " :echo"
	silent !chmod a+x %
	checktime
	execute "au! FileChangedShell " . fname
endfunction
command! Xbit call SetExecutableBit()

function! SaveScript()
	let dir = $HOME."/vim-little-scripts/"
	let latest = dir."latest"
	if bufname('%') == ''
		if !isdirectory(dir)
			call mkdir(dir, "p")
		endif
		let file = dir.strftime('%y-%m-%d_%H:%M:%S.').w:interpreter_language[0]
		call append(0, "#!".w:interpreter_language[1])
		j
		execute "w ".file
		call SetExecutableBit()
		call system("ln -sf '".file."' '".latest."'")
		let w:interpreter_autosave = 1
	else
		if exists("w:interpreter_autosave")
			silent! w
		end
	end
endfunction

function! ExecuteInterpreter()
	let dir = $HOME."/vim-little-scripts/"
	let latest = dir."latest"
	if line('$') == 1 && getline(1) == '' && bufname('%') == ''
		if filereadable(latest)
			silent! execute "e ".resolve(latest)
			let w:interpreter_autosave = 1
			echo ''
			return
		else
			echo "No most recent script."
		endif
		return
	endif

	if !exists("w:interpreter_language")
		let language_map = {
			\ 'ruby'   : ['rb', '/usr/bin/ruby', 'ruby'],
			\ 'python' : ['py', '/usr/bin/python', 'python'],
			\ 'bash'   : ['sh', '/bin/bash', 'sh'],
			\ 'sh'     : ['sh', '/bin/sh', 'sh'] }

		let first_line = getline(1)
		for [lang_name, lang_details] in items(language_map)
			if match(first_line, lang_details[2]) != -1
				echo "Auto-detected language: ".lang_name
				let user_lang = lang_name
				break
			endif
		endfor
		
		if !exists("user_lang")
			let user_lang = input("Enter interpreter for window: ")
			if user_lang == ""
				echo ''
				return
			endif
		endif
		let w:interpreter_language = get(language_map, user_lang, [user_lang, "/usr/bin/".user_lang, user_lang])
	endif

	silent! call SaveScript()
	silent! call ExecuteBuffer()
	redraw!
endfunction

function! ExecuteBuffer()
	let oldbuf = bufnr('%')
	let exec = "%!".w:interpreter_language[1]
	if exists("w:interpreter_buffer") && bufexists(w:interpreter_buffer)
		execute "sb ".w:interpreter_buffer
		%d
		execute "sb ".oldbuf
		%y
		execute "sb ".w:interpreter_buffer
		normal p
		execute exec
		execute "sb ".oldbuf
	else
		execute 'set filetype='.w:interpreter_language[2]
		%y
		new
		set buftype=nofile
		normal p
		execute exec
		let exec_buf = bufnr('%')
		execute "sb ".oldbuf
		let w:interpreter_buffer = exec_buf
	endif
endfunction

map <F5> :call ExecuteInterpreter()<CR>
imap <F5> <ESC>:call ExecuteInterpreter()<CR>
