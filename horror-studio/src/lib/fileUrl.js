// Converts a local absolute path (Windows or POSIX) to a local-file:// URL
// served by the custom protocol registered in electron/main.js.
export function fileUrl(p) {
  if (!p) return '';
  // Normalize backslashes -> forward slashes
  const norm = String(p).replace(/\\/g, '/');
  // Ensure single leading slash so URL parses to "/C:/..." which we strip in main
  const withSlash = norm.startsWith('/') ? norm : '/' + norm;
  return 'local-file://' + encodeURI(withSlash);
}
