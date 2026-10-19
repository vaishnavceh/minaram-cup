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
  const [theme, setThemeState] = useState<Theme>('ucl');

  const setTheme = (_t: Theme) => {
    setThemeState('ucl');
    localStorage.setItem('minaram_theme', 'ucl');
  };

  const toggleTheme = () => setTheme('ucl');

  useEffect(() => {
    localStorage.setItem('minaram_theme', 'ucl');
    const root = document.documentElement;
    root.classList.add('theme-ucl');
    root.classList.remove('theme-classic');
  }, [theme]);

  return (
    <ThemeContext.Provider value={{ theme, setTheme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => useContext(ThemeContext);
