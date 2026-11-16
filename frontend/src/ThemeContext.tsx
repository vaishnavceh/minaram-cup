import React, { createContext, useContext, useState, useEffect } from 'react';

export type Theme = 'legends' | 'classic';

interface ThemeContextValue {
  theme: Theme;
  setTheme: (t: Theme) => void;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextValue>({
  theme: 'legends',
  setTheme: () => {},
  toggleTheme: () => {},
});

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [theme, setThemeState] = useState<Theme>('legends');

  const setTheme = (t: Theme) => {
    setThemeState(t);
    localStorage.setItem('minaram_theme', t);
  };

  const toggleTheme = () => setTheme(theme === 'legends' ? 'classic' : 'legends');

  useEffect(() => {
    localStorage.setItem('minaram_theme', 'legends');
    const root = document.documentElement;
    root.classList.add('theme-legends');
    root.classList.remove('theme-ucl', 'theme-classic');
  }, [theme]);

  return (
    <ThemeContext.Provider value={{ theme, setTheme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => useContext(ThemeContext);
