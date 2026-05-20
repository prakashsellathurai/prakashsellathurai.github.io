export function parseFrontmatter(content) {
  const match = content.match(/^---\r?\n([\s\S]*?)\r?\n(?:---|\.\.\.)\r?\n?/);
  if (!match) {
    return { data: {}, content };
  }

  const yaml = match[1];
  const body = content.slice(match[0].length);
  const data = {};

  for (const line of yaml.split('\n')) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;

    const colonIdx = trimmed.indexOf(':');
    if (colonIdx === -1) continue;

    const key = trimmed.slice(0, colonIdx).trim();
    let raw = trimmed.slice(colonIdx + 1).trim();

    if (!key) continue;

    if ((raw.startsWith("'") && raw.endsWith("'")) ||
        (raw.startsWith('"') && raw.endsWith('"'))) {
      data[key] = raw.slice(1, -1);
    } else if (raw.startsWith('[') && raw.endsWith(']')) {
      try {
        data[key] = JSON.parse(raw.replace(/'/g, '"'));
      } catch {
        data[key] = [];
      }
    } else if (raw.toLowerCase() === 'true') {
      data[key] = true;
    } else if (raw.toLowerCase() === 'false') {
      data[key] = false;
    } else if (/^\d+(\.\d+)?$/.test(raw)) {
      data[key] = Number(raw);
    } else {
      data[key] = raw;
    }
  }

  return { data, content: body };
}
