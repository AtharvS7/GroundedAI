'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Paperclip, ArrowUp } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useChatStore } from '@/store/chatStore';
import { sendQuery, checkHealth } from '@/lib/api';
import { getConfidenceLevel, truncate } from '@/lib/utils';
import TopBar from '@/components/layout/TopBar';
import type { ChatMessage, CitationObject } from '@/types';

export default function ChatPage() {
  const {
    conversations, activeConversationId, createConversation, addMessage,
    isContextInspectorOpen, selectedMessageId, setSelectedMessage,
  } = useChatStore();

  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [ollamaOnline, setOllamaOnline] = useState<boolean | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const activeConv = conversations.find((c) => c.id === activeConversationId);
  const messages = activeConv?.messages || [];
  const selectedMsg = messages.find((m) => m.id === selectedMessageId);

  useEffect(() => {
    checkHealth().then((h) => setOllamaOnline(h.ollama)).catch(() => setOllamaOnline(false));
  }, []);

  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  const handleTextareaInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    const ta = e.target;
    ta.style.height = 'auto';
    ta.style.height = Math.min(ta.scrollHeight, 160) + 'px';
  };

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    let convId = activeConversationId;
    if (!convId) convId = createConversation();

    const userMsg: ChatMessage = {
      id: crypto.randomUUID(), role: 'user', content: input.trim(),
      timestamp: new Date().toISOString(),
    };
    addMessage(convId!, userMsg);
    setInput('');
    if (textareaRef.current) { textareaRef.current.style.height = 'auto'; }

    setIsLoading(true);
    try {
      const { response } = await sendQuery({ query: userMsg.content, conversation_id: convId || undefined });
      const aiMsg: ChatMessage = {
        id: crypto.randomUUID(), role: 'assistant', content: response.answer,
        timestamp: new Date().toISOString(),
        citations: response.citations, confidence_score: response.confidence_score,
        retrieval_time_ms: response.retrieval_time_ms,
        generation_time_ms: response.generation_time_ms,
        chunks_used: response.chunks_used, refusal: response.refusal,
      };
      addMessage(convId!, aiMsg);
    } catch (err) {
      const errorMsg: ChatMessage = {
        id: crypto.randomUUID(), role: 'assistant',
        content: 'Sorry, an error occurred. Please check that the backend is running and Ollama is available.',
        timestamp: new Date().toISOString(), refusal: true,
      };
      addMessage(convId!, errorMsg);
    } finally { setIsLoading(false); }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); }
  };

  return (
    <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
      {/* Main Chat Area */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', background: '#0A0C10' }}>
        <TopBar />

        {/* Messages */}
        <div style={{ flex: 1, overflow: 'auto', padding: '24px 40px' }}>
          {messages.length === 0 ? (
            /* Empty State */
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', gap: 16 }}>
              <div style={{
                width: 64, height: 64, borderRadius: 18,
                background: 'linear-gradient(135deg, #6C63FF, #3B82F6)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 28, fontWeight: 700, color: '#fff',
              }}>G</div>
              <h2 style={{ fontSize: 22, fontWeight: 700, color: '#E6EDF3', margin: 0 }}>
                Ask anything about your documents
              </h2>
              <p style={{ color: '#8B949E', fontSize: 14 }}>
                Upload documents first, then ask questions grounded in your data.
              </p>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginTop: 8 }}>
                {['What are the key findings?', 'Summarize the main points', 'What does section 3 say?', 'Compare the two reports'].map((s) => (
                  <button key={s} onClick={() => { setInput(s); }}
                    style={{
                      padding: '14px 18px', background: 'rgba(22,27,34,0.75)',
                      backdropFilter: 'blur(16px)', border: '1px solid rgba(48,54,61,0.6)',
                      borderRadius: 12, color: '#E6EDF3', fontSize: 13, cursor: 'pointer',
                      textAlign: 'left', transition: 'all 0.15s',
                    }}
                    onMouseEnter={(e) => { e.currentTarget.style.borderColor = '#6C63FF'; }}
                    onMouseLeave={(e) => { e.currentTarget.style.borderColor = 'rgba(48,54,61,0.6)'; }}
                  >{s}</button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((msg) => (
              <motion.div key={msg.id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.2 }}
                style={{
                  display: 'flex', justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
                  marginBottom: 16,
                }}
              >
                {msg.role === 'user' ? (
                  <div style={{
                    maxWidth: '70%', padding: '12px 16px',
                    background: 'linear-gradient(135deg, #6C63FF, #3B82F6)',
                    borderRadius: '14px 14px 4px 14px', color: '#fff', fontSize: 14, lineHeight: 1.7,
                    boxShadow: '0 0 12px rgba(108,99,255,0.2)',
                  }}>{msg.content}</div>
                ) : (
                  <div
                    onClick={() => setSelectedMessage(msg.id)}
                    style={{
                      maxWidth: '80%', padding: 16, cursor: 'pointer',
                      backdropFilter: 'blur(16px)', background: 'rgba(22,27,34,0.75)',
                      border: `1px solid ${selectedMessageId === msg.id ? '#6C63FF' : 'rgba(48,54,61,0.6)'}`,
                      borderRadius: '4px 14px 14px 14px', transition: 'border-color 0.15s',
                    }}
                  >
                    {/* Header: avatar + confidence */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <div style={{
                          width: 24, height: 24, borderRadius: 8,
                          background: 'linear-gradient(135deg, #6C63FF, #3B82F6)',
                          display: 'flex', alignItems: 'center', justifyContent: 'center',
                          fontSize: 10, fontWeight: 700, color: '#fff',
                        }}>G</div>
                        <span style={{ fontSize: 13, fontWeight: 600, color: '#E6EDF3' }}>GroundedAI</span>
                      </div>
                      {msg.confidence_score !== undefined && !msg.refusal && (
                        <span style={{
                          fontSize: 11, fontWeight: 600, padding: '3px 10px', borderRadius: 999,
                          color: getConfidenceLevel(msg.confidence_score).color,
                          background: getConfidenceLevel(msg.confidence_score).bg,
                          display: 'flex', alignItems: 'center', gap: 4,
                        }}>
                          <span style={{
                            width: 6, height: 6, borderRadius: '50%',
                            background: getConfidenceLevel(msg.confidence_score).color,
                          }} />
                          {Math.round(msg.confidence_score * 100)}% confident
                        </span>
                      )}
                    </div>

                    {/* Answer text */}
                    <div style={{ fontSize: 14, lineHeight: 1.7, color: '#E6EDF3', whiteSpace: 'pre-wrap' }}>
                      {msg.content}
                    </div>

                    {/* Citations */}
                    {msg.citations && msg.citations.length > 0 && (
                      <div style={{ marginTop: 12, borderTop: '1px solid #21262D', paddingTop: 10 }}>
                        <div style={{ fontSize: 12, color: '#8B949E', marginBottom: 6 }}>
                          Sources ({msg.citations.length})
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                          {msg.citations.slice(0, 3).map((c, i) => (
                            <div key={i} style={{
                              background: '#161B22', borderLeft: '3px solid #6C63FF',
                              borderRadius: 8, padding: '8px 12px',
                            }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                                <span style={{ fontSize: 12, fontWeight: 600, color: '#E6EDF3' }}>
                                  {truncate(c.source_filename, 30)}
                                </span>
                                <span style={{
                                  fontSize: 10, color: '#8B949E', background: '#0F1117',
                                  padding: '2px 6px', borderRadius: 999,
                                }}>p.{c.page_number}</span>
                              </div>
                              {/* Relevance bar */}
                              <div style={{ height: 3, background: '#21262D', borderRadius: 3, marginBottom: 4 }}>
                                <div style={{
                                  height: '100%', borderRadius: 3, width: `${c.relevance_score * 100}%`,
                                  background: 'linear-gradient(90deg, #6C63FF, #3B82F6)',
                                }} />
                              </div>
                              <div style={{ fontSize: 11, color: '#484F58', fontStyle: 'italic' }}>
                                {truncate(c.chunk_preview, 100)}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Meta */}
                    <div style={{ marginTop: 8, fontSize: 11, color: '#484F58' }}>
                      {msg.retrieval_time_ms && `Retrieval: ${msg.retrieval_time_ms}ms`}
                      {msg.generation_time_ms && ` · Generation: ${msg.generation_time_ms}ms`}
                    </div>
                  </div>
                )}
              </motion.div>
            ))
          )}

          {/* Typing indicator */}
          {isLoading && (
            <div style={{ display: 'flex', justifyContent: 'flex-start', marginBottom: 16 }}>
              <div style={{
                padding: 16, backdropFilter: 'blur(16px)', background: 'rgba(22,27,34,0.75)',
                border: '1px solid rgba(48,54,61,0.6)', borderRadius: '4px 14px 14px 14px',
                display: 'flex', gap: 6,
              }}>
                {[0, 1, 2].map((i) => (
                  <div key={i} style={{
                    width: 8, height: 8, borderRadius: '50%', background: '#6C63FF',
                    animation: `dot-pulse 1.2s ease-in-out infinite ${i * 0.2}s`,
                  }} />
                ))}
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div style={{
          padding: '16px 40px 24px', borderTop: '1px solid #21262D',
          background: 'rgba(10,12,16,0.95)', backdropFilter: 'blur(12px)',
        }}>
          <div style={{
            backdropFilter: 'blur(16px)', background: 'rgba(22,27,34,0.75)',
            border: '1px solid rgba(48,54,61,0.6)', borderRadius: 14,
            padding: '12px 16px', display: 'flex', alignItems: 'flex-end', gap: 12,
            transition: 'border-color 0.18s',
          }}>
            <textarea
              ref={textareaRef} value={input} onChange={handleTextareaInput}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question about your documents..."
              rows={1}
              style={{
                flex: 1, background: 'transparent', border: 'none', outline: 'none',
                color: '#E6EDF3', fontSize: 14, resize: 'none', lineHeight: 1.5,
                maxHeight: 160, fontFamily: "'Inter', sans-serif",
              }}
            />
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              {/* Ollama status */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 11, color: '#8B949E' }}>
                <div style={{
                  width: 6, height: 6, borderRadius: '50%',
                  background: ollamaOnline ? '#10B981' : '#EF4444',
                }} />
                {ollamaOnline ? 'Online' : 'Offline'}
              </div>
              {/* Send */}
              <button
                onClick={handleSend}
                disabled={!input.trim() || isLoading}
                style={{
                  width: 36, height: 36, borderRadius: 10, border: 'none',
                  background: input.trim() && !isLoading ? 'linear-gradient(135deg, #6C63FF, #3B82F6)' : '#21262D',
                  color: input.trim() && !isLoading ? '#fff' : '#484F58',
                  cursor: input.trim() && !isLoading ? 'pointer' : 'not-allowed',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  transition: 'all 0.18s',
                }}
              >
                <ArrowUp size={18} />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Context Inspector */}
      <AnimatePresence>
        {isContextInspectorOpen && (
          <motion.div
            initial={{ width: 0, opacity: 0 }} animate={{ width: 320, opacity: 1 }}
            exit={{ width: 0, opacity: 0 }} transition={{ duration: 0.2 }}
            style={{
              background: '#0F1117', borderLeft: '1px solid #21262D',
              overflow: 'hidden', flexShrink: 0,
            }}
          >
            <div style={{ padding: 16 }}>
              <h3 style={{ fontSize: 14, fontWeight: 600, color: '#E6EDF3', marginBottom: 16 }}>
                Context Inspector
              </h3>
              {selectedMsg && selectedMsg.role === 'assistant' ? (
                <div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: '#E6EDF3', marginBottom: 12 }}>
                    Retrieved Chunks ({selectedMsg.chunks_used || 0})
                  </div>
                  {selectedMsg.citations?.map((c, i) => (
                    <div key={i} style={{
                      background: '#161B22', borderLeft: '3px solid #6C63FF',
                      borderRadius: 8, padding: '10px 12px', marginBottom: 8,
                    }}>
                      <div style={{ fontSize: 12, fontWeight: 600, color: '#E6EDF3' }}>
                        {c.source_filename}
                      </div>
                      <div style={{ fontSize: 10, color: '#8B949E', marginTop: 2 }}>p.{c.page_number}</div>
                      <div style={{ fontSize: 11, color: '#484F58', marginTop: 4, fontStyle: 'italic' }}>
                        {truncate(c.chunk_preview, 150)}
                      </div>
                    </div>
                  ))}
                  <div style={{ fontSize: 11, color: '#484F58', marginTop: 12 }}>
                    Retrieval time: {selectedMsg.retrieval_time_ms}ms
                  </div>
                </div>
              ) : (
                <p style={{ color: '#484F58', fontSize: 13, textAlign: 'center', marginTop: 40 }}>
                  Select an AI message to inspect its context
                </p>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
