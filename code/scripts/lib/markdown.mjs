const ESCAPE = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };

function escapeHtml(s) {
  if (!s) return '';
  return String(s).replace(/[&<>"']/g, c => ESCAPE[c]);
}

function escapeAttr(s) {
  if (!s) return '';
  return String(s).replace(/[&"]/g, c => ESCAPE[c]);
}

export class MarkdownRenderer {
  render(content) {
    const [defs, body] = this._extractFootnotes(content);
    return this._renderBlocks(body, defs);
  }

  _extractFootnotes(text) {
    const defs = {};
    const lines = text.split('\n');
    const result = [];
    let i = 0;

    while (i < lines.length) {
      const line = lines[i];
      const m = line.match(/^\[\^([\w-]+)\]:\s*(.*)/);
      if (m) {
        const id = m[1];
        let content = m[2];
        i++;
        while (i < lines.length) {
          const next = lines[i];
          if (next === '' || /^[ \t]/.test(next)) {
            content += next === '' ? '\n\n' : ' ' + next.trim();
            i++;
          } else {
            break;
          }
        }
        defs[id] = content.trim();
      } else {
        result.push(line);
        i++;
      }
    }
    return [defs, result.join('\n')];
  }

  _renderBlocks(text, defs) {
    const lines = text.split('\n');
    const blocks = [];
    let i = 0;

    while (i < lines.length) {
      const line = lines[i];
      if (line.trim() === '') { i++; continue; }

      if (line.trimStart().startsWith('>')) {
        const quoteLines = [];
        while (i < lines.length && lines[i].trimStart().startsWith('>')) {
          quoteLines.push(lines[i].replace(/^>\s?/, ''));
          i++;
        }
        blocks.push({ type: 'blockquote', content: quoteLines.join('\n') });
        continue;
      }

      const paraLines = [];
      while (i < lines.length && lines[i].trim() !== '') {
        paraLines.push(lines[i]);
        i++;
      }
      blocks.push({ type: 'paragraph', content: paraLines.join(' ').trim() });
    }

    return blocks.map(b => this._renderBlock(b, defs)).join('\n');
  }

  _renderBlock(block, defs) {
    switch (block.type) {
      case 'blockquote':
        return `<blockquote>\n${this._renderBlocks(block.content, defs)}\n</blockquote>`;
      case 'paragraph':
        return `<p>${this._renderInline(block.content, defs)}</p>`;
      default:
        return '';
    }
  }

  _renderInline(text, defs) {
    let result = '';
    let i = 0;

    while (i < text.length) {
      const codeMatch = text.slice(i).match(/^`([^`]*)`/);
      if (codeMatch) {
        result += `<code>${codeMatch[1]}</code>`;
        i += codeMatch[0].length;
        continue;
      }

      const fnMatch = text.slice(i).match(/^\[\^([\w-]+)\]/);
      if (fnMatch) {
        const id = fnMatch[1];
        if (defs[id] !== undefined) {
          result += `<a class="sidenote-number" href="#sn-${id}">${id}</a><span class="sidenote" id="sn-${id}"> ${this._renderInline(defs[id], defs)}</span>`;
        } else {
          result += `[^${id}]`;
        }
        i += fnMatch[0].length;
        continue;
      }

      const linkMatch = text.slice(i).match(/^\[([^\]]*)\]\(([^)]+)\)/);
      if (linkMatch) {
        const linkText = linkMatch[1];
        const urlPart = linkMatch[2];
        let url, title;
        const titleMatch = urlPart.match(/^(\S+)\s+"([^"]*)"\s*$/);
        if (titleMatch) {
          url = titleMatch[1];
          title = titleMatch[2];
        } else {
          url = urlPart;
        }
        const titleAttr = title ? ` title="${escapeAttr(title)}"` : '';
        result += `<a href="${escapeAttr(url)}"${titleAttr}>${this._renderInline(linkText, defs)}</a>`;
        i += linkMatch[0].length;
        continue;
      }

      const autoMatch = text.slice(i).match(/^<([^>\s]+)>/);
      if (autoMatch) {
        const url = autoMatch[1];
        result += `<a href="${escapeAttr(url)}">${escapeHtml(url)}</a>`;
        i += autoMatch[0].length;
        continue;
      }

      const boldMatch = text.slice(i).match(/^\*\*([^*]+)\*\*/);
      if (boldMatch) {
        result += `<strong>${this._renderInline(boldMatch[1], defs)}</strong>`;
        i += boldMatch[0].length;
        continue;
      }

      const italicMatch = text.slice(i).match(/^\*([^*]+)\*/);
      if (italicMatch) {
        result += `<em>${this._renderInline(italicMatch[1], defs)}</em>`;
        i += italicMatch[0].length;
        continue;
      }

      const bareMatch = text.slice(i).match(/^https?:\/\/[^\s<>\]\)]+/);
      if (bareMatch) {
        let url = bareMatch[0];
        url = url.replace(/[.,;:!?]+$/, '');
        if (url) {
          result += `<a href="${escapeAttr(url)}">${escapeHtml(url)}</a>`;
        } else {
          result += escapeHtml(text[i]);
          i++;
          continue;
        }
        i += bareMatch[0].length;
        continue;
      }

      if (text[i] === '\\' && i + 1 < text.length) {
        result += text[i + 1];
        i += 2;
        continue;
      }

      result += escapeHtml(text[i]);
      i++;
    }

    return result;
  }
}
