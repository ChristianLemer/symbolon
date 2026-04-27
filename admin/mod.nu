# Token Dashboard — admin commands
#
# Scripted setup for project administration (GitHub, etc.). Idempotent —
# safe to re-run.
#
# Install (in your nu config or one-off):
#   use /path/to/token-dashboard/admin
#
# Common commands:
#   admin gh project create   # create the GitHub Project and link it to this repo
#
# Run `help admin` for the full command list.

export use gh
