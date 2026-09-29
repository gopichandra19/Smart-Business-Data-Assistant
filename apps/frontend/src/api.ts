/**
 * API client for the Smart Business Data Assistant backend.
 * Handles authentication, request/response formatting, and error handling.
 */

import axios, { type AxiosInstance } from 'axios';

const API_BASE = '/api/v1';

class ApiClient {
  private client: AxiosInstance;
  private token: string | null = null;

  constructor() {
    this.client = axios.create({ baseURL: API_BASE });
    this.client.interceptors.request.use((config) => {
      if (this.token) {
        config.headers.Authorization = `Bearer ${this.token}`;
      }
      return config;
    });
    this.client.interceptors.response.use(
      (res) => res,
      (err) => {
        if (err.response?.status === 401) {
          this.token = null;
          localStorage.removeItem('token');
          localStorage.removeItem('user');
          window.location.href = '/login';
        }
        return Promise.reject(err);
      }
    );
    // Restore token
    const saved = localStorage.getItem('token');
    if (saved) this.token = saved;
  }

  setToken(token: string) {
    this.token = token;
    localStorage.setItem('token', token);
  }

  clearToken() {
    this.token = null;
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  }

  isAuthenticated() {
    return !!this.token;
  }

  // Auth
  async login(email: string, password: string) {
    const { data } = await this.client.post('/auth/login', { email, password });
    this.setToken(data.access_token);
    localStorage.setItem('user', JSON.stringify(data.user));
    return data;
  }

  getUser() {
    const u = localStorage.getItem('user');
    return u ? JSON.parse(u) : null;
  }

  async getMe() {
    const { data } = await this.client.get('/auth/me');
    return data;
  }

  // Dashboard
  async getDashboard() {
    const { data } = await this.client.get('/dashboard');
    return data;
  }

  // Chat
  async sendMessage(message: string, conversationId?: number) {
    const { data } = await this.client.post('/chat', {
      message,
      conversation_id: conversationId,
    });
    return data;
  }

  // Conversations
  async getConversations() {
    const { data } = await this.client.get('/conversations');
    return data;
  }

  async getConversation(id: number) {
    const { data } = await this.client.get(`/conversations/${id}`);
    return data;
  }

  // Data Sources
  async getDataSources() {
    const { data } = await this.client.get('/data-sources');
    return data;
  }

  // Knowledge
  async getKnowledge(category?: string, search?: string) {
    const params: Record<string, string> = {};
    if (category) params.category = category;
    if (search) params.search = search;
    const { data } = await this.client.get('/knowledge', { params });
    return data;
  }

  async addKnowledge(doc: { title: string; content: string; category: string; business_domain?: string; table_name?: string; column_name?: string }) {
    const { data } = await this.client.post('/knowledge', doc);
    return data;
  }

  // Memory
  async getMemories(memoryType?: string) {
    const params: Record<string, string> = {};
    if (memoryType) params.memory_type = memoryType;
    const { data } = await this.client.get('/memories', { params });
    return data;
  }

  async deleteMemory(id: number) {
    const { data } = await this.client.delete(`/memories/${id}`);
    return data;
  }

  // Audit
  async getAuditLogs(limit = 50) {
    const { data } = await this.client.get('/audit', { params: { limit } });
    return data;
  }

  // Insights
  async getInsights() {
    const { data } = await this.client.get('/insights');
    return data;
  }

  // Settings
  async getSettings() {
    const { data } = await this.client.get('/settings');
    return data;
  }

  // Health
  async health() {
    const { data } = await this.client.get('/health');
    return data;
  }
}

export const api = new ApiClient();
export default api;
