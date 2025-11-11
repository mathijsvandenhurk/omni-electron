/**
 * Message Storage Service
 * 
 * Robust persistence layer using IndexedDB with localStorage fallback
 * Ensures messages and tool executions are NEVER lost
 */

import type {
  OmniMessage,
  AssistantMessage,
  StorageOptions
} from '../types/messages';
import { marked } from 'marked';

/**
 * Deep clone object and remove non-serializable properties
 * This prevents IndexedDB "An object could not be cloned" errors
 */
function sanitizeForStorage(obj: any): any {
  // Handle null/undefined
  if (obj === null || obj === undefined) return obj;
  
  // Handle primitives
  if (typeof obj !== 'object') return obj;
  
  // Handle Date
  if (obj instanceof Date) return obj.toISOString();
  
  // Handle Arrays
  if (Array.isArray(obj)) {
    return obj.map(item => sanitizeForStorage(item));
  }
  
  // Handle plain objects
  const sanitized: any = {};
  const seen = new WeakSet();
  
  for (const key in obj) {
    if (!obj.hasOwnProperty(key)) continue;
    
    const value = obj[key];
    
    // Skip functions
    if (typeof value === 'function') continue;
    
    // Skip DOM nodes
    if (value instanceof Node) continue;
    
    // Skip circular references
    if (typeof value === 'object' && value !== null) {
      if (seen.has(value)) continue;
      seen.add(value);
    }
    
    // Recursively sanitize
    try {
      sanitized[key] = sanitizeForStorage(value);
    } catch (e) {
      console.warn(`[MessageStorage] ⚠️ Skipping non-serializable property: ${key}`, e);
    }
  }
  
  return sanitized;
}

/**
 * IndexedDB wrapper for message storage
 */
class MessageStorageDB {
  private dbName = 'omni-chat-db';
  private version = 2; // Increment version to trigger upgrade and fix timestamp issues
  private db: IDBDatabase | null = null;

  async init(): Promise<void> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, this.version);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        this.db = request.result;
        resolve();
      };

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;
        const oldVersion = event.oldVersion;

        console.log(`[MessageStorage] 🔄 Database upgrade: v${oldVersion} → v${this.version}`);

        // If upgrading from version 1, clear old data to fix timestamp issues
        if (oldVersion === 1 && db.objectStoreNames.contains('messages')) {
          console.log('[MessageStorage] 🧹 Clearing old v1 data (timestamp format fix)');
          // Delete and recreate the store to start fresh
          db.deleteObjectStore('messages');
          if (db.objectStoreNames.contains('threads')) {
            db.deleteObjectStore('threads');
          }
          if (db.objectStoreNames.contains('chatIndex')) {
            db.deleteObjectStore('chatIndex');
          }
        }

        // Messages store
        if (!db.objectStoreNames.contains('messages')) {
          const messageStore = db.createObjectStore('messages', { keyPath: 'id' });
          messageStore.createIndex('timestamp', 'timestamp', { unique: false });
          messageStore.createIndex('role', 'role', { unique: false });
          messageStore.createIndex('requestId', 'requestId', { unique: false });
        }

        // Threads store (for future use)
        if (!db.objectStoreNames.contains('threads')) {
          const threadStore = db.createObjectStore('threads', { keyPath: 'id' });
          threadStore.createIndex('createdAt', 'createdAt', { unique: false });
        }

        // Chat index (for fast queries)
        if (!db.objectStoreNames.contains('chatIndex')) {
          db.createObjectStore('chatIndex', { keyPath: 'key' });
        }
        
        console.log('[MessageStorage] ✅ Database schema updated');
      };
    });
  }

  async saveMessage(message: OmniMessage): Promise<void> {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      // Sanitize message to remove non-serializable properties
      const sanitizedMessage = sanitizeForStorage(message);
      
      const transaction = this.db!.transaction(['messages'], 'readwrite');
      const store = transaction.objectStore('messages');
      const request = store.put(sanitizedMessage);

      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }

  async getMessages(limit = 50): Promise<OmniMessage[]> {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['messages'], 'readonly');
      const store = transaction.objectStore('messages');
      const index = store.index('timestamp');
      const request = index.openCursor(null, 'prev'); // Latest first

      const messages: OmniMessage[] = [];
      let count = 0;

      request.onsuccess = (event) => {
        const cursor = (event.target as IDBRequest).result;
        if (cursor && count < limit) {
          const msg = cursor.value;
          // Convert timestamp string back to Date object
          if (msg.timestamp && typeof msg.timestamp === 'string') {
            msg.timestamp = new Date(msg.timestamp);
          }
          messages.push(msg);
          count++;
          cursor.continue();
        } else {
          resolve(messages.reverse()); // Return in chronological order
        }
      };

      request.onerror = () => reject(request.error);
    });
  }

  async getMessage(id: string): Promise<OmniMessage | null> {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['messages'], 'readonly');
      const store = transaction.objectStore('messages');
      const request = store.get(id);

      request.onsuccess = () => {
        const msg = request.result;
        if (msg) {
          // Convert timestamp string back to Date object
          if (msg.timestamp && typeof msg.timestamp === 'string') {
            msg.timestamp = new Date(msg.timestamp);
          }
        }
        resolve(msg || null);
      };
      request.onerror = () => reject(request.error);
    });
  }

  async deleteMessage(id: string): Promise<void> {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['messages'], 'readwrite');
      const store = transaction.objectStore('messages');
      const request = store.delete(id);

      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }

  async clear(): Promise<void> {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['messages'], 'readwrite');
      const store = transaction.objectStore('messages');
      const request = store.clear();

      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }

  async count(): Promise<number> {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['messages'], 'readonly');
      const store = transaction.objectStore('messages');
      const request = store.count();

      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }
}

