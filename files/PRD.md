# PRD.md — EngageSphere Project Requirements Document

## Summary
EngageSphere is an AI-powered, multi-platform customer engagement system for business owners. It automatically generates and posts thoughtful, brand-appropriate replies to customer reviews and comments across Google Maps, Facebook, Instagram, and Twitter — all managed from a single unified dashboard. Each platform is handled by its own connector agent, feeding into a shared AI reply-generation core, so every customer touchpoint gets a timely, consistent, satisfaction-focused response. Beyond replies, EngageSphere analyzes customer sentiment across all channels to give business owners actionable suggestions for improving their service and reputation.

## Problem Statement
Small and medium business owners get customer feedback scattered across many platforms — Google Maps reviews, Facebook comments, Instagram comments, Twitter mentions. Responding to each one manually, quickly, and in a consistent tone is time-consuming and often neglected, which hurts customer satisfaction and public reputation. There is no single tool that reads feedback from all these channels, replies appropriately, and tells the owner what to actually improve.

## Target Users
- Small and medium business owners (restaurants, retail, hospitality, services) who are active on multiple social/review platforms
- Business social media managers who currently reply manually across platforms
- (For this project) A dummy business created specifically to demo the system with real connected handles

## Goals
- Reduce response time to customer feedback across all platforms to near-zero
- Keep replies consistent in tone and aligned with the business's brand voice
- Surface actionable, evidence-backed suggestions for business improvement from aggregated feedback
- Demonstrate a working, modular, multi-platform architecture (not a single-platform bot)

## Core Features
1. **Multi-Platform Data Ingestion**
   - Google Maps reviews (simulated/mock dataset — business verification not feasible in project timeline)
   - Facebook Page comments (live, via Graph API on a dummy Facebook Page)
   - Instagram Business comments (live, via Graph API on a dummy Instagram Business account)
   - Twitter/X mentions (simulated/mock dataset — API pricing not feasible for student project)

2. **AI Reply-Generation Agent**
   - Reads incoming review/comment text
   - Determines sentiment and intent
   - Generates a brand-appropriate, satisfaction-focused reply
   - Optionally grounds replies in business-specific info (hours, policies, menu, etc.) via RAG

3. **Platform Connector Modules**
   - Independent, pluggable modules per platform that fetch feedback and post replies
   - Live connectors: Facebook, Instagram
   - Simulated connectors: Google Maps, Twitter

4. **Unified Dashboard**
   - Single view of all incoming reviews/comments across platforms
   - Shows AI-generated reply per item, with option to approve/edit before posting
   - Sentiment breakdown across all channels combined

5. **Suggestion Agent**
   - Analyzes aggregated customer feedback across all platforms
   - Surfaces recurring themes/issues
   - Generates actionable, evidence-backed suggestions for the business owner

## Out of Scope (for this project)
- Fully automated posting without any human review (safety: auto-reply should support an approve/edit step, not blind auto-post, especially for negative feedback)
- Real Google Business Profile verification and live posting (simulated instead)
- Live Twitter/X API integration (simulated instead)
- Multi-business/tenant production deployment (single dummy business for demo)

## Success Criteria
- Dashboard shows aggregated feedback from at least 2 live-connected platforms (Facebook, Instagram) and 2 simulated platforms (Google Maps, Twitter)
- AI-generated replies are contextually appropriate and tonally consistent
- Suggestion Agent produces at least 3 actionable, evidence-backed recommendations per demo run
- End-to-end demo is completable within a reasonable time window for a panel presentation
