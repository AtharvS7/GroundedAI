/** Utility functions */

import { clsx, type ClassValue } from 'clsx';

export function cn(...inputs: ClassValue[]): string {
  return clsx(inputs);
}

export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

export function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const days = Math.floor(diff / (1000 * 60 * 60 * 24));

  if (days === 0) return 'Today';
  if (days === 1) return 'Yesterday';
  if (days < 7) return `${days} days ago`;
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

export function truncate(text: string, maxLen: number): string {
  if (text.length <= maxLen) return text;
  return text.slice(0, maxLen) + '...';
}

export function getConfidenceLevel(score: number): {
  label: string;
  color: string;
  bg: string;
} {
  if (score >= 0.8) return { label: 'High', color: '#10B981', bg: 'rgba(16,185,129,0.1)' };
  if (score >= 0.6) return { label: 'Medium', color: '#F59E0B', bg: 'rgba(245,158,11,0.1)' };
  return { label: 'Low', color: '#EF4444', bg: 'rgba(239,68,68,0.1)' };
}
