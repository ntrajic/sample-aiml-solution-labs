# Team Search & League Filter - Implementation Tasks

## Phase 1: Core Search Functionality

### Task 1.1: Create TeamSearchBar Component
**File**: `src/components/TeamSearchBar.jsx`
- [ ] Create functional component with TextField
- [ ] Add Search icon (start adornment)
- [ ] Add Clear button (end adornment, conditional)
- [ ] Implement onChange handler
- [ ] Implement onClear handler
- [ ] Add ARIA labels
- [ ] Apply Material-UI styling

**Estimated Time**: 1 hour

### Task 1.2: Add Search State to VotingPage
**File**: `src/pages/VotingPage.jsx`
- [ ] Add `searchTerm` state with useState
- [ ] Create `handleSearchChange` function
- [ ] Create `handleClearSearch` function
- [ ] Import TeamSearchBar component
- [ ] Add TeamSearchBar to JSX above TeamList

**Estimated Time**: 30 minutes

### Task 1.3: Implement Team Filtering Logic
**File**: `src/pages/VotingPage.jsx`
- [ ] Create `filteredTeams` with useMemo
- [ ] Implement case-insensitive substring match
- [ ] Pass filteredTeams to TeamList component
- [ ] Add empty state message for no results

**Estimated Time**: 45 minutes

---

## Phase 2: League Filter Functionality

### Task 2.1: Create LeagueFilter Component
**File**: `src/components/LeagueFilter.jsx`
- [ ] Create functional component with Select dropdown
- [ ] Add "All Leagues" default option
- [ ] Map league options from teams data
- [ ] Implement onChange handler
- [ ] Add label "Filter by League"
- [ ] Apply Material-UI styling

**Estimated Time**: 1 hour

### Task 2.2: Add League Filter State
**File**: `src/pages/VotingPage.jsx`
- [ ] Add `selectedLeague` state with useState (default: 'all')
- [ ] Create `handleLeagueChange` function
- [ ] Import LeagueFilter component
- [ ] Add LeagueFilter to JSX

**Estimated Time**: 30 minutes

### Task 2.3: Combine Search and League Filters
**File**: `src/pages/VotingPage.jsx`
- [ ] Update useMemo to filter by both search AND league
- [ ] Apply league filter first, then search filter
- [ ] Update empty state message to reflect both filters
- [ ] Ensure filters work independently and together

**Estimated Time**: 45 minutes

---

## Phase 3: UI/UX Enhancements

### Task 3.1: Create Filter Container Layout
**File**: `src/pages/VotingPage.jsx`
- [ ] Create Grid/Box container for filters
- [ ] Position search bar (left, 70% width)
- [ ] Position league filter (right, 30% width)
- [ ] Add responsive breakpoints for mobile
- [ ] Add spacing between filters

**Estimated Time**: 45 minutes

### Task 3.2: Add Results Count Display
**File**: `src/pages/VotingPage.jsx`
- [ ] Add Typography component showing count
- [ ] Display "Showing X of Y teams"
- [ ] Add aria-live="polite" for screen readers
- [ ] Position below filters

**Estimated Time**: 30 minutes

### Task 3.3: Style Empty States
**File**: `src/pages/VotingPage.jsx`
- [ ] Create EmptyState component (optional)
- [ ] Add icon for empty state
- [ ] Style message text (centered, gray)
- [ ] Add "Clear filters" button when both active

**Estimated Time**: 45 minutes

---

## Phase 4: Testing

### Task 4.1: Unit Tests - TeamSearchBar
**File**: `src/components/TeamSearchBar.test.jsx`
- [ ] Test component renders
- [ ] Test onChange callback fires
- [ ] Test clear button appears with text
- [ ] Test clear button calls onClear
- [ ] Test ARIA labels present

**Estimated Time**: 1 hour

### Task 4.2: Unit Tests - LeagueFilter
**File**: `src/components/LeagueFilter.test.jsx`
- [ ] Test component renders
- [ ] Test options populate correctly
- [ ] Test onChange callback fires
- [ ] Test "All Leagues" default selected

