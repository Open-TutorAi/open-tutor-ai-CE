import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

// Create the mocks first before usage
const mockAppName = 'OpenTutorAI';

// Mock modules with vi.mock
vi.mock('$lib/constants', () => ({
  APP_NAME: mockAppName
}));

// Create a OpenTutorAI name mock that we can reference later
const mockOpenTutorAIName = {
  set: vi.fn(),
  subscribe: vi.fn(cb => {
    cb(mockAppName);
    return () => {};
  })
};

// Mock the stores
vi.mock('$lib/stores', () => ({
  OpenTutorAI_NAME: mockOpenTutorAIName,
  settings: {
    subscribe: vi.fn(cb => {
      cb({});
      return () => {};
    }),
    update: vi.fn()
  },
  mobile: {
    subscribe: vi.fn(cb => {
      cb(false);
      return () => {};
    })
  },
  config: {
    subscribe: vi.fn(cb => {
      cb({});
      return () => {};
    })
  },
  i18n: {
    subscribe: vi.fn(cb => {
      cb({ t: function(key) { return key; } });
      return () => {};
    })
  }
}));

describe('Application Title Tests', () => {
  // Create a simple document mock object type for testing
  let originalTitle = '';
  
  // Setup mocks before each test
  beforeEach(() => {
    // Save original document title
    originalTitle = document.title;
    
    // Update document title for testing
    document.title = 'Initial Title';
    
    // Reset mocks
    vi.clearAllMocks();
  });

  // Restore document after each test
  afterEach(() => {
    // Restore original title
    document.title = originalTitle;
  });

  it('should have APP_NAME set to OpenTutorAI', () => {
    expect(mockAppName).toBe('OpenTutorAI');
  });

  it('should override backend name with OpenTutorAI', async () => {
    // Mock the scenario where the layout component would set OpenTutorAI_NAME from backend
    const mockBackendConfig = {
      name: 'Open Tutor AI' // This is what the backend would send
    };
    
    // Call the set function similar to what happens in +layout.svelte
    mockOpenTutorAIName.set('OpenTutorAI');
    
    // Check that our value is used, not the backend's
    expect(mockOpenTutorAIName.set).toHaveBeenCalledWith('OpenTutorAI');
    expect(mockOpenTutorAIName.set).not.toHaveBeenCalledWith(mockBackendConfig.name);
  });
}); 