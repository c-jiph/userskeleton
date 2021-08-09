This is a local shop for local people; there is nothing for you here.

	git clone https://github.com/c-jiph/userskeleton.git &&
		find userskeleton/ -maxdepth 1 -exec mv {} . \; &&
		rm -rf userskeleton/ &&
		git config --local user.email "" && 
		git config --local user.name "C-JiPH"

Add to .bashrc:
	
	echo "source ~/.bashrc-git" > ~/.bashrc

Add to .gitconfig

        [include]
            path = ~/.gitconfig-git

Install FZF if possible.

Install Vim Fugitive if possible:

	mkdir -p ~/.vim/pack/tpope/start
	cd ~/.vim/pack/tpope/start
	git clone https://tpope.io/vim/fugitive.git
	vim -u NONE -c "helptags fugitive/doc" -c q
