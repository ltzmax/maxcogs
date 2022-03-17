name: Bug report
about: Create a report to help us improve
title: [BUG]
labels: Status Pending
assignees: ltzmax
body:
  - type: dropdown
    id: cog
    attributes:
      label: Cog
      description: Which cog has this bug occured in?
      options:
        - EmbedUptime
        - Kitsune
        - Nekos
        - OnConnect
        - VeryFun
    validations:
      required: true
  - type: input
    id: details
    attributes:
      label: Details
      description: Can you tell exactly what happened? give as much as details as possible
    validations:
      required: true
  - type: input
    id: discord_user_info
    attributes:
      label: Discord User Information
      description: "What is your Discord username? username#1234"
    validations:
      required: true
  - type: textarea
    id: logs
    attributes:
      label: Post your traceback here.
      description: Please copy every traceback you got in your logs from the cog you're reporting bug from.
      render: py
    validations: 
      required: false
  - type: input
    id: repro
    attributes:
      label: Reproduction
      description: Anything else?
    validations:
      required: false
