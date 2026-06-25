/**
 * Formats a number of bytes into a human-readable string.
 */
export const formatBytes = (bytes: number, decimals: number = 2): string => {
  if (bytes === 0) return "0 Bytes";
  
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ["Bytes", "KB", "MB", "GB", "TB"];
  
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + " " + sizes[i];
};

/**
 * Formats date string to local readable format
 */
export const formatLocalDate = (dateStr: string): string => {
  try {
    const d = new Date(dateStr);
    return d.toLocaleString("en-IN", { hour12: false });
  } catch (e) {
    return dateStr;
  }
};