/**
 * Main Message Storage Service
 */
export class MessageStorage {
  private db: MessageStorageDB;
  private cache: Map<string, OmniMessage> = new Map();
  private options: Required<StorageOptions>;

  constructor(options: StorageOptions = {}) {
    this.db = new MessageStorageDB();
    this.options = {
      maxMessages: options.maxMessages || 1000,
      archiveThreshold: options.archiveThreshold || 100,
      enableCache: options.enableCache !== false
    };
  }

  /**
   * Initialize storage (must be called before use)
   */
  async init(): Promise<void> {
    console.log('[MessageStorage] 🔧 Initializing IndexedDB storage...');
    try {
      await this.db.init();
      console.log('[MessageStorage] ✅ IndexedDB connection established');
      
      await this.loadCacheFromDB();
      console.log(`[MessageStorage] 📦 Cache loaded with ${this.cache.size} messages`);
      
      await this.migrateFromLocalStorage();
      console.log('[MessageStorage] 🔄 Migration from localStorage complete');
    } catch (error) {
      console.error('[MessageStorage] ❌ Failed to initialize:', error);
      // Fallback to localStorage only mode
    }
  }

  /**
   * Save message with full validation and enhancement
   */
  async saveMessage(message: OmniMessage): Promise<void> {
    try {
      // Validate and enhance message
      const enhanced = await this.enhanceMessage(message);

      // Save to IndexedDB
      await this.db.saveMessage(enhanced);

      // Update memory cache
      if (this.options.enableCache) {
        this.cache.set(enhanced.id, enhanced);
      }

      // Also save to localStorage as backup
      await this.backupToLocalStorage(enhanced);

      // Debug: Show what was saved
      if (enhanced.role === 'assistant') {
        const content = enhanced.structuredContent;
        console.log(`[MessageStorage] 💾 Saved assistant message: ${enhanced.id.substring(0, 8)}...`);
        console.log(`  - Narrative: ${content.narrative.length} chars`);
        console.log(`  - Tools: ${content.tools.length}`);
        console.log(`  - Code changes: ${content.codeChanges.length}`);
        console.log(`  - File refs: ${content.fileReferences.length}`);
      } else {
        console.log(`[MessageStorage] 💾 Saved ${enhanced.role} message: ${enhanced.id.substring(0, 8)}...`);
      }
    } catch (error) {
      console.error('[MessageStorage] ❌ Failed to save message:', error);
      // Try localStorage fallback
      try {
        await this.backupToLocalStorage(message);
        console.log('[MessageStorage] 📦 Fallback: Saved to localStorage');
      } catch (fallbackError) {
        console.error('[MessageStorage] ❌❌ Fallback also failed:', fallbackError);
      }
    }
  }

