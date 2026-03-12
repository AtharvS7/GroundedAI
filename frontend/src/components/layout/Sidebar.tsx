'use client';

import { usePathname, useRouter } from 'next/navigation';
import { MessageSquare, FileText, BarChart2, Settings, LogOut, ChevronLeft, Plus } from 'lucide-react';
import { useChatStore } from '@/store/chatStore';
import { useAuthStore } from '@/store/authStore';
import { createClient } from '@/lib/supabase';
import { formatDate, truncate } from '@/lib/utils';
import { motion, AnimatePresence } from 'framer-motion';

const navItems = [
  { href: '/chat', label: 'Chat', icon: MessageSquare },
  { href: '/documents', label: 'Documents', icon: FileText },
  { href: '/metrics', label: 'Metrics', icon: BarChart2 },
];

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { user } = useAuthStore();
  const {
    conversations,
    activeConversationId,
    isSidebarCollapsed,
    createConversation,
    setActiveConversation,
    toggleSidebar,
  } = useChatStore();

  const handleNewChat = () => {
    const id = createConversation();
    router.push('/chat');
  };

  const handleLogout = async () => {
    const supabase = createClient();
    await supabase.auth.signOut();
    useAuthStore.getState().logout();
    router.push('/login');
  };

  const initials = user?.email?.slice(0, 2).toUpperCase() || 'GA';

  return (
    <motion.aside
      animate={{ width: isSidebarCollapsed ? 64 : 260 }}
      transition={{ duration: 0.2, ease: [0.4, 0, 0.2, 1] }}
      style={{
        background: '#0F1117',
        borderRight: '1px solid #21262D',
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
        overflow: 'hidden',
        flexShrink: 0,
      }}
    >
      {/* Top: Logo + Collapse */}
      <div style={{ padding: '16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        {!isSidebarCollapsed && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{
              width: 28, height: 28, borderRadius: 8,
              background: 'linear-gradient(135deg, #6C63FF, #3B82F6)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 14, fontWeight: 700, color: '#fff',
            }}>G</div>
            <span style={{ fontWeight: 700, fontSize: 15, color: '#E6EDF3' }}>GroundedAI</span>
          </div>
        )}
        <button
          onClick={toggleSidebar}
          style={{
            background: 'none', border: 'none', color: '#8B949E', cursor: 'pointer',
            padding: 4, borderRadius: 6,
          }}
        >
          <ChevronLeft size={18} style={{ transform: isSidebarCollapsed ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }} />
        </button>
      </div>

      {/* New Chat */}
      <div style={{ padding: '0 12px 12px' }}>
        <button
          onClick={handleNewChat}
          style={{
            width: '100%', padding: isSidebarCollapsed ? '10px' : '10px 16px',
            background: 'linear-gradient(135deg, #6C63FF, #3B82F6)',
            border: 'none', borderRadius: 10, color: '#fff', cursor: 'pointer',
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
            fontSize: 13, fontWeight: 600,
            transition: 'all 0.18s cubic-bezier(0.4, 0, 0.2, 1)',
          }}
          onMouseEnter={(e) => { e.currentTarget.style.transform = 'scale(1.02)'; e.currentTarget.style.boxShadow = '0 0 20px rgba(108,99,255,0.3)'; }}
          onMouseLeave={(e) => { e.currentTarget.style.transform = 'scale(1)'; e.currentTarget.style.boxShadow = 'none'; }}
        >
          <Plus size={16} />
          {!isSidebarCollapsed && 'New Chat'}
        </button>
      </div>

      {/* Chat History */}
      {!isSidebarCollapsed && (
        <div style={{ flex: 1, overflow: 'auto', padding: '0 12px' }}>
          <div style={{ fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.08em', color: '#8B949E', padding: '8px 4px', fontWeight: 600 }}>
            Recent
          </div>
          {conversations.map((conv) => (
            <button
              key={conv.id}
              onClick={() => { setActiveConversation(conv.id); router.push('/chat'); }}
              style={{
                width: '100%', padding: '8px 10px', marginBottom: 2,
                background: conv.id === activeConversationId ? '#1C2128' : 'transparent',
                border: 'none', borderRadius: 8, cursor: 'pointer',
                textAlign: 'left', color: '#E6EDF3', fontSize: 13,
                display: 'flex', flexDirection: 'column', gap: 2,
                borderLeft: conv.id === activeConversationId ? '3px solid #6C63FF' : '3px solid transparent',
                transition: 'all 0.15s ease',
              }}
              onMouseEnter={(e) => { if (conv.id !== activeConversationId) e.currentTarget.style.background = '#1C2128'; }}
              onMouseLeave={(e) => { if (conv.id !== activeConversationId) e.currentTarget.style.background = 'transparent'; }}
            >
              <span style={{ fontWeight: 500 }}>{truncate(conv.title, 28)}</span>
              <span style={{ fontSize: 11, color: '#484F58' }}>{formatDate(conv.updated_at)}</span>
            </button>
          ))}
        </div>
      )}

      {/* Bottom Nav */}
      <div style={{ borderTop: '1px solid #21262D', padding: '8px 12px' }}>
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;
          return (
            <button
              key={item.href}
              onClick={() => router.push(item.href)}
              style={{
                width: '100%', padding: '8px 10px', marginBottom: 2,
                background: isActive ? '#1C2128' : 'transparent',
                border: 'none', borderRadius: 8, cursor: 'pointer',
                display: 'flex', alignItems: 'center', gap: 10,
                color: isActive ? '#6C63FF' : '#8B949E',
                fontSize: 13, fontWeight: isActive ? 600 : 400,
                borderLeft: isActive ? '3px solid #6C63FF' : '3px solid transparent',
                transition: 'all 0.15s ease',
              }}
              onMouseEnter={(e) => { e.currentTarget.style.color = '#6C63FF'; }}
              onMouseLeave={(e) => { if (!isActive) e.currentTarget.style.color = '#8B949E'; }}
            >
              <Icon size={18} />
              {!isSidebarCollapsed && item.label}
            </button>
          );
        })}
      </div>

      {/* User Card */}
      <div style={{ borderTop: '1px solid #21262D', padding: 12, display: 'flex', alignItems: 'center', gap: 10 }}>
        <div style={{
          width: 32, height: 32, borderRadius: '50%',
          background: 'linear-gradient(135deg, #6C63FF, #3B82F6)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 12, fontWeight: 700, color: '#fff', flexShrink: 0,
        }}>{initials}</div>
        {!isSidebarCollapsed && (
          <>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: 13, fontWeight: 500, color: '#E6EDF3', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {user?.email || 'User'}
              </div>
            </div>
            <button
              onClick={handleLogout}
              style={{ background: 'none', border: 'none', color: '#8B949E', cursor: 'pointer', padding: 4, borderRadius: 6 }}
              onMouseEnter={(e) => { e.currentTarget.style.color = '#6C63FF'; }}
              onMouseLeave={(e) => { e.currentTarget.style.color = '#8B949E'; }}
            >
              <LogOut size={16} />
            </button>
          </>
        )}
      </div>
    </motion.aside>
  );
}