**Estimated Time**: 45 minutes

### Task 4.3: Integration Tests - Combined Filtering
**File**: `src/pages/VotingPage.test.jsx`
- [ ] Test search filters teams by name
- [ ] Test league filter filters teams by league
- [ ] Test both filters work together (AND logic)
- [ ] Test empty state shows when no matches
- [ ] Test clear search resets search only
- [ ] Test changing league resets correctly
- [ ] Test filtered teams can be voted on

**Estimated Time**: 2 hours

### Task 4.4: Integration Tests - Real-time Updates
**File**: `src/pages/VotingPage.test.jsx`
- [ ] Test vote counts update with active search
- [ ] Test vote counts update with active league filter
- [ ] Test new teams appear in filtered view
- [ ] Test WebSocket updates don't reset filters

**Estimated Time**: 1 hour

---

## Phase 5: Accessibility & Polish

### Task 5.1: Keyboard Navigation
**File**: `src/pages/VotingPage.jsx`
- [ ] Test Tab navigation through filters
- [ ] Add Escape key to clear search (optional)
- [ ] Ensure focus management works correctly
- [ ] Test with keyboard-only navigation

**Estimated Time**: 45 minutes

### Task 5.2: Screen Reader Testing
- [ ] Test with NVDA/JAWS
- [ ] Verify filter changes announced
- [ ] Verify results count announced
- [ ] Verify empty state announced

**Estimated Time**: 1 hour

### Task 5.3: Mobile Responsiveness
**File**: `src/pages/VotingPage.jsx`
- [ ] Test filters stack vertically on mobile
- [ ] Test touch interactions work
- [ ] Adjust spacing for small screens
- [ ] Test with Chrome DevTools mobile view

**Estimated Time**: 45 minutes

---

## Phase 6: Documentation & Deployment

### Task 6.1: Update Documentation
**Files**: `IMPL-TASKS.MD`, `README.md`
- [ ] Mark search feature tasks complete
- [ ] Add league filter to feature list
- [ ] Document filter behavior
- [ ] Add screenshots/GIFs of filters

**Estimated Time**: 30 minutes

### Task 6.2: Code Review Preparation
- [ ] Run linter and fix issues
- [ ] Ensure all tests pass
- [ ] Check code coverage (aim for 80%+)
- [ ] Write PR description

**Estimated Time**: 30 minutes

### Task 6.3: Deployment
- [ ] Merge to main branch
- [ ] Deploy to staging environment
- [ ] Smoke test on staging
- [ ] Deploy to production
- [ ] Monitor for errors

**Estimated Time**: 1 hour

---

## Summary

### Total Estimated Time: 16-18 hours

### Task Breakdown by Phase:
- Phase 1 (Search): 2.25 hours
- Phase 2 (League Filter): 2.25 hours
- Phase 3 (UI/UX): 2 hours
- Phase 4 (Testing): 4.75 hours
- Phase 5 (Accessibility): 2.5 hours
- Phase 6 (Documentation): 2 hours

### Priority Order:
1. **P0 (Must Have)**: Phase 1, Phase 2, Task 4.3
2. **P1 (Should Have)**: Phase 3, Phase 4 (remaining), Phase 5.1
3. **P2 (Nice to Have)**: Phase 5.2, Phase 5.3, Phase 3.3

### Dependencies:
- Task 2.3 depends on Task 1.3 and Task 2.2
- Task 3.1 depends on Task 1.1 and Task 2.1
- Phase 4 depends on Phase 1 and Phase 2 completion
- Phase 6 depends on all previous phases

### Team Assignment Suggestion:
- **Developer 1**: Phase 1 + Phase 2 (core functionality)
- **Developer 2**: Phase 3 + Phase 5 (UI/UX + accessibility)
- **QA Engineer**: Phase 4 (testing)
- **Tech Lead**: Phase 6 (review + deployment)

### Risk Mitigation:
- Start with Phase 1 only, validate with stakeholders
- Add Phase 2 after Phase 1 approval
- Phase 3 enhancements can be done in parallel
- Testing can start once Phase 1 is complete
