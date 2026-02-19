import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from models.qa_models import SourceReference, AnnotatedContent

logger = logging.getLogger(__name__)


@dataclass
class AnnotatedSegment:
    text: str
    source_ids: List[str] = field(default_factory=list)


class ReferenceAnnotator:
    REFERENCE_PATTERN = re.compile(r'\[(\d+)\]')
    
    def __init__(
        self,
        min_match_length: int = 10,
        similarity_threshold: float = 0.6
    ):
        self.min_match_length = min_match_length
        self.similarity_threshold = similarity_threshold
    
    def annotate_response(
        self,
        response: str,
        sources: List[SourceReference]
    ) -> AnnotatedContent:
        logger.info(f"Annotating response with {len(sources)} sources")
        
        if not sources:
            return AnnotatedContent(
                text=response,
                source_ids=[]
            )
        
        existing_refs = self._extract_existing_references(response)
        
        if existing_refs:
            valid_refs = [ref for ref in existing_refs if int(ref) <= len(sources)]
            return AnnotatedContent(
                text=response,
                source_ids=valid_refs
            )
        
        annotated_text = response
        used_sources: List[str] = []
        
        for i, source in enumerate(sources, 1):
            source_id = f"[{i}]"
            content = source.content
            
            key_phrases = self._extract_key_phrases(content)
            
            for phrase in key_phrases:
                if len(phrase) >= self.min_match_length and phrase in annotated_text:
                    annotated_text = annotated_text.replace(
                        phrase,
                        f"{phrase}{source_id}",
                        1
                    )
                    if source_id not in used_sources:
                        used_sources.append(source_id)
                    break
        
        return AnnotatedContent(
            text=annotated_text,
            source_ids=used_sources
        )
    
    def extract_references(
        self,
        text: str
    ) -> List[Tuple[str, int, int]]:
        references = []
        for match in self.REFERENCE_PATTERN.finditer(text):
            ref_id = match.group(1)
            start = match.start()
            end = match.end()
            references.append((ref_id, start, end))
        return references
    
    def validate_references(
        self,
        text: str,
        sources: List[SourceReference]
    ) -> Tuple[bool, List[str]]:
        refs = self.extract_references(text)
        source_ids = set(range(1, len(sources) + 1))
        referenced_ids = set(int(ref[0]) for ref in refs)
        
        invalid_refs = []
        for ref_id in referenced_ids:
            if ref_id not in source_ids:
                invalid_refs.append(f"[{ref_id}]")
        
        is_valid = len(invalid_refs) == 0
        return is_valid, invalid_refs
    
    def format_source_list(
        self,
        sources: List[SourceReference],
        max_length: int = 200
    ) -> str:
        if not sources:
            return ""
        
        lines = ["\n\n---\n**参考来源：**\n"]
        
        for i, source in enumerate(sources, 1):
            content = source.content
            if len(content) > max_length:
                content = content[:max_length] + "..."
            
            doc_info = source.doc_id
            if source.metadata and source.metadata.get("title"):
                doc_info = source.metadata["title"]
            
            lines.append(f"[{i}] {doc_info}: {content}")
        
        return "\n".join(lines)
    
    def _extract_existing_references(self, text: str) -> List[str]:
        refs = self.REFERENCE_PATTERN.findall(text)
        return list(set(refs))
    
    def _extract_key_phrases(self, content: str) -> List[str]:
        phrases = []
        
        sentences = re.split(r'[。！？.!?]', content)
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) >= self.min_match_length:
                phrases.append(sentence)
        
        key_terms = re.findall(r'[\u4e00-\u9fa5]{2,8}(?:技术|系统|方法|功能|模块|服务|组件)', content)
        phrases.extend(key_terms)
        
        return list(set(phrases))
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        if not text1 or not text2:
            return 0.0
        
        words1 = set(text1)
        words2 = set(text2)
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        if union == 0:
            return 0.0
        
        return intersection / union


reference_annotator = ReferenceAnnotator()
