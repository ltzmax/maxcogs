name: Bug Report
description: File a bug report
title: "[Bug]: "
labels: ["Status Pending"]
assignees:
  - ltzmax
body:
  - type: markdown
    attributes:
      value: |
        Hello, This is a bug report, please enter as much as details as possible. thank you.
  - type: input
    id: contact
    attributes:
      label: Your discord username
      description: Please enter your discord username so i can @ you if i need more informations about your bug.
      placeholder: ex. username#0001
    validations:
      required: true
  - type: textarea
    id: what-happened
    attributes:
      label: What happened?
      description: what did you expect to happen?
    validations:
      required: true
  - type: textarea
    id: traceback
    attributes:
      label: post your traceback here
      description: Please provide full traceback, this will help us.
    validations:
      required: true
  - type: dropdown
    id: cog
    attributes:
      label: What cog did you see the bug from?
      multiple: true
      options:
        - embeduptime
        - kitsune
        - nekos
        - onconnect
        - veryfun
        - waifu
    validations:
      required: true
