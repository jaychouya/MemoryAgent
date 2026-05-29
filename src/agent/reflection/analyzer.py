"""
Sequence analyzer for discovering reusable patterns.

Uses sequence alignment algorithms to find recurring
patterns in tool call sequences.
"""

from typing import List, Dict, Tuple, Set
from collections import Counter
from dataclasses import dataclass
from .tracer import ExecutionTrace


@dataclass
class Pattern:
    """
    Represents a discovered pattern.
    
    Attributes:
        sequence: Tool call sequence
        frequency: How often this pattern occurs
        success_rate: Success rate of this pattern
        examples: Example trace IDs
        description: Human-readable description
    """
    sequence: List[str]
    frequency: int
    success_rate: float
    examples: List[str]
    description: str = ""
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "sequence": self.sequence,
            "frequency": self.frequency,
            "success_rate": self.success_rate,
            "examples": self.examples[:5],
            "description": self.description
        }
    
    @property
    def pattern_string(self) -> str:
        """Get pattern as string."""
        return " -> ".join(self.sequence)


class SequenceAnalyzer:
    """
    Analyzes tool call sequences to discover patterns.
    
    Features:
    - Frequent subsequence discovery
    - Success rate calculation
    - Pattern description generation
    """
    
    def __init__(
        self,
        min_pattern_length: int = 2,
        min_frequency: int = 3
    ):
        """
        Initialize analyzer.
        
        Args:
            min_pattern_length: Minimum pattern length to consider
            min_frequency: Minimum frequency to consider a pattern
        """
        self.min_pattern_length = min_pattern_length
        self.min_frequency = min_frequency
    
    def discover_patterns(
        self,
        traces: List[ExecutionTrace]
    ) -> List[Pattern]:
        """
        Discover recurring patterns in traces.
        
        Args:
            traces: List of execution traces
            
        Returns:
            List of discovered patterns
        """
        if not traces:
            return []
        
        # Extract all sequences
        sequences = [trace.tool_sequence for trace in traces]
        
        # Find frequent subsequences
        patterns = self._find_frequent_subsequences(sequences, traces)
        
        # Filter by minimum frequency
        patterns = [p for p in patterns if p.frequency >= self.min_frequency]
        
        # Sort by frequency
        patterns.sort(key=lambda p: p.frequency, reverse=True)
        
        return patterns
    
    def _find_frequent_subsequences(
        self,
        sequences: List[List[str]],
        traces: List[ExecutionTrace]
    ) -> List[Pattern]:
        """
        Find frequent subsequences using sliding window.
        
        Args:
            sequences: List of tool call sequences
            traces: Original traces for context
            
        Returns:
            List of patterns
        """
        pattern_counts: Counter = Counter()
        pattern_examples: Dict[str, List[str]] = {}
        pattern_success: Dict[str, int] = Counter()
        
        for i, seq in enumerate(sequences):
            # Generate subsequences of different lengths
            for length in range(self.min_pattern_length, min(len(seq) + 1, 6)):  # Max length 5
                for start in range(len(seq) - length + 1):
                    subseq = tuple(seq[start:start + length])
                    pattern_str = "->".join(subseq)
                    
                    pattern_counts[pattern_str] += 1
                    
                    if pattern_str not in pattern_examples:
                        pattern_examples[pattern_str] = []
                    pattern_examples[pattern_str].append(traces[i].id)
                    
                    if traces[i].success:
                        pattern_success[pattern_str] += 1
        
        # Convert to Pattern objects
        patterns = []
        for pattern_str, count in pattern_counts.items():
            sequence = pattern_str.split("->")
            
            # Calculate success rate
            success_count = pattern_success.get(pattern_str, 0)
            success_rate = success_count / count if count > 0 else 0
            
            # Generate description
            description = self._generate_pattern_description(sequence)
            
            patterns.append(Pattern(
                sequence=sequence,
                frequency=count,
                success_rate=success_rate,
                examples=list(set(pattern_examples[pattern_str]))[:5],
                description=description
            ))
        
        return patterns
    
    def _generate_pattern_description(self, sequence: List[str]) -> str:
        """
        Generate human-readable description for a pattern.
        
        Args:
            sequence: Tool call sequence
            
        Returns:
            Description string
        """
        if len(sequence) == 2:
            return f"Commonly uses {sequence[0]} followed by {sequence[1]}"
        elif len(sequence) == 3:
            return f"Workflow: {sequence[0]} → {sequence[1]} → {sequence[2]}"
        else:
            return f"Multi-step workflow starting with {sequence[0]}"
    
    def find_similar_patterns(
        self,
        pattern: Pattern,
        all_patterns: List[Pattern],
        threshold: float = 0.7
    ) -> List[Pattern]:
        """
        Find patterns similar to the given pattern.
        
        Args:
            pattern: Target pattern
            all_patterns: Patterns to search
            threshold: Similarity threshold
            
        Returns:
            List of similar patterns
        """
        similar = []
        
        for other in all_patterns:
            if other.pattern_string == pattern.pattern_string:
                continue
            
            similarity = self._compute_pattern_similarity(pattern, other)
            if similarity >= threshold:
                similar.append(other)
        
        return similar
    
    def _compute_pattern_similarity(self, p1: Pattern, p2: Pattern) -> float:
        """
        Compute similarity between two patterns.
        
        Uses sequence alignment score.
        """
        # Simple overlap-based similarity
        set1 = set(p1.sequence)
        set2 = set(p2.sequence)
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0
