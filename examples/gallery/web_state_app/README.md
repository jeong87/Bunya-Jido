# Pulse Counter Web App

Clicking the increment control creates an `increment` action. The reducer owns
the authoritative count, `loadMessage` derives a side-effect-backed message,
and `renderCounter` presents the resulting state.

The documented interaction loop gives this miniature an honest ordered
behavioral scenario.
