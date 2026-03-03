# Team Search Feature Specification

## Overview
Add real-time search functionality to filter teams by name as users type in the voting interface.

## User Story
**AS** a voter  
**I WANT** to search and filter teams by name as I type  
**SO THAT** I can quickly find and vote for my preferred team without scrolling through all options

## Functional Requirements

### Search Input
- Display search input field above team list
- Placeholder text: "Search teams..."
- Clear button (X) appears when text is entered
- Search is case-insensitive
- Minimum 0 characters to trigger filter (instant filtering)

### Filtering Behavior
- Filter teams in real-time as user types
- Match team names containing the search term (substring match)
- Update filtered results immediately (no debounce delay)
- Show "No teams found" message when filter returns zero results
- Preserve original team order in filtered results

### Search Scope
- Search applies to team name field only
- Does not search team descriptions, locations, or other metadata

## Technical Requirements

### Frontend Component
```javascript
// SearchBar component
- Input field with onChange handler
- Clear button with onClick handler
- State management for search term
```

### Filtering Logic
```javascript
const filteredTeams = teams.filter(team => 
  team.name.toLowerCase().includes(searchTerm.toLowerCase())
);
```

### UI/UX Requirements
- Search input width: 100% of container
- Input height: 40px
- Border: 1px solid #ccc, focus: 2px solid primary color
- Clear button: positioned absolute right, visible only when text present
- Empty state message: centered, gray text

## Acceptance Criteria

**GIVEN** a user is on the voting page with multiple teams displayed  
**WHEN** the user types "Man" in the search field  
**THEN** only teams with "Man" in their name are displayed (e.g., "Manchester United", "Manchester City")

**GIVEN** a user has entered search text  
**WHEN** the user clicks the clear button (X)  
**THEN** the search field is cleared and all teams are displayed again

**GIVEN** a user searches for a term with no matches  
**WHEN** the filter returns zero results  
**THEN** display "No teams found matching '[search term]'"

**GIVEN** a user has filtered the team list  
**WHEN** real-time vote counts update  
**THEN** the filtered view persists and vote counts update correctly

## Implementation Notes

### State Management
- Add `searchTerm` state to voting component
- Pass filtered team list to display component
- Preserve search term during vote submission

### Performance
- No debouncing required (filter is fast for typical team counts)
- Consider debouncing if team list exceeds 1000 items

### Accessibility
- Search input has `aria-label="Search teams"`
- Clear button has `aria-label="Clear search"`
- Results count announced to screen readers

## Testing Requirements

### Unit Tests
- Filter returns correct teams for partial match
- Filter is case-insensitive
- Empty search returns all teams
- No matches returns empty array

### Integration Tests
- Search input updates filtered list
- Clear button resets search
- Voting works with filtered list
- Real-time updates work with active filter

## Dependencies
- Existing team list component
- Material-UI TextField component (per TECH-STACK.MD)

## Estimated Effort
- Frontend implementation: 2-3 hours
- Testing: 1-2 hours
- Total: 3-5 hours
