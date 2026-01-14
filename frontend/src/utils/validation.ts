/**
 * Validate if a string is a valid URL
 */
export const isValidUrl = (url: string): boolean => {
  try {
    const urlObj = new URL(url);
    return urlObj.protocol === 'http:' || urlObj.protocol === 'https:';
  } catch {
    return false;
  }
};

/**
 * Extract URLs from text (one per line or comma-separated)
 */
export const extractUrlsFromText = (text: string): string[] => {
  // Split by newlines or commas
  const lines = text.split(/[\n,]/).map((line) => line.trim()).filter(Boolean);
  return lines;
};

/**
 * Remove duplicate URLs from an array
 */
export const removeDuplicateUrls = (urls: string[]): string[] => {
  return [...new Set(urls)];
};

/**
 * Parse HTML bookmark file and extract URLs
 * Supports Chrome and Firefox bookmark HTML format
 */
export const parseBookmarkHtml = (html: string): { url: string; title: string }[] => {
  const bookmarks: { url: string; title: string }[] = [];

  // Create a temporary DOM element to parse HTML
  const parser = new DOMParser();
  const doc = parser.parseFromString(html, 'text/html');

  // Find all <a> tags (bookmark links)
  const links = doc.querySelectorAll('a[href]');

  links.forEach((link) => {
    const href = link.getAttribute('href');
    const title = link.textContent?.trim() || '';

    if (href && isValidUrl(href)) {
      bookmarks.push({ url: href, title });
    }
  });

  return bookmarks;
};

/**
 * Validate file type (check if it's an HTML file)
 */
export const isValidBookmarkFile = (file: File): boolean => {
  return file.type === 'text/html' || file.name.endsWith('.html');
};

/**
 * Validate file size (max 10MB)
 */
export const isValidFileSize = (file: File, maxSizeMB: number = 10): boolean => {
  const maxSizeBytes = maxSizeMB * 1024 * 1024;
  return file.size <= maxSizeBytes;
};

/**
 * Mask API token for display (show first 3 and last 3 characters)
 */
export const maskApiToken = (token: string): string => {
  if (!token || token.length < 10) {
    return '••••••••';
  }
  return `${token.slice(0, 3)}...${token.slice(-3)}`;
};
