import React, { createContext, useContext, useState, useEffect } from 'react';

export type Theme = 'ucl' | 'classic';

interface ThemeContextValue {
  theme: Theme;
  setTheme: (t: Theme) => void;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextValue>({
  theme: 'ucl',
  setTheme: () => {},
  toggleTheme: () => {},
});

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [theme, setThemeState] = useState<Theme>(() => {
    const stored = localStorage.getItem('minaram_theme');
    return (stored === 'classic' || stored === 'ucl') ? stored : 'ucl';
  });

  const setTheme = (t: Theme) => {
    setThemeState(t);
    localStorage.setItem('minaram_theme', t);
  };

  const toggleTheme = () => setTheme(theme === 'ucl' ? 'classic' : 'ucl');

  useEffect(() => {
    const root = document.documentElement;
    if (theme === 'ucl') {
      root.classList.add('theme-ucl');
      root.classList.remove('theme-classic');
    } else {
      root.classList.add('theme-classic');
      root.classList.remove('theme-ucl');
    }
  }, [theme]);

  return (
    <ThemeContext.Provider value={{ theme, setTheme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => useContext(ThemeContext);
