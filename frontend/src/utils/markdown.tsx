import DOMPurify from 'dompurify';

/**
 * Simple markdown renderer that converts markdown text to HTML.
 * Supports: bold, italic, code, lists, links, and emojis.
 */
export function renderMarkdown(text: string): string {
  if (!text) return '';

  let html = text;

  // Escape HTML first (except for our markdown conversions)
  html = html
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  // Code blocks (```)
  html = html.replace(/```(\w*)\n?([\s\S]*?)```/g, (_, lang, code) => {
    return `<pre class="bg-gray-800 text-gray-100 p-3 rounded-lg my-2 overflow-x-auto text-xs"><code>${code.trim()}</code></pre>`;
  });

  // Inline code (`)
  html = html.replace(/`([^`]+)`/g, '<code class="bg-gray-200 text-gray-800 px-1.5 py-0.5 rounded text-xs font-mono">$1</code>');

  // Bold (**text** or __text__)
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong class="font-semibold">$1</strong>');
  html = html.replace(/__(.+?)__/g, '<strong class="font-semibold">$1</strong>');

  // Italic (*text* or _text_)
  html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');
  html = html.replace(/_([^_]+)_/g, '<em>$1</em>');

  // Headers (## Header)
  html = html.replace(/^### (.+)$/gm, '<h4 class="font-semibold text-base mt-3 mb-1">$1</h4>');
  html = html.replace(/^## (.+)$/gm, '<h3 class="font-semibold text-lg mt-3 mb-1">$1</h3>');
  html = html.replace(/^# (.+)$/gm, '<h2 class="font-bold text-xl mt-3 mb-2">$1</h2>');

  // Unordered lists (- item or * item)
  html = html.replace(/^[-*] (.+)$/gm, '<li class="ml-4 list-disc">$1</li>');

  // Numbered lists (1. item)
  html = html.replace(/^\d+\. (.+)$/gm, '<li class="ml-4 list-decimal">$1</li>');

  // Wrap consecutive <li> items in <ul> or <ol>
  html = html.replace(/(<li class="ml-4 list-disc">[\s\S]*?<\/li>)(\n?<li class="ml-4 list-disc">[\s\S]*?<\/li>)*/g, (match) => {
    return `<ul class="my-2 space-y-1">${match}</ul>`;
  });
  html = html.replace(/(<li class="ml-4 list-decimal">[\s\S]*?<\/li>)(\n?<li class="ml-4 list-decimal">[\s\S]*?<\/li>)*/g, (match) => {
    return `<ol class="my-2 space-y-1">${match}</ol>`;
  });

  // Links [text](url)
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:underline">$1</a>');

  // Line breaks (double newline = paragraph)
  html = html.replace(/\n\n/g, '</p><p class="mb-2">');
  html = html.replace(/\n/g, '<br />');

  // Wrap in paragraph
  html = `<p class="mb-2">${html}</p>`;

  // Clean up empty paragraphs
  html = html.replace(/<p class="mb-2"><\/p>/g, '');
  html = html.replace(/<p class="mb-2">(<[uo]l)/g, '$1');
  html = html.replace(/(<\/[uo]l>)<\/p>/g, '$1');
  html = html.replace(/<p class="mb-2">(<pre)/g, '$1');
  html = html.replace(/(<\/pre>)<\/p>/g, '$1');
  html = html.replace(/<p class="mb-2">(<h[234])/g, '$1');
  html = html.replace(/(<\/h[234]>)<\/p>/g, '$1');

  // Sanitize the HTML
  return DOMPurify.sanitize(html, {
    ALLOWED_TAGS: ['p', 'br', 'strong', 'em', 'code', 'pre', 'ul', 'ol', 'li', 'a', 'h2', 'h3', 'h4'],
    ALLOWED_ATTR: ['href', 'target', 'rel', 'class'],
  });
}

/**
 * React component that renders markdown content safely.
 */
interface MarkdownContentProps {
  content: string;
  className?: string;
}

export function MarkdownContent({ content, className = '' }: MarkdownContentProps) {
  const html = renderMarkdown(content);

  return (
    <div
      className={`markdown-content ${className}`}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}
