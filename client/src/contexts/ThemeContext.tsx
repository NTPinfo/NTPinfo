import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

type Theme = 'light' | 'dark';

interface ThemeContextType {
  theme: Theme;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

const THEME_STORAGE_KEY = 'ntpinfo-theme';

export const ThemeProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [theme, setTheme] = useState<Theme>(() => {
    // Check localStorage first, then system preference
    const storedTheme = localStorage.getItem(THEME_STORAGE_KEY) as Theme | null;
    let initialTheme: Theme = 'light';
    
    if (storedTheme === 'light' || storedTheme === 'dark') {
      initialTheme = storedTheme;
    }
    
    // Apply theme immediately to prevent flash
    const root = document.documentElement;
    root.setAttribute('data-theme', initialTheme);
    
    return initialTheme;
  });

  useEffect(() => {
    // Apply theme to document root
    const root = document.documentElement;
    root.setAttribute('data-theme', theme);
    
    // Update color-scheme meta tag
    const metaThemeColor = document.querySelector('meta[name="color-scheme"]');
    if (metaThemeColor) {
      metaThemeColor.setAttribute('content', theme);
    } else {
      const meta = document.createElement('meta');
      meta.name = 'color-scheme';
      meta.content = theme;
      document.head.appendChild(meta);
    }
    
    // Save to localStorage
    localStorage.setItem(THEME_STORAGE_KEY, theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prevTheme) => (prevTheme === 'light' ? 'dark' : 'light'));
  };

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = (): ThemeContextType => {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

