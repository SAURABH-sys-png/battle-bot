#!/usr/bin/env bash
# Terminal makeover for Ptyxis + bash. User-local only: no sudo, nothing outside $HOME.
#
# What it does:
#   1. Downloads starship, eza, bat, zoxide, fastfetch, lazygit (pinned releases from GitHub)
#      into ~/.local/bin
#   2. Writes ~/.config/starship.toml (two-line Tokyo-night prompt)
#   3. Adds a clearly marked block to ~/.bashrc (backup is made first)
#   4. Adds a "Tokyo Black" palette to Ptyxis and sets the Nerd Font
#
# Safe to re-run: the bashrc block is replaced, not duplicated.
# Undo:  cp ~/.bashrc.bak-before-terminal-makeover ~/.bashrc
set -euo pipefail

BIN="$HOME/.local/bin"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$BIN"

say() { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }

fetch() { # fetch <name> <url> : download + extract into $TMP/<name>
  local name=$1 url=$2
  mkdir -p "$TMP/$name"
  curl -fsSL --max-time 180 "$url" | tar xz -C "$TMP/$name"
}

say "Downloading tools"
fetch starship "https://github.com/starship/starship/releases/download/v1.27.0/starship-x86_64-unknown-linux-musl.tar.gz"
fetch eza      "https://github.com/eza-community/eza/releases/download/v0.23.5/eza_x86_64-unknown-linux-gnu.tar.gz"
fetch bat      "https://github.com/sharkdp/bat/releases/download/v0.26.1/bat-v0.26.1-x86_64-unknown-linux-musl.tar.gz"
fetch zoxide   "https://github.com/ajeetdsouza/zoxide/releases/download/v0.10.0/zoxide-0.10.0-x86_64-unknown-linux-musl.tar.gz"
fetch fastfetch "https://github.com/fastfetch-cli/fastfetch/releases/download/2.70.0/fastfetch-linux-amd64.tar.gz"
fetch lazygit  "https://github.com/jesseduffield/lazygit/releases/download/v0.66.2/lazygit_0.66.2_linux_x86_64.tar.gz"

say "Installing into $BIN"
install -m755 "$TMP/starship/starship" "$BIN/"
install -m755 "$TMP/eza/eza" "$BIN/"
install -m755 "$TMP"/bat/*/bat "$BIN/"
install -m755 "$TMP/zoxide/zoxide" "$BIN/"
install -m755 "$TMP"/fastfetch/*/usr/bin/fastfetch "$BIN/"
install -m755 "$TMP/lazygit/lazygit" "$BIN/"
for t in starship eza bat zoxide fastfetch lazygit; do
  printf '  %-10s %s\n' "$t" "$("$BIN/$t" --version | head -1)"
done

say "Writing ~/.config/starship.toml"
mkdir -p "$HOME/.config"
cat > "$HOME/.config/starship.toml" <<'EOF'
# Starship prompt: two-line, colourful, Tokyo-night palette (needs a Nerd Font)
"$schema" = 'https://starship.rs/config-schema.json'
add_newline = true
command_timeout = 800

format = """
[╭─](#414868)\
$os$username$hostname\
[](fg:#7aa2f7 bg:#1a1b26)$directory[](fg:#1a1b26)\
$git_branch$git_status\
$python$c$cpp$nodejs$rust$java$cmake\
$cmd_duration\
$line_break\
[╰─](#414868)$character"""

right_format = "$time"

[character]
success_symbol = "[❯](bold #9ece6a)"
error_symbol = "[❯](bold #f7768e)"

[os]
disabled = false
format = "[ $symbol ]($style)"
style = "bg:#7aa2f7 fg:#000000"
[os.symbols]
Ubuntu = ""
Linux = ""

[username]
show_always = true
style_user = "bg:#7aa2f7 fg:#000000 bold"
style_root = "bg:#f7768e fg:#000000 bold"
format = "[$user]($style)"

[hostname]
ssh_only = true
style = "bg:#7aa2f7 fg:#000000"
format = "[@$hostname ]($style)"

[directory]
style = "bg:#1a1b26 fg:#7dcfff bold"
format = "[ $path ]($style)[$read_only]($read_only_style)"
truncation_length = 4
truncation_symbol = "…/"
read_only = " "
[directory.substitutions]
"Documents" = "󰈙"
"Downloads" = ""
"battlecode" = "󰊗"

[git_branch]
symbol = ""
style = "fg:#bb9af7"
format = " [$symbol $branch]($style)"

[git_status]
style = "fg:#e0af68"
format = "[( $all_status$ahead_behind)]($style)"

[cmd_duration]
min_time = 2000
style = "fg:#e0af68"
format = " [󱦟 $duration]($style)"

[time]
disabled = false
time_format = "%H:%M"
style = "fg:#565f89"
format = "[ $time]($style)"

[python]
symbol = ""
style = "fg:#e0af68"
format = " [$symbol $version( \\($virtualenv\\))]($style)"
[c]
symbol = ""
style = "fg:#7aa2f7"
format = " [$symbol $version]($style)"
[cpp]
disabled = false
symbol = ""
style = "fg:#7aa2f7"
format = " [$symbol $version]($style)"
[cmake]
symbol = "△"
style = "fg:#9ece6a"
format = " [$symbol $version]($style)"
[nodejs]
symbol = ""
style = "fg:#9ece6a"
format = " [$symbol $version]($style)"
[rust]
symbol = ""
style = "fg:#ff9e64"
format = " [$symbol $version]($style)"
[java]
symbol = ""
style = "fg:#f7768e"
format = " [$symbol $version]($style)"
EOF

