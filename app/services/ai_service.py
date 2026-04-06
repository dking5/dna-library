from google import genai
from google.genai import types
from fastapi import HTTPException
import logging
#from app.core.config import settings

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self, api_key: str, model_id: str):
        self.client = genai.Client(api_key=api_key)
        self.model_id = model_id

    async def summarize_gene_function(self, target_gene, similar_genes):
        """
        Generates a functional analysis report using RAG.
        :param target_gene: The Gene model instance to analyze.
        :param similar_genes: A list of similar genes retrieved via pgvector.
        """
        
        # 1. Prepare the context from your specific metadata
        context_entries = []
        for g in similar_genes:
            entry = (
                f"- Label: {g.label}\n"
                f"  Description: {g.description}\n"
                f"  GC Content: {g.gc_content}%\n"
            )
            context_entries.append(entry)
        
        context_text = "\n".join(context_entries)

        # 2. Craft a biologically-aware prompt
        prompt = f"""
        You are a Senior Computational Biologist. Analyze the following DNA sequence data:
        
        TARGET SEQUENCE INFO:
        - Label: {target_gene.label}
        - GC Content: {target_gene.gc_content}%
        - Sequence Snippet: {target_gene.sequence[:200]}...
        
        REFERENCE CONTEXT (Similar sequences found in library):
        {context_text}
        
        TASK:
        Based on the reference context, provide:
        1. Predicted biological function or gene family.
        2. Analysis of the GC content relevance.
        3. Potential research applications or risks.
        
        Format the output in professional Markdown.
        """

        try:
            response = await self.client.aio.models.generate_content(
                model = self.model_id,
                contents = prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1, # Lower temperature for factual bio-data
                )
            )            
            return response.text

        except Exception as e:
            logger.error(f"Gemini SDK Error: {str(e)}")
            logger.error(f"DETAILED GEMINI ERROR: {type(e).__name__}: {str(e)}")
            raise HTTPException(
                status_code=502, 
                detail="AI service temporarily unavailable."
            )