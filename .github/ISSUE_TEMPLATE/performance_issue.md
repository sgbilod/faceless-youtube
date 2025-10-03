---
name: Performance Issue
about: Report performance problems or optimization opportunities
title: '[PERF] '
labels: performance
assignees: ''
---

## ⚡ Performance Issue

A clear and concise description of the performance problem.

## 📊 Current Performance

**Measured metrics:**
- Response time: ___ ms
- Memory usage: ___ MB
- CPU usage: ___% 
- Database queries: ___ queries
- API calls: ___ calls

## 🎯 Expected Performance

**Target metrics:**
- Response time: < ___ ms
- Memory usage: < ___ MB
- CPU usage: < ___%
- Database queries: < ___ queries
- API calls: < ___ calls

## 🔍 Affected Component

- [ ] Video Generation
- [ ] Script Generation
- [ ] Asset Scraper
- [ ] Database Queries
- [ ] API Endpoints
- [ ] Multi-Platform Publisher
- [ ] Analytics Engine
- [ ] UI/Frontend
- [ ] Other: ___________

## 📋 Steps to Reproduce

1. Go to '...'
2. Perform action '...'
3. Observe performance issue

## 📈 Profiling Data

```python
# Paste profiling output, cProfile results, or flamegraphs
```

## 🔬 Analysis

**Root cause (if known):**
- N+1 query problem
- Missing index
- Inefficient algorithm
- Memory leak
- External API slowness
- Other: ___________

## 💡 Proposed Optimization

Describe potential solutions:

1. **Solution 1:** Add database index
   - Impact: -50% query time
   - Effort: Low
   
2. **Solution 2:** Implement caching
   - Impact: -80% response time
   - Effort: Medium

## 🧪 Benchmarks

If you've tested optimizations, share results:

**Before:**
```
Metric: Value
```

**After:**
```
Metric: Improved Value
```

## 🖥️ Environment

- OS: [e.g. Windows 11]
- Python Version: [e.g. 3.11.5]
- Database: [e.g. PostgreSQL 15]
- Dataset size: [e.g. 10K videos, 50K assets]
- Hardware: [e.g. 16GB RAM, 8-core CPU]

## 🎯 Priority

- [ ] Critical (app unusable)
- [ ] High (major slowdown)
- [ ] Medium (noticeable lag)
- [ ] Low (minor optimization)

## ✔️ Checklist

- [ ] I have measured actual performance metrics
- [ ] I have identified the bottleneck
- [ ] I have profiled the code
- [ ] I have considered optimization options
- [ ] This is not a hardware limitation