say "Updating ~/.bashrc (backup: ~/.bashrc.bak-before-terminal-makeover)"
[ -f "$HOME/.bashrc.bak-before-terminal-makeover" ] || cp "$HOME/.bashrc" "$HOME/.bashrc.bak-before-terminal-makeover"
# remove any previous copy of our block so re-running doesn't duplicate it
sed -i '/^# >>> terminal makeover >>>$/,/^# <<< terminal makeover <<<$/d' "$HOME/.bashrc"
cat >> "$HOME/.bashrc" <<'EOF'

# >>> terminal makeover >>>
# Everything below is guarded with `command -v`, so it's safe if a tool is missing.

# History: bigger, shared across terminals, no duplicates
HISTSIZE=50000
HISTFILESIZE=100000
HISTCONTROL=ignoreboth:erasedups
shopt -s histappend cmdhist checkwinsize globstar autocd cdspell 2>/dev/null
PROMPT_COMMAND="history -a${PROMPT_COMMAND:+; $PROMPT_COMMAND}"

# Case-insensitive, menu-style tab completion
bind 'set completion-ignore-case on'
bind 'set show-all-if-ambiguous on'
bind 'set colored-stats on'
bind 'set colored-completion-prefix on'
bind '"\e[A": history-search-backward'   # type a prefix, then Up/Down
bind '"\e[B": history-search-forward'

# Colourful man pages
export MANPAGER="less -R --use-color -Dd+r -Du+b"

# Prompt / smarter cd / fuzzy finder
command -v starship >/dev/null && eval "$(starship init bash)"
command -v zoxide   >/dev/null && eval "$(zoxide init bash --cmd cd)"
if command -v fzf >/dev/null; then
  eval "$(fzf --bash 2>/dev/null)"   # Ctrl-R history, Ctrl-T files, Alt-C dirs
  export FZF_DEFAULT_OPTS="--height=40% --layout=reverse --border=rounded --info=inline \
--color=bg:#000000,bg+:#1a1b26,fg:#c0caf5,fg+:#c0caf5,hl:#7aa2f7,hl+:#7dcfff,info:#e0af68,prompt:#bb9af7,pointer:#f7768e,marker:#9ece6a,spinner:#7dcfff,header:#565f89,border:#414868"
  if command -v fd >/dev/null; then
    export FZF_DEFAULT_COMMAND='fd --type f --hidden --exclude .git'
    export FZF_CTRL_T_COMMAND="$FZF_DEFAULT_COMMAND"
  fi
  command -v bat >/dev/null && export FZF_CTRL_T_OPTS="--preview 'bat -n --color=always {}'"
fi

# Nicer ls / cat
if command -v eza >/dev/null; then
  alias ls='eza --icons --group-directories-first'
  alias ll='eza -lh --icons --git --group-directories-first'
  alias la='eza -lah --icons --git --group-directories-first'
  alias lt='eza --tree --level=2 --icons'
else
  alias ll='ls -lh --color=auto'
  alias la='ls -lah --color=auto'
fi
if command -v bat >/dev/null; then
  alias cat='bat --paging=never --style=plain'
  alias catp='bat'
fi
command -v lazygit >/dev/null && alias lg='lazygit'
alias grep='grep --color=auto'
alias ..='cd ..'
alias ...='cd ../..'
alias gs='git status -sb'
alias gl='git log --oneline --graph --decorate -15'
alias v='nvim'

# Greeting on new terminals (skipped inside tmux)
if [ -n "$PS1" ] && [ -z "$TMUX" ] && command -v fastfetch >/dev/null; then fastfetch; fi
# <<< terminal makeover <<<
EOF
bash -n "$HOME/.bashrc" && echo "  .bashrc syntax OK"

say "Ptyxis: black palette + Nerd Font"
PAL="$HOME/.local/share/org.gnome.Ptyxis/palettes"
mkdir -p "$PAL"
{
  echo "[Palette]"; echo "Name=Tokyo Black"
  for mode in Dark Light; do
    cat <<EOF

[$mode]
Foreground=#c0caf5
Background=#000000
Cursor=#c0caf5
Color0=#15161e
Color1=#f7768e
Color2=#9ece6a
Color3=#e0af68
Color4=#7aa2f7
Color5=#bb9af7
Color6=#7dcfff
Color7=#a9b1d6
Color8=#414868
Color9=#f7768e
Color10=#9ece6a
Color11=#e0af68
Color12=#7aa2f7
Color13=#bb9af7
Color14=#7dcfff
Color15=#c0caf5
EOF
  done
} > "$PAL/tokyo-black.palette"

if command -v gsettings >/dev/null; then
  UUID="$(gsettings get org.gnome.Ptyxis default-profile-uuid | tr -d "'")"
  P="org.gnome.Ptyxis.Profile:/org/gnome/Ptyxis/Profiles/$UUID/"
  gsettings set org.gnome.Ptyxis use-system-font false
  gsettings set org.gnome.Ptyxis font-name 'JetBrainsMono Nerd Font 12'
  gsettings set "$P" palette 'Tokyo Black'
  gsettings set "$P" scrollback-lines 20000
  gsettings set "$P" limit-scrollback false
else
  echo "  gsettings not found; pick the palette + font in Ptyxis preferences instead."
fi

say "Done. Close this terminal and open a new one (or run: exec bash)"
