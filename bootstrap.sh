#!/bin/bash -x

. /etc/os-release
export NAME

function install() {
  local pkg_name="$1"
  local install_cmd="sudo apt-get install -y"

  case "$NAME" in
    *OpenWrt*)
      install_cmd="opkg install"
      case "$pkg_name" in
        fzf|mosh)
          return
          ;;
      esac
      ;;
  esac

  $install_cmd $pkg_name
}

function is_openwrt() {
  [[ "$NAME" == *OpenWrt* ]]
}

if is_openwrt ; then
  install bash
  install shadow_chsh
  chsh -s /bin/bash
fi

install git

cd

git clone https://github.com/c-jiph/userskeleton.git
find userskeleton/ -maxdepth 1 -exec mv {} . \;
rm -rf userskeleton/ &&
git config --local user.email ""
git config --local user.name "C-JiPH"

echo "source ~/.bashrc-git" >> ~/.bashrc
echo "source ~/.bashrc-git" >> ~/.bash_login
echo -e "[include]\n    path = ~/.gitconfig-git" >> .gitconfig

install vim

mkdir -p ~/.vim/pack/tpope/start
cd ~/.vim/pack/tpope/start
git clone https://tpope.io/vim/fugitive.git
vim -u NONE -c "helptags fugitive/doc" -c q

install tmux
install mosh
install fzf
