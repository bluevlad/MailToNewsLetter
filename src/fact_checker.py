"""
Fact Checker Module using Google Custom Search API

This module verifies the accuracy of newsletter content by:
1. Extracting key claims from AI-generated summaries
2. Searching for corroborating sources via Google Custom Search
3. Calculating a confidence score based on source reliability
"""

import os
import re
import logging
import requests
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class VerificationResult:
    """Result of fact verification for a single claim"""
    claim: str
    verified: bool
    confidence: float  # 0.0 - 1.0
    sources: List[Dict[str, str]]  # [{'title': ..., 'url': ..., 'snippet': ...}]
    status: str  # 'verified', 'partially_verified', 'unverified', 'conflicting'


@dataclass
class FactCheckReport:
    """Complete fact-check report for a newsletter item"""
    topic: str
    overall_confidence: float
    verification_results: List[VerificationResult]
    reliable_sources: List[Dict[str, str]]
    warnings: List[str]


class FactChecker:
    """
    Fact-checking service using Google Custom Search API.

    Usage:
        checker = FactChecker()
        report = checker.verify_content(topic, ai_summary)
    """

    # Domains considered highly reliable for tech content
    TRUSTED_DOMAINS = {
        'official': [
            'docs.python.org', 'docs.oracle.com', 'developer.mozilla.org',
            'learn.microsoft.com', 'cloud.google.com', 'aws.amazon.com',
            'kubernetes.io', 'docker.com', 'spring.io', 'redis.io',
            'kafka.apache.org', 'postgresql.org', 'github.com'
        ],
        'educational': [
            'geeksforgeeks.org', 'baeldung.com', 'tutorialspoint.com',
            'w3schools.com', 'freecodecamp.org', 'stackoverflow.com'
        ],
        'news': [
            'techcrunch.com', 'wired.com', 'arstechnica.com',
            'theverge.com', 'zdnet.com', 'infoworld.com'
        ]
    }

    def __init__(self):
        self.api_key = os.getenv('GOOGLE_SEARCH_API_KEY')
        self.cx = os.getenv('GOOGLE_SEARCH_CX')

        if not self.api_key or not self.cx:
            logging.warning(
                "Google Search API credentials not found. "
                "Set GOOGLE_SEARCH_API_KEY and GOOGLE_SEARCH_CX in .env"
            )

    def is_configured(self) -> bool:
        """Check if the API is properly configured"""
        return bool(self.api_key and self.cx)

    def search(self, query: str, num_results: int = 5) -> List[Dict]:
        """
        Search using Google Custom Search API.

        Args:
            query: Search query string
            num_results: Number of results to return (max 10)

        Returns:
            List of search results with title, link, and snippet
        """
        if not self.is_configured():
            logging.error("Google Search API not configured")
            return []

        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'key': self.api_key,
            'cx': self.cx,
            'q': query,
            'num': min(num_results, 10)
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get('items', []):
                results.append({
                    'title': item.get('title', ''),
                    'url': item.get('link', ''),
                    'snippet': item.get('snippet', ''),
                    'domain': self._extract_domain(item.get('link', ''))
                })

            return results

        except requests.exceptions.RequestException as e:
            logging.error(f"Google Search API error: {e}")
            return []

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc.replace('www.', '')
            return domain
        except Exception:
            return ''

    def _get_domain_trust_score(self, domain: str) -> float:
        """
        Calculate trust score based on domain.

        Returns:
            Score from 0.0 to 1.0
        """
        for category, domains in self.TRUSTED_DOMAINS.items():
            for trusted in domains:
                if trusted in domain:
                    if category == 'official':
                        return 1.0
                    elif category == 'educational':
                        return 0.8
                    elif category == 'news':
                        return 0.7
        return 0.5  # Unknown domain

    def extract_key_claims(self, text: str) -> List[str]:
        """
        Extract key factual claims from text using heuristics.

        Looks for:
        - Statements with numbers/statistics
        - Technology comparisons
        - Performance claims
        - Best practices statements
        """
        claims = []

        # Split into sentences
        sentences = re.split(r'[.!?]\s+', text)

        for sentence in sentences:
            # Skip short sentences
            if len(sentence) < 20:
                continue

            # Patterns that indicate factual claims
            claim_patterns = [
                r'\d+%',  # Percentages
                r'\d+x\s',  # Multipliers (e.g., "10x faster")
                r'\d+\s*(ms|seconds?|minutes?|hours?)',  # Time measurements
                r'(faster|slower|better|worse)\s+than',  # Comparisons
                r'(always|never|must|should)\s+',  # Strong statements
                r'(increase|decrease|improve|reduce).*\d+',  # Quantified changes
            ]

            for pattern in claim_patterns:
                if re.search(pattern, sentence, re.IGNORECASE):
                    claims.append(sentence.strip())
                    break

        # Also extract first 3 sentences as main claims
        main_sentences = [s.strip() for s in sentences[:3] if len(s.strip()) > 30]
        claims = list(set(claims + main_sentences))[:5]  # Limit to 5 claims

        return claims

    def verify_claim(self, claim: str, topic: str) -> VerificationResult:
        """
        Verify a single claim using Google Search.

        Args:
            claim: The factual claim to verify
            topic: Original topic for context

        Returns:
            VerificationResult with sources and confidence
        """
        # Create search query from claim
        # Remove common filler words for better search
        search_query = f"{topic} {claim[:100]}"

        results = self.search(search_query, num_results=5)

        if not results:
            return VerificationResult(
                claim=claim,
                verified=False,
                confidence=0.0,
                sources=[],
                status='unverified'
            )

        # Calculate confidence based on:
        # 1. Number of corroborating sources
        # 2. Trust level of sources
        # 3. Relevance of snippets

        trust_scores = []
        relevant_sources = []

        for result in results:
            domain_score = self._get_domain_trust_score(result['domain'])
            trust_scores.append(domain_score)

            # Check if snippet is relevant to the claim
            claim_words = set(claim.lower().split())
            snippet_words = set(result['snippet'].lower().split())
            overlap = len(claim_words & snippet_words) / max(len(claim_words), 1)

            if overlap > 0.2 or domain_score >= 0.8:
                relevant_sources.append(result)

        # Calculate overall confidence
        if not trust_scores:
            confidence = 0.0
        else:
            avg_trust = sum(trust_scores) / len(trust_scores)
            source_bonus = min(len(relevant_sources) * 0.1, 0.3)
            confidence = min(avg_trust + source_bonus, 1.0)

        # Determine status
        if confidence >= 0.7:
            status = 'verified'
            verified = True
        elif confidence >= 0.4:
            status = 'partially_verified'
            verified = True
        else:
            status = 'unverified'
            verified = False

        return VerificationResult(
            claim=claim,
            verified=verified,
            confidence=confidence,
            sources=relevant_sources[:3],
            status=status
        )

    def verify_content(self, topic: str, summary: str) -> FactCheckReport:
        """
        Perform full fact-check on newsletter content.

        Args:
            topic: The main topic/title
            summary: AI-generated summary to verify

        Returns:
            FactCheckReport with all verification results
        """
        if not self.is_configured():
            return FactCheckReport(
                topic=topic,
                overall_confidence=0.0,
                verification_results=[],
                reliable_sources=[],
                warnings=['Google Search API not configured. Fact-checking disabled.']
            )

        # Extract claims to verify
        claims = self.extract_key_claims(summary)

        if not claims:
            return FactCheckReport(
                topic=topic,
                overall_confidence=0.5,
                verification_results=[],
                reliable_sources=[],
                warnings=['No specific claims found to verify.']
            )

        # Verify each claim
        verification_results = []
        all_sources = []

        for claim in claims:
            result = self.verify_claim(claim, topic)
            verification_results.append(result)
            all_sources.extend(result.sources)

        # Calculate overall confidence
        if verification_results:
            confidences = [r.confidence for r in verification_results]
            overall_confidence = sum(confidences) / len(confidences)
        else:
            overall_confidence = 0.5

        # Collect unique reliable sources
        seen_urls = set()
        reliable_sources = []
        for source in all_sources:
            if source['url'] not in seen_urls:
                seen_urls.add(source['url'])
                if self._get_domain_trust_score(source['domain']) >= 0.7:
                    reliable_sources.append(source)

        # Generate warnings
        warnings = []
        unverified_count = sum(1 for r in verification_results if r.status == 'unverified')
        if unverified_count > 0:
            warnings.append(f'{unverified_count} claim(s) could not be verified.')
        if overall_confidence < 0.5:
            warnings.append('Overall confidence is low. Manual review recommended.')

        return FactCheckReport(
            topic=topic,
            overall_confidence=overall_confidence,
            verification_results=verification_results,
            reliable_sources=reliable_sources[:5],
            warnings=warnings
        )

    def format_report_html(self, report: FactCheckReport) -> str:
        """
        Format fact-check report as HTML for newsletter inclusion.
        """
        html = ['<div class="fact-check">']
        html.append('<h4>🔍 Fact-Check Report</h4>')

        # Confidence meter
        confidence_pct = int(report.overall_confidence * 100)
        confidence_color = (
            '#27ae60' if confidence_pct >= 70 else
            '#f39c12' if confidence_pct >= 40 else
            '#e74c3c'
        )
        html.append(f'''
            <div class="confidence-meter" style="margin-bottom: 10px;">
                <span style="font-weight: bold;">Confidence: </span>
                <span style="color: {confidence_color}; font-weight: bold;">{confidence_pct}%</span>
                <div style="background: #eee; height: 8px; border-radius: 4px; margin-top: 4px;">
                    <div style="background: {confidence_color}; width: {confidence_pct}%; height: 100%; border-radius: 4px;"></div>
                </div>
            </div>
        ''')

        # Verification results
        if report.verification_results:
            html.append('<div class="verifications" style="font-size: 0.9em; margin-bottom: 10px;">')
            for result in report.verification_results[:3]:
                icon = (
                    '✓' if result.status == 'verified' else
                    '⚠' if result.status == 'partially_verified' else
                    '✗'
                )
                color = (
                    '#27ae60' if result.status == 'verified' else
                    '#f39c12' if result.status == 'partially_verified' else
                    '#e74c3c'
                )
                claim_preview = result.claim[:80] + '...' if len(result.claim) > 80 else result.claim
                html.append(f'<div style="margin: 4px 0;"><span style="color: {color};">{icon}</span> {claim_preview}</div>')
            html.append('</div>')

        # Reliable sources
        if report.reliable_sources:
            html.append('<div class="sources" style="font-size: 0.85em; color: #666;">')
            html.append('<p style="margin-bottom: 5px; font-weight: bold;">📚 Verified Sources:</p>')
            for source in report.reliable_sources[:3]:
                html.append(f'<div style="margin: 2px 0;"><a href="{source["url"]}" target="_blank" style="color: #3498db;">• {source["title"][:50]}...</a></div>')
            html.append('</div>')

        # Warnings
        if report.warnings:
            html.append('<div class="warnings" style="font-size: 0.85em; color: #e74c3c; margin-top: 8px;">')
            for warning in report.warnings:
                html.append(f'<div>⚠ {warning}</div>')
            html.append('</div>')

        html.append('</div>')
        return '\n'.join(html)

    def format_report_text(self, report: FactCheckReport) -> str:
        """
        Format fact-check report as plain text.
        """
        lines = []
        lines.append("━" * 40)
        lines.append("🔍 FACT-CHECK REPORT")
        lines.append("━" * 40)

        confidence_pct = int(report.overall_confidence * 100)
        lines.append(f"Overall Confidence: {confidence_pct}%")
        lines.append("")

        if report.verification_results:
            lines.append("Verification Results:")
            for result in report.verification_results:
                icon = '✓' if result.verified else '✗'
                lines.append(f"  {icon} [{result.status}] {result.claim[:60]}...")

        if report.reliable_sources:
            lines.append("")
            lines.append("Verified Sources:")
            for source in report.reliable_sources[:3]:
                lines.append(f"  • {source['title'][:50]}...")
                lines.append(f"    {source['url']}")

        if report.warnings:
            lines.append("")
            lines.append("Warnings:")
            for warning in report.warnings:
                lines.append(f"  ⚠ {warning}")

        lines.append("━" * 40)
        return '\n'.join(lines)
