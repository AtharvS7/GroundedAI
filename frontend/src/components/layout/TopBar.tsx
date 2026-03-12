'use client';

import { PanelRight, FileText } from 'lucide-react';
import { useChatStore } from '@/store/chatStore';
import { useDocumentStore } from '@/store/documentStore';

export default function TopBar() {
  const { isContextInspectorOpen, toggleContextInspector, conversations, activeConversationId } = useChatStore();
  const { documents } = useDocumentStore();

  const activeConv = conversations.find((c) => c.id === activeConversationId);
  const indexedCount = documents.filter((d) => d.status === 'indexed').length;

  return (
    <div style={{
      height: 56, background: 'rgba(10,12,16,0.9)', backdropFilter: 'blur(12px)',
      borderBottom: '1px solid #21262D', display: 'flex', alignItems: 'center',
      justifyContent: 'space-between', padding: '0 24px', flexShrink: 0,
    }}>
      <div style={{ fontSize: 15, fontWeight: 600, color: '#E6EDF3' }}>
        {activeConv?.title || 'New Chat'}
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        {/* Model Badge */}
        <span style={{
          fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: '#8B949E',
          background: '#161B22', padding: '4px 10px', borderRadius: 999,
          border: '1px solid #21262D',
        }}>
          mistral:7b
        </span>

        {/* Docs Count */}
        <span style={{
          display: 'flex', alignItems: 'center', gap: 4,
          fontSize: 12, color: '#10B981',
          background: 'rgba(16,185,129,0.1)', padding: '4px 10px', borderRadius: 999,
        }}>
          <FileText size={12} />
          {indexedCount} docs
        </span>

        {/* Context Inspector Toggle */}
        <button
          onClick={toggleContextInspector}
          style={{
            background: 'none', border: 'none',
            color: isContextInspectorOpen ? '#6C63FF' : '#8B949E',
            cursor: 'pointer', padding: 4, borderRadius: 6,
            transition: 'color 0.15s',
          }}
          onMouseEnter={(e) => { e.currentTarget.style.color = '#6C63FF'; }}
          onMouseLeave={(e) => { if (!isContextInspectorOpen) e.currentTarget.style.color = '#8B949E'; }}
        >
          <PanelRight size={18} />
        </button>
      </div>
    </div>
  );
}
