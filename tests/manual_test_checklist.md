# Manual Test Checklist

## Authentication & Profile
- [ ] User can successfully log in
- [ ] User can log out
- [ ] User can view their profile
- [ ] User can edit profile information
- [ ] Profile changes are persisted after logout/login

## Chat Functionality
- [ ] New conversation can be started
- [ ] Messages are sent and received correctly
- [ ] Chat history loads properly
- [ ] Long conversations scroll smoothly
- [ ] Code blocks are properly formatted
- [ ] Images/attachments display correctly

## Human Verification
- [ ] Verification process triggers appropriately
- [ ] User can complete verification successfully
- [ ] Failed verification handled gracefully
- [ ] Verification status persists correctly

## Configuration
- [ ] User can view configuration settings
- [ ] Changes to settings are saved
- [ ] Settings persist across sessions
- [ ] Invalid configurations are handled properly

## Beta Features
- [ ] Beta tester access works correctly
- [ ] Beta features are properly gated
- [ ] Beta feedback submission works

## Leaderboard
- [ ] Leaderboard displays correctly
- [ ] Scores update appropriately
- [ ] User rankings are accurate

## Research & Bounties
- [ ] Research proposals can be submitted
- [ ] Bounties are displayed correctly
- [ ] Bounty submission process works
- [ ] Bounty rewards are properly tracked

## Error Handling
- [ ] Invalid inputs are handled gracefully
- [ ] Network errors show appropriate messages
- [ ] Rate limiting works as expected
- [ ] Error messages are clear and helpful

## Performance
- [ ] Pages load within acceptable time
- [ ] No memory leaks in long sessions
- [ ] API responses are timely
- [ ] Large data sets handle smoothly

## Cross-browser Testing
- [ ] Works in Chrome
- [ ] Works in Firefox
- [ ] Works in Safari
- [ ] Works in Edge

## Mobile Responsiveness
- [ ] Layout adapts to mobile screens
- [ ] Touch interactions work properly
- [ ] Forms are usable on mobile
- [ ] No horizontal scrolling issues

## Notes
- Complete this checklist before deploying major changes
- Document any failures or issues found
- Update checklist as new features are added
- Mark tests as N/A if feature is not included in current release