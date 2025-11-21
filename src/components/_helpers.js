// small helper utilities used by components

export function getYoutubeId(url) {
    try {
      const u = new URL(url);
      if (u.hostname.includes("youtu")) {
        // youtube.com/watch?v=... or youtu.be/...
        if (u.hostname.includes("youtu.be")) {
          return u.pathname.slice(1);
        }
        return u.searchParams.get("v");
      }
    } catch {
      return null;
    }
  }
  
  export function getThumbnailFromUrl(url) {
    const id = getYoutubeId(url);
    if (id) {
      return `https://img.youtube.com/vi/${id}/hqdefault.jpg`;
    }
    // fallback placeholder dataURI or remote placeholder
    return "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='640' height='360'><rect width='100%' height='100%' fill='%23222'/><text x='50%' y='50%' fill='%23fff' font-size='24' text-anchor='middle' dominant-baseline='middle'>No thumbnail</text></svg>";
  }
  