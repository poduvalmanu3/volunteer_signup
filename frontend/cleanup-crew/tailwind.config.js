/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        "./app/**/*.{js,ts,jsx,tsx}",
        "./components/**/*.{js,ts,jsx,tsx}",
        "./context/**/*.{js,ts,jsx,tsx}",
        "./lib/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                primary: {
                    DEFAULT: "#1F7A63",
                    dark: "#176655",
                    light: "#2FA88A",
                },
                background: {
                    DEFAULT: "#F7F9F8",
                    subtle: "#EEF2F1",
                },
                text: {
                    primary: "#1A1A1A",
                    secondary: "#5F6C6B",
                    muted: "#8A9593",
                },
                border: {
                    DEFAULT: "#E3E7E5",
                },
                accent: {
                    DEFAULT: "#F4A261",
                },
            },
            fontFamily: {
                sans: [
                    "Inter",
                    "system-ui",
                    "-apple-system",
                    "BlinkMacSystemFont",
                    "sans-serif",
                ],
            },
        },
    },
    plugins: [],
};
