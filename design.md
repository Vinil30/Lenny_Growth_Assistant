# Design

## Principles

The UI is built for product and growth operators who want answers quickly. It prioritizes reading, follow-up questions, visible grounding, and a clear artifact preview over decorative complexity.

## Information Architecture

- Left sidebar: product identity, provider indicator, new conversation, session history.
- Center pane: chat transcript, loading states, citations, latency diagnostics.
- Right pane: sandboxed Artifact Viewer for Markdown and HTML/CSS outputs.

## Interaction States

- Empty state invites the user to ask about Lenny's Podcast.
- Loading state makes retrieval/generation visible without exposing implementation detail.
- Error state shows actionable messages for missing index, database issues, and provider failures.
- Citations appear directly under grounded answers.

## Responsive Behavior

Desktop uses a three-column workspace. Narrow screens stack sidebar, chat, and artifact viewer so every control remains usable without horizontal scrolling.

## Accessibility

The page uses semantic landmarks, readable contrast, visible form controls, labels through context/ARIA, and keyboard-friendly buttons/forms. The artifact iframe has a title and is isolated from the parent UI.

## Decisions

The frontend is plain HTML/CSS/JS to keep setup simple. Cards are used only for individual messages, not page sections. The palette is restrained but not monochrome, with teal for action and a secondary violet accent reserved for contrast.
