This is a local shop for local people; there is nothing for you here.

	git clone https://github.com/c-jiph/userskeleton.git &&
		find userskeleton/ -maxdepth 1 -exec mv {} . \; &&
		rm -rf userskeleton/ &&
		git config --local user.email "" && 
		git config --local user.name "C-JiPH"

Add to .bashrc:
	
	source ~/.bashrc-git

Add to .gitconfig

        [include]
            path = ~/.gitconfig-git

Install FZF if possible.
