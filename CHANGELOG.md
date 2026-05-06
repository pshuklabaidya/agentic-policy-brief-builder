# Changelog

All notable changes to this project will be documented in this file.

This project follows a practical, human-readable changelog format inspired by [Keep a Changelog](https://keepachangelog.com/) and uses semantic-version-style release labels.

## [Unreleased]

### Added

- Release notes and portfolio documentation for public project review.
- Portfolio overview, interview talk track, limitations, and roadmap documentation.

### Changed

- README refreshed from template-style starter content into a finished project overview.

### Fixed

- Clarified demo scope, validation gates, and non-production boundaries across public docs.

### Security

- Reinforced responsible-use notes and the expectation that secrets and private data must not be committed.

## [0.1.0] - Portfolio-ready baseline

### Added

- Streamlit Agentic RAG demo for generating cited policy briefs from local policy documents.
- Synthetic Riverton policy packet for safe public demos without private or employer data.
- TXT/PDF ingestion, document chunking, local vector retrieval, and cited brief drafting workflow.
- Citation audit utilities that check whether generated brief citations map back to retrieved evidence.
- Markdown formatting and download support for generated briefs, retrieved evidence, and citation-audit output.
- Deterministic local evaluation runner using synthetic fixtures and fake clients.
- GitHub Actions CI workflow for Ruff, pytest, local evals, repository-health checks, and release-readiness checks.
- Repository-health and release-readiness scripts for portfolio review.

### Documentation

- Setup, CI, local evaluation, security, contribution, and release-readiness documentation.
- Synthetic-data disclosure for public demo materials.

### Security

- `.env.example` documents required configuration without committing secrets.
- Health checks flag obvious secret-bearing files and generated local artifacts.
