import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./App.css";
import { DownloadProvider } from "./context/DownloadContext";
import { ThemeProvider } from "./context/ThemeContext";

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <ThemeProvider>
      <DownloadProvider>
        <App />
      </DownloadProvider>
    </ThemeProvider>
  </React.StrictMode>
);
