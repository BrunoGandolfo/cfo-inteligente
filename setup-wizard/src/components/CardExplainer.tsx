import { useState, useCallback, useRef, useEffect, useMemo } from 'react';
import { useCardChat } from '../hooks/useCardChat';
import { findVideosForComponent, getYouTubeUrl, getYouTubeThumbnail } from '../data/videos';
import type { DetectionResult } from '../types';
import type { VideoEntry } from '../data/videos';

interface CardExplainerProps {
  component: DetectionResult;
  onClose: () => void;
}

export function CardExplainer({ component, onClose }: CardExplainerProps) {
  const { messages, loading, error, send, clear } = useCardChat(component.id);
  const [input, setInput] = useState('');
  const [activeTab, setActiveTab] = useState<'chat' | 'videos'>('chat');
  const chatEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const videos = useMemo(
    () => findVideosForComponent(component.id, component.name),
    [component.id, component.name]
  );

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  // Auto-ask initial explanation if no messages yet
  useEffect(() => {
    if (messages.length === 0 && !loading) {
      send(
        `Explicame que es "${component.name}" y para que lo necesito en mi setup de IA local con dual RTX 5090. Mi nivel es de desarrollador de software que no sabe mucho de hardware.`,
        {
          name: component.name,
          status: component.status,
          message: component.message,
          details: component.details,
        }
      );
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleSend = useCallback(() => {
    if (!input.trim() || loading) return;
    send(input.trim(), {
      name: component.name,
      status: component.status,
      message: component.message,
      details: component.details,
    });
    setInput('');
  }, [input, loading, send, component]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }, [handleSend]);

  return (
    <div className="explainer-panel">
      <div className="explainer-header">
        <div className="explainer-title-row">
          <span className="explainer-icon">📖</span>
          <span className="explainer-title">Aprender: {component.name}</span>
        </div>
        <div className="explainer-actions">
          <div className="explainer-tabs">
            <button
              className={`explainer-tab ${activeTab === 'chat' ? 'explainer-tab-active' : ''}`}
              onClick={() => setActiveTab('chat')}
            >
              Chat
            </button>
            {videos.length > 0 && (
              <button
                className={`explainer-tab ${activeTab === 'videos' ? 'explainer-tab-active' : ''}`}
                onClick={() => setActiveTab('videos')}
              >
                Videos ({videos.length})
              </button>
            )}
          </div>
          {messages.length > 2 && activeTab === 'chat' && (
            <button className="explainer-clear" onClick={clear} title="Reiniciar conversacion">
              Reiniciar
            </button>
          )}
          <button className="explainer-close" onClick={onClose} title="Cerrar">
            ✕
          </button>
        </div>
      </div>

      {activeTab === 'chat' && (
        <>
          <div className="explainer-chat">
            {messages.map((msg, i) => (
              <div key={i} className={`chat-msg chat-${msg.role}`}>
                <div className="chat-msg-label">
                  {msg.role === 'user' ? 'Tu' : 'Claude'}
                </div>
                <div className="chat-msg-content">
                  {msg.content.split('\n').map((line, j) => (
                    <p key={j}>{line || '\u00A0'}</p>
                  ))}
                </div>
              </div>
            ))}

            {loading && (
              <div className="chat-msg chat-assistant">
                <div className="chat-msg-label">Claude</div>
                <div className="chat-msg-content chat-typing">
                  <span className="typing-dot" />
                  <span className="typing-dot" />
                  <span className="typing-dot" />
                </div>
              </div>
            )}

            {error && (
              <div className="chat-error">Error: {error}</div>
            )}

            <div ref={chatEndRef} />
          </div>

          <div className="explainer-input-row">
            <textarea
              ref={inputRef}
              className="explainer-input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Pregunta lo que quieras sobre este componente..."
              rows={2}
              disabled={loading}
            />
            <button
              className="explainer-send"
              onClick={handleSend}
              disabled={!input.trim() || loading}
            >
              Enviar
            </button>
          </div>

          <div className="explainer-suggestions">
            {messages.length <= 2 && (
              <>
                <span className="suggestions-label">Sugerencias:</span>
                <button className="suggestion-chip" onClick={() => {
                  setInput('Como se relaciona esto con las RTX 5090?');
                  inputRef.current?.focus();
                }}>
                  Relacion con RTX 5090
                </button>
                <button className="suggestion-chip" onClick={() => {
                  setInput('Que pasa si no lo tengo instalado?');
                  inputRef.current?.focus();
                }}>
                  Si no lo tengo?
                </button>
                <button className="suggestion-chip" onClick={() => {
                  setInput('Como lo instalo paso a paso?');
                  inputRef.current?.focus();
                }}>
                  Como instalarlo
                </button>
                {videos.length > 0 && (
                  <button className="suggestion-chip" onClick={() => setActiveTab('videos')}>
                    Ver videos
                  </button>
                )}
              </>
            )}
          </div>
        </>
      )}

      {activeTab === 'videos' && (
        <div className="video-section">
          <div className="video-grid">
            {videos.map((video, i) => (
              <VideoCard key={i} video={video} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function VideoCard({ video }: { video: VideoEntry }) {
  const url = getYouTubeUrl(video);
  const thumbnail = getYouTubeThumbnail(video);

  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      className="video-card"
    >
      <div className="video-thumbnail">
        {thumbnail ? (
          <img src={thumbnail} alt={video.title} loading="lazy" />
        ) : (
          <div className="video-thumbnail-placeholder">
            <span className="video-play-icon">▶</span>
            <span className="video-yt-icon">YouTube</span>
          </div>
        )}
        <span className={`video-lang-badge ${video.lang === 'es' ? 'lang-es' : 'lang-en'}`}>
          {video.lang === 'es' ? 'ES' : 'EN'}
        </span>
      </div>
      <div className="video-info">
        <div className="video-title">{video.title}</div>
        {video.channel && (
          <div className="video-channel">{video.channel}</div>
        )}
      </div>
    </a>
  );
}
