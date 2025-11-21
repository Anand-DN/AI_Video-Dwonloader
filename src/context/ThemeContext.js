import React, { createContext, useContext, useEffect, useState } from "react";

const ThemeContext = createContext();

export function ThemeProvider({ children }) {
  const init = localStorage.getItem("ui_theme_v4") || "dark";
  const [theme, setTheme] = useState(init);

  useEffect(() => {
    localStorage.setItem("ui_theme_v4", theme);
    document.documentElement.setAttribute("data-theme", theme);
  }, [theme]);

  const toggle = () => setTheme((t) => (t === "dark" ? "light" : "dark"));

  return (
    <ThemeContext.Provider value={{ theme, toggle }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  return useContext(ThemeContext);
}
