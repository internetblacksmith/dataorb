import '@testing-library/jest-dom';

// TextEncoder/TextDecoder polyfill — required by react-router v7 in jsdom
import { TextEncoder, TextDecoder } from 'util';
if (typeof globalThis.TextEncoder === 'undefined') {
  globalThis.TextEncoder = TextEncoder;
  // @ts-expect-error TextDecoder types don't match exactly
  globalThis.TextDecoder = TextDecoder;
}

// BroadcastChannel mock — jsdom doesn't provide one
class MockBroadcastChannel {
  name: string;
  private listeners: Map<string, Set<EventListener>> = new Map();

  constructor(name: string) {
    this.name = name;
  }

  postMessage(_message: unknown): void {
    // no-op in tests
  }

  addEventListener(type: string, listener: EventListener): void {
    if (!this.listeners.has(type)) {
      this.listeners.set(type, new Set());
    }
    this.listeners.get(type)!.add(listener);
  }

  removeEventListener(type: string, listener: EventListener): void {
    this.listeners.get(type)?.delete(listener);
  }

  close(): void {
    this.listeners.clear();
  }
}

// @ts-expect-error jsdom doesn't have BroadcastChannel
globalThis.BroadcastChannel = MockBroadcastChannel;
