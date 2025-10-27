// services/chatRating.ts - Two approaches to fix the TypeScript error

import { api } from './api'

export interface MessageRating {
  message_id: string
  rating: number // -1 (thumbs down) or +1 (thumbs up)
  rated_at: string
}

// Cache to store ratings and prevent constant fetching
const ratingsCache = new Map<string, MessageRating | null>();
const loadingPromises = new Map<string, Promise<MessageRating | null>>();

export const chatRatingService = {
  /**
   * Rate a chat message
   */
  async rateMessage(messageId: string, rating: 1 | -1): Promise<MessageRating> {
    try {
      const { data } = await api.post(`/api/chat/messages/${messageId}/rate`, {
        rating
      })
      
      // Update cache with new rating
      ratingsCache.set(messageId, data);
      
      return data
    } catch (error) {
      console.error('Failed to rate message:', error)
      throw error
    }
  },

  /**
   * Get current rating for a message with caching
   */
  async getMessageRating(messageId: string): Promise<MessageRating | null> {
    // Check cache first
    if (ratingsCache.has(messageId)) {
      return ratingsCache.get(messageId) || null;
    }

    // Check if we're already loading this rating
    if (loadingPromises.has(messageId)) {
      return loadingPromises.get(messageId)!;
    }

    // Create and cache the loading promise
    const loadingPromise = this._fetchMessageRating(messageId);
    loadingPromises.set(messageId, loadingPromise);

    try {
      const result = await loadingPromise;
      // Cache the result (even if null)
      ratingsCache.set(messageId, result);
      return result;
    } finally {
      // Clean up the loading promise
      loadingPromises.delete(messageId);
    }
  },

  /**
   * Private method to actually fetch the rating
   */
  async _fetchMessageRating(messageId: string): Promise<MessageRating | null> {
    try {
      const { data } = await api.get(`/api/chat/messages/${messageId}/rating`)
      return data
    } catch (error) {
      if ((error as any)?.response?.status === 404) {
        return null // Message not rated yet
      }
      console.error('Failed to get message rating:', error)
      throw error
    }
  },

  /**
   * Clear cache for a specific message (useful after rating)
   */
  clearMessageCache(messageId: string): void {
    ratingsCache.delete(messageId);
    loadingPromises.delete(messageId);
  },

  /**
   * Clear all cached ratings (useful when switching conversations)
   */
  clearCache(): void {
    ratingsCache.clear();
    loadingPromises.clear();
  },

  // ========================================
  // APPROACH 1: Return ratings map from preloadRatings
  // ========================================
  /**
   * Preload ratings for multiple messages and return them as a map
   * This approach returns the ratings so the component can use them directly
   */
  async preloadRatings(messageIds: string[]): Promise<Record<string, number>> {
    const uncachedIds = messageIds.filter(id => !ratingsCache.has(id) && !loadingPromises.has(id));
    
    // Load uncached ratings concurrently
    if (uncachedIds.length > 0) {
      const promises = uncachedIds.map(async (messageId) => {
        try {
          const rating = await this.getMessageRating(messageId);
          ratingsCache.set(messageId, rating);
        } catch (error) {
          console.error(`Failed to preload rating for ${messageId}:`, error);
          ratingsCache.set(messageId, null);
        }
      });

      await Promise.allSettled(promises);
    }

    // Now build and return the ratings map from cache
    const ratingsMap: Record<string, number> = {};
    
    for (const messageId of messageIds) {
      const cachedRating = ratingsCache.get(messageId);
      if (cachedRating && cachedRating.rating) {
        ratingsMap[messageId] = cachedRating.rating;
      }
    }
    
    return ratingsMap;
  },

  // ========================================
  // APPROACH 2: Separate methods for preload and get cached ratings
  // ========================================
  /**
   * Alternative: Preload ratings (void return) + separate method to get cached ratings
   */
  async preloadRatingsAsync(messageIds: string[]): Promise<void> {
    const uncachedIds = messageIds.filter(id => !ratingsCache.has(id) && !loadingPromises.has(id));
    
    if (uncachedIds.length === 0) return;

    // Load all uncached ratings concurrently
    const promises = uncachedIds.map(async (messageId) => {
      try {
        const rating = await this.getMessageRating(messageId);
        ratingsCache.set(messageId, rating);
      } catch (error) {
        console.error(`Failed to preload rating for ${messageId}:`, error);
        ratingsCache.set(messageId, null);
      }
    });

    await Promise.allSettled(promises);
  },

  /**
   * Get cached ratings for multiple messages (use after preloadRatingsAsync)
   */
  getCachedRatings(messageIds: string[]): Record<string, number> {
    const ratingsMap: Record<string, number> = {};
    
    for (const messageId of messageIds) {
      const cachedRating = ratingsCache.get(messageId);
      if (cachedRating && cachedRating.rating) {
        ratingsMap[messageId] = cachedRating.rating;
      }
    }
    
    return ratingsMap;
  },

  // ========================================
  // APPROACH 3: Batch API call (most efficient)
  // ========================================
  /**
   * Most efficient: Single API call to get multiple ratings at once
   * Requires backend support for batch rating endpoint
   */
  async batchGetRatings(messageIds: string[]): Promise<Record<string, number>> {
    try {
      const { data } = await api.post('/api/chat/ratings/batch', {
        messageIds
      });
      
      // data should be: { messageId: rating, messageId2: rating, ... }
      const ratingsMap: Record<string, number> = {};
      
      // Cache the results and build the return map
      for (const [messageId, rating] of Object.entries(data)) {
        if (typeof rating === 'number') {
          ratingsMap[messageId] = rating;
          // Cache this rating
          ratingsCache.set(messageId, {
            message_id: messageId,
            rating: rating,
            rated_at: new Date().toISOString()
          });
        }
      }
      
      return ratingsMap;
    } catch (error) {
      console.error('Failed to batch get ratings:', error);
      throw error;
    }
  }
}