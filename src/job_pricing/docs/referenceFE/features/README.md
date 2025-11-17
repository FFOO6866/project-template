# Features Directory

This directory contains feature modules for the Talent Verse dashboard. Each feature is self-contained with its own components, services, and state management.

## Feature Modules

| Module | Description | Status | API Endpoints | Shared Functions |
|--------|-------------|--------|--------------|------------------|
| Executive Summary | Overview dashboard with key metrics | Completed | None | MetricCard, InsightCard |
| Strategic Alignment | Visualization of HR initiatives linked to goals | Completed | None | None |
| E-Dossier & Coaching | Interactive career timeline and psychometric data | Completed | None | None |
| MT Profiles | Management Team profiles and team dynamics | Completed | None | TeamMemberCard, TeamComparisonChart, TeamNetworkGraph |
| MT Document Management | Document storage and directory linking for MT profiles | Completed | None | DocumentDirectoryForm |
| MT Performance Matrix | Comprehensive performance frameworks (Quantum Leadership, Mintzberg, 4 Mindsets, IRTF, AACC, etc.) | Completed | None | Multiple visualization components |
| MT Assessment Admin | Admin module to update assessment center data | Completed | None | AssessmentForm |
| RMRR Matching | *None yet* | Planned | | |

## Guidelines

1. Each feature module should be self-contained with:
   - Local UI components
   - Data models/types
   - API services and handlers
   - Tests
   - Local state logic (if required)

2. Shared logic should only be abstracted when repeatable across 2+ modules.

3. Before developing a new module:
   - Check this README for existing components or utilities
   - Reuse verified functions/scripts where possible
   - Avoid re-writing existing modules unless explicitly authorized

## Module Structure

\`\`\`
features/
  ├── module-name/
  │   ├── components/
  │   │   └── component.tsx
  │   ├── models/
  │   │   └── types.ts
  │   ├── services/
  │   │   └── api.ts
  │   ├── hooks/
  │   │   └── use-feature.ts
  │   └── index.ts
\`\`\`

## Performance Assessment Frameworks

The MT Performance Matrix module includes visualizations for the following TPC-specific assessment frameworks:

1. **Quantum Leadership Attributes** - Leadership capabilities across multiple dimensions
2. **Mintzberg Management Roles** - Interpersonal, informational, and decisional roles
3. **4 Mindsets Framework** - Fixed, Growth, Benefit, and Abundance mindsets
4. **Roles & Relationships** - Formal and informal influence across different roles
5. **IRTF Assessment** - In-search, Research, Think-through, Follow-through
6. **AACC Assessment** - Aware-Align-Collaborate-Co-create progression
7. **Team Dynamics** - Contribution to team effectiveness and collaboration
8. **Consciousness Shift** - Evolution through stages of awareness and consciousness

Each framework provides unique insights into individual performance and potential within the TPC context.
