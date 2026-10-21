# Design tokens — #148

Source of brand hues: official Centro Change CSS, verified 2026-10-21. CSS implementation: `frontend/premium/src/style.css`.

| Token | Value | Use |
|---|---|---|
| `--blue` | `#3899eb` | primary action, focus, calendar booking |
| `--blue-dark` | `#1f7ecf` | stronger blue accents |
| `--blue-soft` | `#edf7ff` | selected navigation, light surfaces |
| `--ink` | `#253347` | readable application text, derived neutral |
| `--muted` | `#718098` | metadata, derived neutral |
| `--line` | `#e6eaf0` | dividers, derived neutral |
| spacing | 8/14/18/22/34px common intervals | compact operations density |
| radii | 8–15px | buttons, cards, dialogs |
| desktop shell | 242px sidebar, 70px topbar | Agenda-first navigation |
| mobile | breakpoint 760px, 390×844 tested | overlay menu, two-column metric cards |

Italian interface labels, `GG/MM/AAAA` and `HH:mm` presentation, EUR `it-IT` formatting, and `Europe/Rome` current date are part of the design contract. The server accepts unchanged canonical ISO-like date/time strings. Contrasts and assistive technology audit across all states remain **NOT_VERIFIED**; visual checks only used Chromium screenshots.
