/**
 * BizSaathi Design Tokens
 * Extracted from reference-ui design comp files (Main.dc.html, Catalog.dc.html, etc.)
 * 
 * These are the EXACT values from the design mockups.
 * Do not deviate unless updating the reference design itself.
 */

export const colors = {
  // Brand
  primary: '#0B6E5C',
  primaryHover: '#09594A',
  primaryLight: '#E4F1EC',
  primaryLighter: '#F2F9F6',
  
  // Text
  text: '#12201B',
  textMuted: '#5B6A64',
  textSecondary: '#42524B',
  
  // Backgrounds
  bgPage: '#F5F8F6',
  bgCard: '#fff',
  bgInput: '#fff',
  bgHover: '#F1F6F3',
  bgMuted: '#EEF2F0',
  
  // Borders
  border: '#E1E8E4',
  borderInput: '#CBD6D0',
  borderInputHover: '#D5DFDA',
  borderInputActive: '#B9C9C1',
  
  // Status colors
  success: '#0B6E5C',
  successBg: '#E4F1EC',
  warning: '#B45309',
  warningText: '#8A4B08',
  warningBg: '#FDEBD3',
  warningBgLight: '#FFF8EE',
  warningBorder: '#F0C48F',
  error: '#8A1F1F',
  errorBg: '#F6DADA',
  errorText: '#8E2B1F',
  errorBorder: '#F3B7B0',
  
  // Process/workflow colors
  workflowDone: '#0B6E5C',
  workflowCurrent: '#B45309',
  workflowUpcoming: '#CBD6D0',
  
  // Product placeholder colors (from catalog cards)
  placeholder1: '#E9DFC9',
  placeholder2: '#D9E4F0',
  placeholder3: '#C9D8E8',
  placeholder4: '#DDE7D0',
  placeholder5: '#EBD9C8',
  placeholder6: '#E6DDEA',
  
  // Overlays
  overlay: '#12201B',
  overlayLight: 'rgba(16,24,20,0.12)',
  overlayLighter: 'rgba(16,24,20,0.04)',
} as const;

export const typography = {
  fontFamily: "'Plus Jakarta Sans', system-ui, sans-serif",
  
  // Font sizes
  h1: '28px',
  h2: '17px',
  body: '14px',
  small: '13px',
  tiny: '12px',
  
  // Font weights
  regular: 400,
  medium: 500,
  semibold: 600,
  bold: 700,
  
  // Line heights
  lineHeightTight: 1.2,
  lineHeightNormal: 1.5,
  lineHeightRelaxed: 1.6,
  
  // Letter spacing
  letterSpacingTightest: '-.02em',
  letterSpacingTighter: '-.01em',
  letterSpacingNormal: '0',
  letterSpacingWider: '.01em',
  letterSpacingWidest: '.04em',
} as const;

export const spacing = {
  // Base spacing units (from design)
  xs: '6px',
  sm: '8px',
  md: '12px',
  lg: '16px',
  xl: '20px',
  '2xl': '24px',
  '3xl': '32px',
  '4xl': '40px',
  
  // Component-specific
  cardPadding: '20px',
  cardPaddingLarge: '28px',
  sectionGap: '24px',
  mainGap: '28px',
  
  // Gaps
  gapTiny: '4px',
  gapSmall: '8px',
  gapMedium: '12px',
  gapLarge: '16px',
  gapXLarge: '24px',
} as const;

export const borderRadius = {
  // EXACT border radius values from reference
  small: '9px',      // Brand logo square
  medium: '10px',    // Nav items, inputs
  large: '12px',     // Buttons
  card: '16px',      // Base card radius (with shadow becomes 18px visually)
  cardActual: '18px', // Cards with shadow
  pill: '99px',      // Tags, badges
  circle: '50%',     // Avatar, account button
  button: '12px',    // Primary/secondary buttons
  input: '10px',     // Form inputs
  modal: '14px',     // Dropdowns, modals
} as const;

export const shadows = {
  card: '0 1px 2px rgba(16,24,20,.04),0 6px 20px rgba(16,24,20,.03)',
  modal: '0 8px 28px rgba(16,24,20,.12)',
  none: 'none',
} as const;

export const components = {
  // Button heights
  buttonHeight: '44px',
  buttonHeightLarge: '56px',
  
  // Input heights
  inputHeight: '44px',
  
  // Nav item height
  navHeight: '44px',
  
  // Account button size
  accountButtonSize: '44px',
  
  // Brand logo size
  logoSize: '32px',
  
  // Workflow dot sizes
  dotSize: '22px',
  dotLine: '2px',
  
  // Max widths
  maxWidthContent: '1240px',
  maxWidthWide: '1360px',
  
  // Transitions
  transition: 'background .15s,border-color .15s,box-shadow .15s',
  transitionFast: '.15s',
} as const;

export const breakpoints = {
  mobile: '640px',
  tablet: '768px',
  desktop: '1024px',
  wide: '1280px',
} as const;
