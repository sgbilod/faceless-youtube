# Pull Request

## 📋 Description

<!-- Provide a clear and concise description of your changes -->

## 🎯 Type of Change

<!-- Mark the relevant option with an 'x' -->

- [ ] 🐛 Bug fix (non-breaking change which fixes an issue)
- [ ] ✨ New feature (non-breaking change which adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] 📝 Documentation update
- [ ] 🎨 Code style/formatting
- [ ] ♻️ Code refactoring (no functional changes)
- [ ] ⚡ Performance improvement
- [ ] ✅ Test addition/update
- [ ] 🔧 Configuration change
- [ ] 🔒 Security fix

## 🔗 Related Issues

<!-- Link related issues here. Use "Fixes #123" or "Closes #123" to auto-close issues -->

Fixes #
Related to #

## 🧪 Testing

### Test Coverage

- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] End-to-end tests added/updated
- [ ] Manual testing performed

### Test Results

```bash
# Paste test output here
pytest -v
```

**Coverage:** \_\_\_%

## 📸 Screenshots/Videos (if applicable)

<!-- Add screenshots or videos to demonstrate changes -->

## 💡 Implementation Details

<!-- Describe the technical implementation -->

### Key Changes

1. **Component A:** Description of changes
2. **Component B:** Description of changes
3. **Component C:** Description of changes

### Architecture Impact

- [ ] Database schema changes (migration included)
- [ ] API changes (documentation updated)
- [ ] Configuration changes (`.env.example` updated)
- [ ] Dependencies added/updated (`requirements.txt` updated)
- [ ] Breaking changes (BREAKING.md updated)

## 💰 Cost Impact

<!-- Estimate cost impact of this change -->

- [ ] No cost impact (FREE)
- [ ] Increases costs by $\_\_\_/month
- [ ] Reduces costs by $\_\_\_/month
- [ ] Cost analysis needed

**Justification:** <!-- Explain cost impact -->

## ⚡ Performance Impact

<!-- Describe performance changes -->

- [ ] No performance impact
- [ ] Improves performance
- [ ] May impact performance (benchmarks provided)

**Metrics:**

- Response time: Before **_ ms → After _** ms
- Memory usage: Before **_ MB → After _** MB
- Database queries: Before **_ → After _**

## 🔒 Security Considerations

- [ ] No security impact
- [ ] Security vulnerability fixed
- [ ] New security measures added
- [ ] Credentials/secrets properly handled
- [ ] Input validation implemented
- [ ] SQL injection prevention verified
- [ ] XSS prevention verified

## 📚 Documentation

- [ ] Code comments added/updated
- [ ] README.md updated
- [ ] ARCHITECTURE.md updated (if architectural changes)
- [ ] DATABASE.md updated (if database changes)
- [ ] API documentation updated (if API changes)
- [ ] Changelog updated (CHANGELOG.md)

## ✅ Pre-Merge Checklist

### Code Quality

- [ ] Code follows project style guide (Black, Ruff)
- [ ] Type hints added (mypy compliant)
- [ ] Docstrings added for all functions/classes
- [ ] No commented-out code
- [ ] No debug print statements
- [ ] Error handling implemented
- [ ] Logging added for important operations

### Testing

- [ ] All tests pass locally
- [ ] CI/CD pipeline passes
- [ ] Test coverage >= 90%
- [ ] No test warnings
- [ ] Edge cases tested

### Git Hygiene

- [ ] Commits are atomic and well-described
- [ ] Commit messages follow convention
- [ ] Branch is up-to-date with main/develop
- [ ] No merge conflicts
- [ ] `.gitignore` updated if needed

### Deployment

- [ ] Database migrations tested
- [ ] Rollback plan documented
- [ ] Feature flags used (if applicable)
- [ ] Monitoring/alerting added
- [ ] Environment variables documented

### Review

- [ ] Self-review completed
- [ ] Screenshots/videos added (if UI changes)
- [ ] Breaking changes documented
- [ ] Migration guide provided (if needed)

## 🚀 Deployment Notes

<!-- Any special deployment instructions? -->

- [ ] Requires database migration
- [ ] Requires configuration changes
- [ ] Requires dependency installation
- [ ] Requires service restart
- [ ] Requires data migration

**Migration steps:**

```bash
# Add migration steps here
```

## 🔄 Rollback Plan

<!-- How to rollback if this breaks production? -->

```bash
# Add rollback steps here
alembic downgrade -1
```

## 📝 Additional Notes

<!-- Any other information reviewers should know -->

## 👥 Reviewers

<!-- Tag specific reviewers if needed -->

@username - Please review for [architecture/performance/security]

---

## 🤖 AI Assistant Note

<!-- For Copilot/AI assistants reviewing code -->

**AI Review Focus:**

- [ ] Code quality and best practices
- [ ] Cost optimization opportunities
- [ ] Performance optimization opportunities
- [ ] Security vulnerabilities
- [ ] Test coverage gaps

---

**By submitting this PR, I confirm:**

- ✅ I have read the CONTRIBUTING.md guidelines
- ✅ My code follows the project's coding standards
- ✅ I have performed a self-review of my code
- ✅ I have tested my changes thoroughly
- ✅ My changes generate no new warnings
- ✅ I have added tests that prove my fix is effective or that my feature works
- ✅ New and existing unit tests pass locally with my changes
- ✅ I have made corresponding changes to the documentation
