"""Chunk-filled solid icons (fill=currentColor, no stroke) — bold geometric
glyphs that sit well on Risograph color blocks. Authored simple/heavy on
purpose. Merged over the base stroke set in this look's manifest."""

RISO_ICONS = {
    "pencil": ('<path d="M16.7 3.3a1 1 0 0 1 1.4 0l2.6 2.6a1 1 0 0 1 0 1.4l-1.7 1.7-4-4 1.7-1.7z"/>'
               '<path d="M14.6 5.4l4 4L8 20H4v-4L14.6 5.4z"/>'),
    "pen-nib": ('<path d="M3 21l1.6-5.2L15 5.4 18.6 9 8.2 19.4 3 21z"/>'
                '<path d="M16.4 4l1.3-1.3a1.7 1.7 0 0 1 2.4 0l1.2 1.2a1.7 1.7 0 0 1 0 2.4L20 7.6 16.4 4z"/>'),
    "note": '<path d="M4 3h16v9.5L12.5 20H4V3z"/><path d="M12.5 20v-7.5H20L12.5 20z" fill="#000" opacity=".22"/>',
    "book": ('<path d="M5 3.5A1.5 1.5 0 0 1 6.5 2H19v15.5H6.5A1.5 1.5 0 0 0 5 19V3.5z"/>'
             '<path d="M6.5 18.5H19V20.5H6.5a1 1 0 0 1 0-2z"/>'),
    "scissors": ('<circle cx="6" cy="6.8" r="2.7"/><circle cx="6" cy="17.2" r="2.7"/>'
                 '<path d="M8.2 8.4 20 15.8l-1.2 1.9L7 10.3zM8.2 15.6 20 8.2l-1.2-1.9L7 13.7z"/>'),
    "brush": ('<path d="M15.5 2.6 21.4 8.5l-4.5 4.5-5.9-5.9 4.5-4.5z"/>'
              '<path d="M9.9 8.5l5.6 5.6-3 3c-1.1 1.1-2.7 1.2-3.6.3-.7-.7-.2-1.7-.8-2.7-.5-.9-1.6-.8-2.1-1.7-.6-1 .2-2 1-2.8l2.9-1.9z"/>'),
    "arrow-right": '<path d="M4 10.8h12.2l-4.7-4.7L13 4.6l7.2 7.2L13 19l-1.5-1.5 4.7-4.7H4z"/>',
    "book-open": ('<path d="M11 6.2C9 4.7 6 4.2 3 4.8V19c3-.6 6-.1 8 1.4V6.2z"/>'
                  '<path d="M13 6.2C15 4.7 18 4.2 21 4.8V19c-3-.6-6-.1-8 1.4V6.2z" opacity=".82"/>'),
    "star": '<path d="M12 2l2.95 6.3 6.85.8-5.05 4.7 1.35 6.8L12 17.7 5.9 20.6l1.35-6.8L2.2 9.1l6.85-.8L12 2z"/>',
    "flag": '<path d="M5 2h2v20H5V2z"/><path d="M7 3h11l-2.5 3.5L18 10H7V3z"/>',
}
