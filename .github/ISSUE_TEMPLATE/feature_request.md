name: Feature request
about: Suggest an idea for this project
title: [Suggestion]
labels: Status Pending
assignees: ltzmax
body:
  - type: dropdown
    id: cog
    attributes:
      label: Cog
      description: Which cog do you make feature request for?
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
      description: "Describe your request:"
    validations:
      required: true
