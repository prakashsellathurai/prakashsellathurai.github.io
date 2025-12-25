// @ts-check
import { fontFamily } from 'tailwindcss/defaultTheme'
import colors from 'tailwindcss/colors'
import forms from '@tailwindcss/forms'
import typography from '@tailwindcss/typography'

/** @type {import("tailwindcss/types").Config } */
module.exports = {
  content: [
    './node_modules/pliny/**/*.js',
    './app/**/*.{js,ts,jsx,tsx}',
    './pages/**/*.{js,ts,tsx}',
    './components/**/*.{js,ts,tsx}',
    './layouts/**/*.{js,ts,tsx}',
    './data/**/*.mdx',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      lineHeight: {
        11: '2.75rem',
        12: '3rem',
        13: '3.25rem',
        14: '3.5rem',
      },
      fontFamily: {
        sans: ['var(--font-lora)', ...fontFamily.sans],
      },
      colors: {
        primary: {
          50: '#f0f4f8',
          100: '#d9e2ec',
          200: '#bcccdc',
          300: '#9fb3c8',
          400: '#829ab1',
          500: '#3b5998',
          600: '#304a80',
          700: '#263b66',
          800: '#1b2b4d',
          900: '#101c33',
        },
        secondary: colors.slate,
        gray: colors.gray,
        brand: {
          black: '#212121', // Slightly softer black
          white: '#ffffff',
          accent: '#3b5998',
        },
      },
      zIndex: {
        60: '60',
        70: '70',
        80: '80',
      },
      typography: ({ theme }) => ({
        DEFAULT: {
          css: {
            color: theme('colors.brand.black'),
            a: {
              color: theme('colors.brand.black'),
              '&:hover': {
                color: theme('colors.primary.600'),
              },
              code: { color: theme('colors.primary.400') },
            },
            'h1,h2': {
              color: theme('colors.brand.black'),
              fontWeight: '700',
              letterSpacing: theme('letterSpacing.tight'),
            },
            h3: {
              color: theme('colors.brand.black'),
              fontWeight: '600',
            },
            code: {
              color: theme('colors.primary.500'),
            },
          },
        },
        invert: {
          css: {
            color: theme('colors.brand.white'),
            a: {
              color: theme('colors.brand.white'),
              '&:hover': {
                color: theme('colors.primary.400'),
              },
              code: { color: theme('colors.primary.400') },
            },
            'h1,h2,h3,h4,h5,h6': {
              color: theme('colors.brand.black'),
            },
          },
        },
      }),
    },
  },
  plugins: [
    forms,
    typography,
    ({ addBase, theme }) => {
      addBase({
        'a, button': {
          outlineColor: theme('colors.brand.black'),
          '&:focus-visible': {
            outline: '2px solid',
            borderRadius: theme('borderRadius.DEFAULT'),
            outlineColor: theme('colors.brand.black'),
          },
        },
      })
    },
  ],
}
