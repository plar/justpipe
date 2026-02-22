/** Platform detection utilities (evaluated once at module load). */

export const isMac =
  typeof navigator !== 'undefined' && navigator.platform?.toUpperCase().includes('MAC')

/** Display-friendly modifier key label. */
export const modKey = isMac ? '\u2318' : 'Ctrl'

/** Display-friendly modifier key name (e.g. "Cmd" on Mac). */
export const modKeyName = isMac ? 'Cmd' : 'Ctrl'
