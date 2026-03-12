'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Eye, EyeOff } from 'lucide-react';
import { createClient } from '@/lib/supabase';
import { useAuthStore } from '@/store/authStore';
import { motion } from 'framer-motion';

export default function LoginPage() {
  const router = useRouter();
  const { setUser } = useAuthStore();
  const [isSignUp, setIsSignUp] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    const supabase = createClient();

    try {
      if (isSignUp) {
        const { data, error: signUpError } = await supabase.auth.signUp({ email, password });
        if (signUpError) throw signUpError;
        if (data.user) {
          setUser({ id: data.user.id, email: data.user.email || '' });
          router.push('/chat');
        }
      } else {
        const { data, error: signInError } = await supabase.auth.signInWithPassword({ email, password });
        if (signInError) throw signInError;
        if (data.user) {
          setUser({ id: data.user.id, email: data.user.email || '' });
          router.push('/chat');
        }
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: '#0A0C10', position: 'relative', overflow: 'hidden',
    }}>
      {/* Animated background orbs */}
      <div style={{
        position: 'absolute', width: 500, height: 500, borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(108,99,255,0.15) 0%, transparent 70%)',
        top: '10%', left: '20%', animation: 'pulse-violet 8s ease-in-out infinite',
      }} />
      <div style={{
        position: 'absolute', width: 400, height: 400, borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(59,130,246,0.1) 0%, transparent 70%)',
        bottom: '15%', right: '15%', animation: 'pulse-blue 8s ease-in-out infinite 2s',
      }} />

      {/* Login Card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: [0.4, 0, 0.2, 1] }}
        style={{
          width: 420, backdropFilter: 'blur(16px)', WebkitBackdropFilter: 'blur(16px)',
          background: 'rgba(22,27,34,0.75)', border: '1px solid rgba(48,54,61,0.6)',
          borderRadius: 18, padding: '40px 36px', position: 'relative', zIndex: 10,
          boxShadow: '0 4px 24px rgba(0,0,0,0.4)',
        }}
      >
        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <div style={{
            width: 48, height: 48, borderRadius: 14, margin: '0 auto 12px',
            background: 'linear-gradient(135deg, #6C63FF, #3B82F6)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 22, fontWeight: 700, color: '#fff',
          }}>G</div>
          <h1 style={{ fontSize: 22, fontWeight: 700, color: '#E6EDF3', margin: 0 }}>GroundedAI</h1>
          <p style={{ fontSize: 13, color: '#8B949E', marginTop: 4 }}>Ground your LLM. Trust your answers.</p>
        </div>

        {/* Divider */}
        <div style={{ height: 1, background: '#21262D', margin: '0 0 24px' }} />

        {/* Form */}
        <form onSubmit={handleSubmit}>
          {error && (
            <div style={{
              background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)',
              borderRadius: 10, padding: '10px 14px', marginBottom: 16,
              fontSize: 13, color: '#EF4444',
            }}>{error}</div>
          )}

          <div style={{ marginBottom: 16 }}>
            <input
              type="email" value={email} onChange={(e) => setEmail(e.target.value)}
              placeholder="Email address" required autoFocus
              style={{
                width: '100%', padding: '12px 16px', background: '#161B22',
                border: '1px solid #21262D', borderRadius: 10, color: '#E6EDF3',
                fontSize: 14, outline: 'none', transition: 'all 0.18s',
              }}
              onFocus={(e) => { e.target.style.borderColor = '#6C63FF'; e.target.style.boxShadow = '0 0 0 3px rgba(108,99,255,0.15)'; }}
              onBlur={(e) => { e.target.style.borderColor = '#21262D'; e.target.style.boxShadow = 'none'; }}
            />
          </div>

          <div style={{ marginBottom: 24, position: 'relative' }}>
            <input
              type={showPassword ? 'text' : 'password'} value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Password" required minLength={6}
              style={{
                width: '100%', padding: '12px 44px 12px 16px', background: '#161B22',
                border: '1px solid #21262D', borderRadius: 10, color: '#E6EDF3',
                fontSize: 14, outline: 'none', transition: 'all 0.18s',
              }}
              onFocus={(e) => { e.target.style.borderColor = '#6C63FF'; e.target.style.boxShadow = '0 0 0 3px rgba(108,99,255,0.15)'; }}
              onBlur={(e) => { e.target.style.borderColor = '#21262D'; e.target.style.boxShadow = 'none'; }}
            />
            <button
              type="button" onClick={() => setShowPassword(!showPassword)}
              style={{
                position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)',
                background: 'none', border: 'none', color: '#8B949E', cursor: 'pointer', padding: 4,
              }}
            >
              {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </div>

          <button
            type="submit" disabled={loading}
            style={{
              width: '100%', padding: '12px', border: 'none', borderRadius: 10,
              background: loading ? '#484F58' : 'linear-gradient(135deg, #6C63FF, #3B82F6)',
              color: '#fff', fontSize: 14, fontWeight: 600, cursor: loading ? 'not-allowed' : 'pointer',
              transition: 'all 0.18s cubic-bezier(0.4, 0, 0.2, 1)',
            }}
            onMouseEnter={(e) => { if (!loading) { e.currentTarget.style.transform = 'scale(1.02)'; e.currentTarget.style.boxShadow = '0 0 20px rgba(108,99,255,0.3)'; } }}
            onMouseLeave={(e) => { e.currentTarget.style.transform = 'scale(1)'; e.currentTarget.style.boxShadow = 'none'; }}
          >
            {loading ? 'Please wait...' : isSignUp ? 'Sign Up' : 'Sign In'}
          </button>
        </form>

        {/* Toggle */}
        <p style={{ textAlign: 'center', marginTop: 20, fontSize: 13, color: '#8B949E' }}>
          {isSignUp ? 'Already have an account? ' : "Don't have an account? "}
          <button
            onClick={() => { setIsSignUp(!isSignUp); setError(''); }}
            style={{
              background: 'none', border: 'none', color: '#6C63FF',
              cursor: 'pointer', fontSize: 13, fontWeight: 600,
            }}
          >
            {isSignUp ? 'Sign In' : 'Sign Up'}
          </button>
        </p>

        {/* Footer */}
        <p style={{ textAlign: 'center', marginTop: 16, fontSize: 11, color: '#484F58' }}>
          Fully local. Zero cloud costs.
        </p>
      </motion.div>
    </div>
  );
}
