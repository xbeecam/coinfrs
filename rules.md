# Rules.md - Development Guidelines for Coinfrs

This document outlines the development workflow and best practices for all developers working on the Coinfrs project, including AI assistants.

## Development Workflow

### 1. Problem Analysis & Planning
**Before writing any code:**
- Thoroughly analyze the problem or feature request
- Read and understand relevant files in the codebase
- Create a detailed plan in `todo.md` with specific, actionable items

### 2. Todo List Structure
Your `todo.md` should include:
- [ ] Clear, specific tasks that can be checked off
- [ ] Tasks ordered by dependency and logical flow
- [ ] Each task should be small and focused
- [ ] Include subtasks where necessary for complex items

**Important**: Keep historical records of all tasks. Never replace the entire todo.md file. Instead:
- Append new tasks for new features/weeks
- Update task statuses in place
- Preserve completed tasks for audit trail
- Add timestamps or week markers to separate different work periods

### 3. Plan Verification
**Before implementation:**
- Present your plan to the project lead
- Get explicit approval before proceeding
- Adjust the plan based on feedback if needed

### 4. Implementation Process
**While working:**
- Complete one todo item at a time
- Mark items as complete as you finish them
- Update status in real-time (pending → in_progress → completed)
- Never batch multiple completions

### 5. Change Documentation
**For every step completed:**
- Provide a high-level explanation of what changed
- Explain why the change was made
- Note any impacts on other parts of the system
- Keep explanations concise but informative

### 6. Code Simplicity Principles
**Every change must:**
- Be as simple as possible
- Impact the minimum amount of code
- Avoid complex or clever solutions
- Prioritize readability and maintainability
- Use existing patterns and libraries in the codebase

### 7. Review & Summary
**After completing all tasks:**
- Add a "Review" section to `todo.md`
- Summarize all changes made
- Note any deviations from the original plan
- Document any issues encountered
- List any follow-up tasks needed

## Example todo.md Structure

```markdown
# Task: [Feature/Fix Description]

## Plan
1. [ ] Analyze existing code structure
2. [ ] Implement core functionality
3. [ ] Add error handling
4. [ ] Write tests
5. [ ] Update documentation

## Progress Notes
- Step 1: Read files X, Y, Z. Found that...
- Step 2: Implemented feature by...

## Review
### Summary of Changes
- Modified files: A, B, C
- Added new functionality for...
- Fixed issue with...

### Key Decisions
- Chose approach X because...
- Avoided Y due to...

### Follow-up Tasks
- Consider adding...
- May need to optimize...
```

## Additional Guidelines

### For High-Frequency Trading (HFT) Features
- Always consider performance implications
- Document expected transaction volumes
- Test with realistic data loads
- Profile critical paths

### Security Considerations
- Never commit API keys or secrets
- Use environment variables for sensitive data
- Follow AES-256 encryption standards for POC
- Plan for cloud secret management in production

### Testing & Validation
- Run linting before marking tasks complete
- Execute type checking (if applicable)
- Test with edge cases
- Verify no regressions

### Communication
- Ask for clarification when requirements are unclear
- Report blockers immediately
- Provide regular status updates
- Document assumptions made

## Commands to Remember

```bash
# Common commands for the project
npm run lint        # Run linting
npm run typecheck   # Run type checking
npm test           # Run tests
```

## File Organization
- Keep related files together
- Follow existing naming conventions
- Update imports when moving files
- Maintain clean directory structure

## Git Workflow (When Applicable)
- Make atomic commits
- Write clear commit messages
- Never commit directly to main
- Create feature branches

---

*Last Updated: 2025-07-16*
*This document should be updated as the project evolves and new patterns emerge.*