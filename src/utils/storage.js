export function loadHistoryFromStorage() {
  try {
    const data = localStorage.getItem("download_history");
    return data ? JSON.parse(data) : [];
  } catch (error) {
    console.error("Failed to load history:", error);
    return [];
  }
}

export function saveHistoryToStorage(history) {
  try {
    localStorage.setItem("download_history", JSON.stringify(history));
  } catch (error) {
    console.error("Failed to save history:", error);
  }
}
