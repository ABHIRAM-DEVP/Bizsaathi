/**
 * BizSaathi Design Tokens - Extracted from PDF mockups
 * Source: BizSaathi - Web App UI.pdf
 * 
 * These values match the actual production design shown in the PDF
 */

export const colors = {
  // Primary brand color (teal/emerald)
  primary: '#0F766E',
  primaryHover: '#0D6B64',
  primaryLight: '#F0FDF9',
  primaryLighter: '#CCFBEF',
  
  // Text colors
  text: '#1A1D1F',
  textSecondary: '#6C7275',
  textMuted: '#9CA3AF',
  
  // Background colors  
  bgPage: '#F8F9FA',
  bgCard: '#FFFFFF',
  bgHover: '#F8F9FA',
  
  // Border colors
  border: '#E9ECEF',
  borderLight: '#E0E4E7',
  borderInput: '#D1D5DB',
  
  // Status colors
  success: '#10B981',
  successBg: '#D1FAE5',
  successBorder: '#6EE7B7',
  
  warning: '#F59E0B',
  warningBg: '#FEF3C7',
  warningBorder: '#FCD34D',
  
  error: '#EF4444',
  errorBg: '#FEE2E2',
  errorBorder: '#FCA5A5',
  
  info: '#3B82F6',
  infoBg: '#DBEAFE',
  infoBorder: '#93C5FD',
  
  // Badge colors
  badgeGreen: '#10B981',
  badgeGreenBg: '#D1FAE5',
  badgeOrange: '#F59E0B',
  badgeOrangeBg: '#FEF3C7',
  badgeRed: '#EF4444',
  badgeRedBg: '#FEE2E2',
  badgeGray: '#6B7280',
  badgeGrayBg: '#F3F4F6',
} as const;

export const typography = {
  fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
  
  // Font sizes (from PDF)
  h1: '32px',
  h2: '24px',
  h3: '20px',
  h4: '18px',
  body: '15px',
  small: '14px',
  tiny: '13px',
  
  // Font weights
  regular: 400,
  medium: 500,
  semibold: 600,
  bold: 700,
  
  // Line heights
  tight: 1.25,
  normal: 1.5,
  relaxed: 1.6,
} as const;

export const spacing = {
  // Base spacing scale
  xs: '4px',
  sm: '8px',
  md: '12px',
  lg: '16px',
  xl: '20px',
  '2xl': '24px',
  '3xl': '32px',
  '4xl': '40px',
  '5xl': '48px',
  
  // Component-specific
  cardPadding: '24px',
  sectionGap: '24px',
  pageGutter: '32px',
} as const;

export const borderRadius = {
  none: '0',
  sm: '4px',
  md: '6px',
  lg: '8px',
  xl: '12px',
  '2xl': '16px',
  full: '9999px',
  
  // Component-specific (from PDF)
  button: '8px',
  input: '8px',
  card: '12px',
  badge: '6px',
  avatar: '50%',
} as const;

export const shadows = {
  sm: '0 1px 2px rgba(0, 0, 0, 0.04)',
  md: '0 1px 3px rgba(0, 0, 0, 0.04), 0 4px 16px rgba(0, 0, 0, 0.02)',
  lg: '0 4px 6px rgba(0, 0, 0, 0.04), 0 10px 40px rgba(0, 0, 0, 0.06)',
  xl: '0 8px 16px rgba(0, 0, 0, 0.08), 0 20px 60px rgba(0, 0, 0, 0.08)',
  button: '0 1px 2px rgba(0, 0, 0, 0.08)',
  buttonHover: '0 4px 12px rgba(0, 0, 0, 0.12)',
} as const;

export const components = {
  // Button
  buttonHeight: '44px',
  buttonPadding: '0 20px',
  buttonRadius: '8px',
  
  // Input
  inputHeight: '44px',
  inputPadding: '0 16px',
  inputRadius: '8px',
  
  // Header
  headerHeight: '64px',
  headerPadding: '0 32px',
  
  // Nav
  navItemHeight: '40px',
  navItemPadding: '0 16px',
  navItemRadius: '6px',
  
  // Card
  cardRadius: '12px',
  cardPadding: '24px',
  
  // Badge/Tag
  badgeRadius: '6px',
  badgePadding: '4px 10px',
  
  // Avatar
  avatarSize: '40px',
  
  // Max widths
  maxWidthContent: '1200px',
  maxWidthWide: '1400px',
  
  // Transitions
  transition: '0.2s ease',
  transitionFast: '0.15s ease',
} as const;

export const breakpoints = {
  mobile: '640px',
  tablet: '768px',
  desktop: '1024px',
  wide: '1280px',
  ultraWide: '1536px',
} as const;
