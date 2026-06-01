# 📘 Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),  
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.16] - 2026-05-25

### Fixed
- 🐞 **Dashboard Infinite Reactive Loop**: Fixed recursive rendering loop in `Dashboard.svelte` by replacing `$_(key, options)` self-reference inside the derived `i18n` store with the direct `$i18n.t` method, resolving browser stack overflow RangeErrors.
- 🎨 **Dashboard HTML Markup Syntax**: Restored missing `>` tag bracket on card headers inside `Dashboard.svelte`, clearing linter parse errors.
- 🧩 **Assignments Dashboard Git Alignment**: Resolved structural git merge conflicts inside `Assignments.svelte`. Blended local Quiz Taking engine with the remote Assignments Dashboard list using a robust router state manager, resolving linter block syntax errors.
- 🛠️ **Vite Proxy Key Sanitization**: Removed validation warnings for duplicate key `target` inside `vite.config.ts` proxy object, securing standard APIs routing and WebSocket (`ws://`) channels.
- 🗄️ **Database Schema Conflict Markers**: Purged git conflict boundary text from `database.py` while fully retaining both `Quiz` related tables and `CourseProgress` tracking schema.

## [0.0.1] - 2025-05-12

### Added
- 👩‍🎓 **Student onboarding features**: profile creation, course joining, AI tutor setup, and learning start.
- 🏠 **Learner Space**: personal hub with progress tracking, AI help, and peer interaction.
- 📊 **Smart Dashboard**: deadlines, achievements, and learning overview at a glance.
- 📚 **Course Library**: manage and access all enrolled courses.
- 🧩 **Supports (Personalized Tutorials)**: custom learning paths powered by AI.
- 📝 **Assignment Central**: task management with feedback, deadlines, and points.
- 💬 **Connect & Learn**: messaging system with group and private chat.
- 🤖 **AI Chat Magic**: 24/7 interactive AI tutor with engagement tracking.
- 🌐 **3D Learning World**: immersive learning with avatars and visual lessons.
- ⚙️ **Settings Hub**: profile customization, themes, and privacy controls.
- 🚀 **Smart Tips & Quick Start Guide**: intuitive walkthrough for new learners.

### Fixed
- ✅ Project setup initialized.
- 🧭 Centralized App Launcher in `open_tutorai/main.py` (using `open_webui` as submodule).
- 📁 Corrected data directory structure — now handled in backend, not `openweb-ui`.

### Changed
- 🎨 Updated OpenTutor AI interface and features.