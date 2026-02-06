# Auto-Save Integration Guide for Jorge's Mobile Platform

This guide explains how to implement auto-save functionality across all field agent forms and components to prevent data loss during poor connectivity.

## Overview

The auto-save system provides comprehensive offline protection for field agents through:
- **Automatic form saving** every 3-5 seconds
- **Instant save** on critical events (recording complete, photo captured)
- **Visual feedback** for save status
- **Form restoration** on page reload/navigation
- **Conflict resolution** for simultaneous edits

## Core Components

### 1. `useAutoSave` Hook (`/hooks/useAutoSave.ts`)

Main hook providing auto-save functionality for any form data:

```typescript
import { useAutoSave } from '@/hooks/useAutoSave';

const [state, actions] = useAutoSave(initialData, {
  storeName: 'agent_notes',
  keyPrefix: 'lead_notes',
  autoSaveInterval: 5000, // 5 seconds
  instantSaveEvents: ['blur', 'lead_change'],
  validator: (data) => typeof data === 'object',
  debugMode: true
});
```

### 2. Visual Indicators

- **`AutoSaveIndicator`**: Floating status indicator with controls
- **`FieldSaveIndicator`**: Compact indicator for form fields
- **`AutoSaveToast`**: Success/error notifications

### 3. Specialized Hooks

Pre-configured hooks for common data types:
- **`useVoiceNoteAutoSave`**: Voice recordings (3s interval)
- **`usePropertyScanAutoSave`**: Scan results (2s interval)
- **`useAgentNotesAutoSave`**: Lead notes (5s interval)
- **`useSafetyControlsAutoSave`**: Safety settings (1s interval)

## Integration Examples

### Voice Recording Component

```typescript
import { useVoiceNoteAutoSave } from '@/hooks/useAutoSave';
import { AutoSaveIndicator, FieldSaveIndicator } from '@/components/mobile/AutoSaveIndicator';

function VoiceRecorder() {
  const [autoSaveState, autoSaveActions] = useVoiceNoteAutoSave(initialNote);

  useEffect(() => {
    if (currentNote?.transcript) {
      autoSaveActions.updateData({
        transcript: currentNote.transcript,
        confidence: currentNote.confidence
      });
    }
  }, [currentNote?.transcript]);

  return (
    <div className="relative">
      {/* Auto-save indicator */}
      <div className="absolute top-4 right-4">
        <AutoSaveIndicator
          status={autoSaveState.status}
          lastSaved={autoSaveState.lastSaved}
          size="sm"
        />
      </div>

      {/* Transcript with save status */}
      <div className="relative">
        <TranscriptionDisplay transcript={transcript} />
        {transcript && (
          <div className="absolute top-2 right-2">
            <FieldSaveIndicator status={autoSaveState.status} />
          </div>
        )}
      </div>
    </div>
  );
}
```

### Form with Text Input

```typescript
import { useAgentNotesAutoSave } from '@/hooks/useAutoSave';

function LeadNotesForm({ leadId }) {
  const [autoSaveState, autoSaveActions] = useAgentNotesAutoSave({
    leadId,
    notes: '',
    timestamp: Date.now()
  });

  const handleNotesChange = (notes: string) => {
    autoSaveActions.updateData({ notes });
  };

  return (
    <div>
      <label>Lead Notes</label>
      <textarea
        value={autoSaveState.data.notes}
        onChange={(e) => handleNotesChange(e.target.value)}
        placeholder="Add notes about this lead..."
      />
      <FieldSaveIndicator status={autoSaveState.status} />

      {autoSaveState.saveCount > 0 && (
        <div className="text-xs text-gray-500">
          Auto-saved {autoSaveState.saveCount} times
        </div>
      )}
    </div>
  );
}
```

## Implementation Steps

### Step 1: Choose the Right Hook

| Data Type | Hook | Auto-Save Interval |
|-----------|------|-------------------|
| Voice recordings | `useVoiceNoteAutoSave` | 3 seconds |
| Property scans | `usePropertyScanAutoSave` | 2 seconds |
| Text notes | `useAgentNotesAutoSave` | 5 seconds |
| Safety settings | `useSafetyControlsAutoSave` | 1 second |
| Custom data | `useAutoSave` | Configurable |

### Step 2: Add Auto-Save to Component

```typescript
// 1. Import the hook
import { useVoiceNoteAutoSave } from '@/hooks/useAutoSave';

// 2. Initialize with default data
const [autoSaveState, autoSaveActions] = useVoiceNoteAutoSave(initialData);

// 3. Update data on changes
useEffect(() => {
  autoSaveActions.updateData({ fieldName: newValue });
}, [newValue]);

// 4. Handle critical events
const handleCriticalEvent = async () => {
  await autoSaveActions.saveNow();
  // Continue with event handling
};
```

### Step 3: Add Visual Feedback

```typescript
import { AutoSaveIndicator, FieldSaveIndicator } from '@/components/mobile/AutoSaveIndicator';

// Floating indicator
<AutoSaveIndicator
  status={autoSaveState.status}
  lastSaved={autoSaveState.lastSaved}
  error={autoSaveState.error}
  position="top-right"
  onManualSave={autoSaveActions.saveNow}
/>

// Field-level indicator
<FieldSaveIndicator status={autoSaveState.status} />
```

### Step 4: Handle Form Restoration

```typescript
useEffect(() => {
  const restoreData = async () => {
    const restored = await autoSaveActions.restoreFromStorage();
    if (restored) {
      // Apply restored data to form
      setFormData(restored);
    }
  };
  restoreData();
}, []); // Run once on mount
```

## Components Requiring Auto-Save

### High Priority (Implemented Examples)