  /**
   * Load recent messages
   */
  async loadRecentMessages(limit = 50): Promise<OmniMessage[]> {
    console.log(`[MessageStorage] 📥 Loading recent messages (limit: ${limit})...`);
    try {
      // Try cache first (instant)
      if (this.cache.size > 0) {
        console.log(`[MessageStorage] 🚀 Cache hit! ${this.cache.size} messages available`);
        const cached = Array.from(this.cache.values())
          .sort((a, b) => {
            // Ensure timestamps are Date objects
            const timeA = a.timestamp instanceof Date ? a.timestamp.getTime() : new Date(a.timestamp).getTime();
            const timeB = b.timestamp instanceof Date ? b.timestamp.getTime() : new Date(b.timestamp).getTime();
            return timeB - timeA;
          })
          .slice(0, limit);
        
        if (cached.length >= limit) {
          console.log(`[MessageStorage] ✅ Returning ${cached.length} messages from cache`);
          return cached.reverse(); // Chronological order
        }
      }

      // Load from IndexedDB
      console.log('[MessageStorage] 💿 Loading from IndexedDB...');
      const messages = await this.db.getMessages(limit);
      console.log(`[MessageStorage] ✅ Loaded ${messages.length} messages from IndexedDB`);
      
      // Update cache
      if (this.options.enableCache) {
        messages.forEach(msg => this.cache.set(msg.id, msg));
        console.log(`[MessageStorage] 📦 Cache updated with ${messages.length} messages`);
      }

      return messages;
    } catch (error) {
      console.error('[MessageStorage] ❌ Failed to load from IndexedDB:', error);
      console.log('[MessageStorage] 🔄 Trying localStorage fallback...');
      // Fallback to localStorage
      return this.loadFromLocalStorage();
    }
  }

  /**
   * Get single message by ID
   */
  async getMessage(id: string): Promise<OmniMessage | null> {
    // Check cache first
    if (this.cache.has(id)) {
      return this.cache.get(id)!;
    }

    // Load from DB
    try {
      const message = await this.db.getMessage(id);
      if (message && this.options.enableCache) {
        this.cache.set(id, message);
      }
      return message;
    } catch (error) {
      console.error('[MessageStorage] Failed to get message:', error);
      return null;
    }
  }

  /**
   * Delete message
   */
  async deleteMessage(id: string): Promise<void> {
    try {
      await this.db.deleteMessage(id);
      this.cache.delete(id);
      console.log('[MessageStorage] Deleted message:', id);
    } catch (error) {
      console.error('[MessageStorage] Failed to delete message:', error);
    }
  }

  /**
   * Clear all messages
   */
  async clearAll(): Promise<void> {
    try {
      await this.db.clear();
      this.cache.clear();
      localStorage.removeItem('omni-chat-messages');
      localStorage.removeItem('omni-chat-archived');
      console.log('[MessageStorage] Cleared all messages');
    } catch (error) {
      console.error('[MessageStorage] Failed to clear messages:', error);
    }
  }

  /**
   * Get message count
   */
  async getCount(): Promise<number> {
    try {
      return await this.db.count();
    } catch (error) {
      console.error('[MessageStorage] Failed to get count:', error);
      return this.cache.size;
    }
  }

  /**
   * Enhance message with validation and caching
   */
  private async enhanceMessage(message: OmniMessage): Promise<OmniMessage> {
    // User messages don't need enhancement
    if (message.role === 'user' || message.role === 'tool' || message.role === 'system') {
      return message;
    }

    // Assistant messages need full enhancement
    const assistantMsg = message as AssistantMessage;

    // Ensure structured content exists
    if (!assistantMsg.structuredContent) {
      assistantMsg.structuredContent = {
        narrative: assistantMsg.content || '',
        narrativeHtml: undefined,
        tools: [],
        codeChanges: [],
        fileReferences: [],
        metadata: {
          duration: 0,
          model: 'unknown',
          filesModified: [],
          testsRun: false
        }
      };
    }

    // Render markdown to HTML (cached)
    if (!assistantMsg.structuredContent.narrativeHtml && assistantMsg.structuredContent.narrative) {
      try {
        assistantMsg.structuredContent.narrativeHtml = await this.renderMarkdown(
          assistantMsg.structuredContent.narrative
        );
      } catch (error) {
        console.warn('[MessageStorage] Failed to render markdown:', error);
      }
    }

    // Ensure state exists
    if (!assistantMsg.state) {
      assistantMsg.state = {
        isStreaming: false,
        isComplete: true,
        hasError: false
      };
    }

    // Create render cache
    assistantMsg._cached = {
      renderedAt: new Date(),
      htmlContent: assistantMsg.structuredContent.narrativeHtml || '',
      toolsCount: assistantMsg.structuredContent.tools.length,
      codeChangesCount: assistantMsg.structuredContent.codeChanges.length
    };

    return assistantMsg;
  }

