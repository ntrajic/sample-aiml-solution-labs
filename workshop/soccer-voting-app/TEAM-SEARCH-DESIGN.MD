# Team Search Feature - Design Document

## Component Architecture

### Component Hierarchy
```
VotingPage
├── TeamSearchBar (new)
└── TeamList
    └── TeamCard[]
```

## Component Design

### TeamSearchBar Component

```javascript
// src/components/TeamSearchBar.jsx
import { TextField, InputAdornment, IconButton } from '@mui/material';
import { Search, Clear } from '@mui/icons-material';

export default function TeamSearchBar({ searchTerm, onSearchChange, onClear }) {
  return (
    <TextField
      fullWidth
      placeholder="Search teams..."
      value={searchTerm}
      onChange={(e) => onSearchChange(e.target.value)}
      InputProps={{
        startAdornment: (
          <InputAdornment position="start">
            <Search />
          </InputAdornment>
        ),
        endAdornment: searchTerm && (
          <InputAdornment position="end">
            <IconButton onClick={onClear} size="small" aria-label="Clear search">
              <Clear />
            </IconButton>
          </InputAdornment>
        ),
      }}
      sx={{ mb: 3 }}
      aria-label="Search teams"
    />
  );
}
```

### VotingPage Component (Updated)

```javascript
// src/pages/VotingPage.jsx
import { useState, useMemo } from 'react';
import TeamSearchBar from '../components/TeamSearchBar';
import TeamList from '../components/TeamList';

export default function VotingPage() {
  const [teams, setTeams] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');

  const filteredTeams = useMemo(() => {
    if (!searchTerm) return teams;
    return teams.filter(team =>
      team.name.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [teams, searchTerm]);

  const handleClearSearch = () => setSearchTerm('');

  return (
    <div>
      <TeamSearchBar
        searchTerm={searchTerm}
        onSearchChange={setSearchTerm}
        onClear={handleClearSearch}
      />
      {filteredTeams.length === 0 ? (
        <p>No teams found matching "{searchTerm}"</p>
      ) : (
        <TeamList teams={filteredTeams} />
      )}
    </div>
  );
}
```

## Visual Design

### Layout
```
┌─────────────────────────────────────────┐
│  🔍  Search teams...              ✕     │  ← Search Bar
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│  Manchester United          [Vote] 45%  │  ← Team Card
├─────────────────────────────────────────┤
│  Manchester City            [Vote] 32%  │
├─────────────────────────────────────────┤
│  Real Madrid                [Vote] 23%  │
└─────────────────────────────────────────┘
```

### Styling Specifications

```javascript
// Theme values (Material-UI)
const styles = {
  searchBar: {
    height: '48px',
    marginBottom: '24px',
    backgroundColor: '#ffffff',
    borderRadius: '8px',
    '& .MuiOutlinedInput-root': {
      '&:hover fieldset': {
        borderColor: 'primary.main',
      },
      '&.Mui-focused fieldset': {
        borderWidth: '2px',
      },
    },
  },
  emptyState: {
    textAlign: 'center',
    color: 'text.secondary',
    padding: '48px 16px',
    fontSize: '16px',
  },
};
```

## State Management

### State Structure
```javascript
{
  searchTerm: string,        // Current search input
  teams: Team[],             // All teams from API
  filteredTeams: Team[]      // Computed from teams + searchTerm
}
```

### Data Flow
```
User Input → searchTerm state → useMemo filter → filteredTeams → TeamList render
```

## API Integration

### No Backend Changes Required
- Filtering happens client-side
- Existing team fetch endpoint unchanged
- Search state is local to frontend

## Accessibility

### ARIA Attributes
```javascript
<TextField
  aria-label="Search teams"
  inputProps={{
    'aria-describedby': 'search-help-text'
  }}
/>

<IconButton
  aria-label="Clear search"
  onClick={onClear}
/>

<div role="status" aria-live="polite">
  {filteredTeams.length} teams found
</div>
```

### Keyboard Navigation
- Tab: Focus search input
- Escape: Clear search (optional enhancement)
- Enter: No action (prevents form submission)

## Performance Optimization

### useMemo Hook
```javascript
const filteredTeams = useMemo(() => {
  if (!searchTerm) return teams;
  return teams.filter(team =>
    team.name.toLowerCase().includes(searchTerm.toLowerCase())
  );
}, [teams, searchTerm]);
```

**Why useMemo?**
- Prevents re-filtering on every render
- Only recomputes when teams or searchTerm changes
- Critical for maintaining real-time vote updates

## Edge Cases

### Empty States
1. **No search term**: Show all teams
2. **No matches**: Show "No teams found matching '[term]'"
3. **No teams loaded**: Show loading spinner (existing behavior)

### Special Characters
- Handle special regex characters in search (e.g., "(", ")")
- Use simple string includes (no regex needed)

### Long Team Names
- Team cards handle text overflow with ellipsis
- Search matches full name, not truncated display

## Testing Strategy

### Unit Tests
```javascript
describe('TeamSearchBar', () => {
  test('renders search input', () => {});
  test('calls onSearchChange when typing', () => {});
  test('shows clear button when text present', () => {});
  test('calls onClear when clear button clicked', () => {});
});

describe('VotingPage filtering', () => {
  test('filters teams by name substring', () => {});
  test('filter is case-insensitive', () => {});
  test('shows all teams when search is empty', () => {});
  test('shows empty state when no matches', () => {});
});
```

### Integration Tests
```javascript
test('user can search and vote for filtered team', async () => {
  render(<VotingPage />);
  
  const searchInput = screen.getByPlaceholderText('Search teams...');
  fireEvent.change(searchInput, { target: { value: 'Manchester' } });
  
  expect(screen.getByText('Manchester United')).toBeInTheDocument();
  expect(screen.queryByText('Real Madrid')).not.toBeInTheDocument();
  
  const voteButton = screen.getByRole('button', { name: /vote/i });
  fireEvent.click(voteButton);
  
  // Assert vote was submitted
});
```

## Implementation Checklist

- [ ] Create TeamSearchBar component
- [ ] Add searchTerm state to VotingPage
- [ ] Implement filtering logic with useMemo
- [ ] Add empty state message
- [ ] Style search bar with Material-UI theme
- [ ] Add ARIA labels for accessibility
- [ ] Write unit tests for TeamSearchBar
- [ ] Write integration tests for filtering
- [ ] Test with real-time vote updates
- [ ] Test keyboard navigation
- [ ] Update IMPL-TASKS.MD with completion

## File Structure

```
src/
├── components/
│   ├── TeamSearchBar.jsx          (new)
│   ├── TeamSearchBar.test.jsx     (new)
│   ├── TeamList.jsx               (existing)
│   └── TeamCard.jsx               (existing)
├── pages/
│   ├── VotingPage.jsx             (modified)
│   └── VotingPage.test.jsx        (modified)
└── utils/
    └── filterTeams.js             (optional helper)
```

## Dependencies

### Existing (from TECH-STACK.MD)
- React 18+
- Material-UI components
- Socket.io-client (for real-time updates)

### New Dependencies
None - uses existing Material-UI components

## Deployment Notes

- No database migrations required
- No API changes required
- Frontend-only change
- Can be deployed independently
- No feature flag needed (low risk)