1. **✅ Voice Recorder** - `VoiceRecorderWithAutoSave.tsx`
2. **✅ Property Scanner Results** - `PropertyResultsWithAutoSave.tsx`

### Remaining High Priority

3. **Lead Notes Forms** - Agent observations about leads
4. **Safety Controls** - Emergency settings and check-in preferences
5. **Property Photo Capture** - Camera metadata and GPS tagging
6. **Showing Feedback Forms** - Post-showing notes and ratings

### Medium Priority

7. **Filter States** - Search filters and preferences
8. **Dashboard Widget States** - Expanded/collapsed states
9. **Map Preferences** - Zoom level, layer selections
10. **Voice Command History** - Recent voice interactions

## Configuration Options

### Auto-Save Intervals by Data Type

```typescript
const intervals = {
  voice_recordings: 3000,    // Frequent - audio is irreplaceable
  property_scans: 2000,      // Fast - scan data is valuable
  agent_notes: 5000,         // Standard - user text input
  safety_settings: 1000,     // Critical - safety is paramount
  ui_preferences: 10000      // Slow - less critical data
};
```

### Storage Strategy

```typescript
const storageConfig = {
  // Large data (audio, images)
  voiceNotes: 'IndexedDB',
  propertyPhotos: 'IndexedDB',

  // Small data (text, settings)
  agentNotes: 'IndexedDB',
  uiState: 'localStorage',

  // Critical data (safety)
  safetySettings: 'IndexedDB + localStorage backup'
};
```

### Validation Rules

```typescript
const validators = {
  voiceNote: (data) => data.transcript?.length > 0,
  propertyData: (data) => data.propertyId || data.address,
  agentNotes: (data) => typeof data.notes === 'string',
  safetyConfig: (data) => data.checkInInterval > 0
};
```

## Error Handling

### Common Scenarios

1. **Storage Full**: Show user notification, clear old data
2. **Validation Failed**: Retry with sanitized data
3. **Network Issues**: Queue for sync when online
4. **Concurrent Edits**: Use conflict resolution strategy

### Error Recovery

```typescript
const [autoSaveState, autoSaveActions] = useAutoSave(data, {
  onError: (error, data) => {
    // Log error
    console.error('Auto-save failed:', error);

    // Attempt recovery
    if (error.message.includes('storage full')) {
      // Clear old data and retry
      clearOldData().then(() => autoSaveActions.saveNow());
    }
  }
});
```

## Performance Considerations

### Battery Optimization

- Voice recordings: 3s interval (necessary for irreplaceable data)
- Property scans: 2s interval (valuable generated data)
- Text notes: 5s interval (standard user input)
- UI state: 10s interval (less critical)

### Storage Efficiency

- Compress large data (audio, images) before storage
- Use delta updates for incremental changes
- Implement LRU eviction for storage quota management
- Background cleanup of old auto-save data

## Testing

### Manual Testing Scenarios

1. **Network Drop Test**: Turn off network during form entry
2. **Battery Low Test**: Verify reduced auto-save frequency
3. **Page Reload Test**: Ensure data restoration works
4. **Concurrent Edit Test**: Multiple tabs editing same data
5. **Storage Full Test**: Exceed browser storage quota

### Automated Testing

```typescript
// Example test for auto-save hook
test('auto-saves data after interval', async () => {
  const { result } = renderHook(() => useAutoSave(initialData, options));

  // Update data
  act(() => {
    result.current[1].updateData({ field: 'new value' });
  });

  // Wait for auto-save interval
  await waitFor(() => {
    expect(result.current[0].status).toBe('saved');
  }, { timeout: 6000 });
});
```

## Migration Guide

### Existing Components

1. **Identify** forms with user input
2. **Choose** appropriate auto-save hook
3. **Replace** manual save logic with auto-save
4. **Add** visual feedback indicators
5. **Test** offline scenarios thoroughly

### Gradual Rollout

1. **Phase 1**: Critical components (voice, property scans)
2. **Phase 2**: High-value forms (agent notes, safety)
3. **Phase 3**: UI state and preferences
4. **Phase 4**: Advanced features (conflict resolution)

## Best Practices

### Do's

- ✅ Use specialized hooks for known data types
- ✅ Provide visual feedback for save status
- ✅ Validate data before saving
- ✅ Handle errors gracefully with recovery options
- ✅ Test offline scenarios thoroughly

### Don'ts

- ❌ Don't auto-save sensitive data without encryption
- ❌ Don't use overly frequent intervals (< 1s)
- ❌ Don't ignore storage quota limits
- ❌ Don't block UI during save operations
- ❌ Don't skip validation for performance

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|--------|----------|
| Save status stuck on "saving" | Network timeout | Implement retry logic |
| Data not restored on reload | Storage quota exceeded | Clear old data, show warning |
| Auto-save too frequent | Short interval | Adjust interval, use debouncing |
| Validation errors | Bad data format | Implement data sanitization |
| Storage errors | Browser limitations | Fallback to localStorage |

### Debug Mode

Enable debug logging for auto-save operations:

```typescript
const [autoSaveState, autoSaveActions] = useAutoSave(data, {
  debugMode: true // Enables console logging
});
```

This will log:
- Save attempts and results
- Data validation failures
- Storage operations
- Conflict resolution steps

---

## Summary

The auto-save system provides comprehensive protection for field agent data with minimal integration effort. Focus on high-value, irreplaceable data first (voice recordings, property scans), then expand to other forms systematically.

For questions or implementation help, refer to the example components:
- `VoiceRecorderWithAutoSave.tsx` - Complete voice recording protection
- `PropertyResultsWithAutoSave.tsx` - Property scan data protection