  /**
   * Render markdown to HTML
   */
  private async renderMarkdown(markdown: string): Promise<string> {
    try {
      return await marked.parse(markdown, {
        gfm: true,
        breaks: true
      });
    } catch (error) {
      console.error('[MessageStorage] Markdown rendering failed:', error);
      return markdown;
    }
  }

  /**
   * Load cache from DB on startup
   */
  private async loadCacheFromDB(): Promise<void> {
    if (!this.options.enableCache) return;

    try {
      const messages = await this.db.getMessages(50);
      messages.forEach(msg => this.cache.set(msg.id, msg));
      console.log('[MessageStorage] Loaded', messages.length, 'messages into cache');
    } catch (error) {
      console.error('[MessageStorage] Failed to load cache:', error);
    }
  }

  /**
   * Migrate old messages from localStorage to IndexedDB
   */
  private async migrateFromLocalStorage(): Promise<void> {
    try {
      const oldMessages = localStorage.getItem('omni-chat-messages');
      if (!oldMessages) return;

      const parsed = JSON.parse(oldMessages);
      if (!Array.isArray(parsed) || parsed.length === 0) return;

      console.log('[MessageStorage] Migrating', parsed.length, 'messages from localStorage...');

      // Import the migration function
      const { migrateOldMessage } = await import('../types/messages');

      for (const oldMsg of parsed) {
        try {
          const migrated = migrateOldMessage(oldMsg);
          await this.saveMessage(migrated);
        } catch (error) {
          console.error('[MessageStorage] Failed to migrate message:', error);
        }
      }

      console.log('[MessageStorage] ✅ Migration complete');
      
      // Keep localStorage as backup but mark as migrated
      localStorage.setItem('omni-chat-migrated', 'true');
    } catch (error) {
      console.error('[MessageStorage] Migration failed:', error);
    }
  }

  /**
   * Backup to localStorage (fallback)
   */
  private async backupToLocalStorage(message: OmniMessage): Promise<void> {
    try {
      const existing = localStorage.getItem('omni-chat-messages-backup');
      const messages = existing ? JSON.parse(existing) : [];
      
      // Sanitize message before adding
      const sanitized = sanitizeForStorage(message);
      
      // Add new message
      messages.push(sanitized);
      
      // Keep only last 100
      if (messages.length > 100) {
        messages.splice(0, messages.length - 100);
      }
      
      localStorage.setItem('omni-chat-messages-backup', JSON.stringify(messages));
    } catch (error) {
      console.error('[MessageStorage] Backup to localStorage failed:', error);
    }
  }

  /**
   * Load from localStorage (fallback)
   */
  private async loadFromLocalStorage(): Promise<OmniMessage[]> {
    try {
      // Try backup first
      const backup = localStorage.getItem('omni-chat-messages-backup');
      if (backup) {
        return JSON.parse(backup);
      }

      // Try old format
      const old = localStorage.getItem('omni-chat-messages');
      if (old) {
        const parsed = JSON.parse(old);
        const { migrateOldMessage } = await import('../types/messages');
        return parsed.map(migrateOldMessage);
      }

      return [];
    } catch (error) {
      console.error('[MessageStorage] Failed to load from localStorage:', error);
      return [];
    }
  }
}

/**
 * Global storage instance
 */
export const messageStorage = new MessageStorage({
  maxMessages: 1000,
  archiveThreshold: 100,
  enableCache: true
});
