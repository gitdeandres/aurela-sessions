## Docker shortcuts
alias dc='docker compose'
alias dc-enter-web='dc exec web bash'

## Django management via UV
alias uvmanage='uv run -- manage.py'
alias djmigrate='uvmanage migrate'
alias djmakemigrations='uvmanage makemigrations'
alias djshell='uvmanage shell'
alias djtest='uv run pytest'