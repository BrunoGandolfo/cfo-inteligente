import { useState, useCallback } from 'react';
import type { Command } from '../types';

interface CommandBlockProps {
  command: Command;
  index: number;
}

function escapeHtml(str: string): string {
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

export function CommandBlock({ command, index }: CommandBlockProps) {
  const [copied, setCopied] = useState(false);
  const isComment = command.command.startsWith('#');

  const handleCopy = useCallback(() => {
    navigator.clipboard.writeText(command.command).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }, [command.command]);

  return (
    <div className={`cmd-block ${isComment ? 'cmd-comment' : ''}`}>
      <div className="cmd-header">
        <span className="cmd-desc">{command.description}</span>
        {!isComment && (
          <button
            className={`cmd-copy ${copied ? 'cmd-copied' : ''}`}
            onClick={handleCopy}
          >
            {copied ? '✓ Copiado' : 'Copiar'}
          </button>
        )}
      </div>
      <pre
        className="cmd-pre"
        id={`cmd-${index}`}
        dangerouslySetInnerHTML={{ __html: escapeHtml(command.command) }}
      />
    </div>
  );
}
