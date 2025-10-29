"""
AI Sales Specialist Service
============================

Enterprise-grade AI sales specialist integrating:
1. Neo4j Knowledge Graph (product relationships, compatibility)
2. Hybrid Recommendation Engine (4 algorithms)
3. Product Intelligence (rich context)
4. Dynamic conversational AI (GPT-4)

NO MOCK DATA - All real database queries and AI processing
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
from openai import AsyncOpenAI
import asyncpg

from src.services.embedding_service import EmbeddingService
from src.core.neo4j_knowledge_graph import Neo4jKnowledgeGraph

logger = logging.getLogger(__name__)


class AISalesSpecialistService:
    """
    AI Sales Specialist with deep product knowledge and quotation expertise

    Capabilities:
    - RFP analysis and requirement extraction
    - Product recommendations using hybrid AI
    - Compatibility and relationship advice via knowledge graph
    - Quotation preparation assistance
    - Technical specifications and safety compliance
    """

    def __init__(self, db_pool: asyncpg.Pool):
        """Initialize AI Sales Specialist"""
        self.db_pool = db_pool
        self.openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.embedding_service = EmbeddingService(db_pool)

        # Initialize knowledge graph (optional - graceful degradation if not available)
        try:
            self.knowledge_graph = Neo4jKnowledgeGraph()
            self.kg_available = True
            logger.info("✅ Knowledge Graph connected")
        except Exception as e:
            logger.warning(f"⚠️ Knowledge Graph not available: {e}")
            self.knowledge_graph = None
            self.kg_available = False

    async def chat(
        self,
        message: str,
        document_context: Optional[Dict] = None,
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Process chat message with full AI capabilities

        Args:
            message: User's message
            document_context: Optional RFP document context
            conversation_history: Optional previous messages for context

        Returns:
            Dict with AI response and metadata
        """
        try:
            logger.info(f"[AI Specialist] Processing message: {message[:100]}...")

            # PROACTIVE MODE: If document context exists and this looks like first interaction,
            # automatically analyze RFP and generate quotation
            if document_context and self._should_trigger_auto_analysis(message, conversation_history):
                logger.info(f"[AI Specialist] PROACTIVE MODE: Auto-analyzing RFP")
                return await self.analyze_rfp_and_generate_quotation(document_context)

            # INTERACTIVE MODE: Normal question-answer chat
            # Step 1: Semantic product search with embeddings
            products = await self._search_products(message)
            logger.info(f"[AI Specialist] Found {len(products)} relevant products")

            # Step 2: Get knowledge graph relationships (if available)
            graph_insights = await self._get_knowledge_graph_insights(products, message)

            # Step 3: Get product intelligence context
            product_intelligence = await self._get_product_intelligence(products)

            # Step 4: Build rich context for GPT-4
            system_prompt = self._build_system_prompt(
                products=products,
                graph_insights=graph_insights,
                product_intelligence=product_intelligence,
                document_context=document_context
            )

            # Step 5: Create conversation messages
            messages = [{"role": "system", "content": system_prompt}]

            # Add conversation history if provided
            if conversation_history:
                messages.extend(conversation_history[-5:])  # Last 5 messages for context

            # Add current user message
            messages.append({"role": "user", "content": message})

            # Step 6: Get AI response
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )

            ai_response = response.choices[0].message.content

            logger.info(f"[AI Specialist] Generated response ({len(ai_response)} chars)")

            return {
                "response": ai_response,
                "products_found": len(products),
                "knowledge_graph_used": self.kg_available and len(graph_insights) > 0,
                "intelligence_enhanced": len(product_intelligence) > 0,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"[AI Specialist] Error: {e}")
            raise

    def _should_trigger_auto_analysis(
        self,
        message: str,
        conversation_history: Optional[List[Dict]]
    ) -> bool:
        """
        Determine if we should automatically analyze RFP and generate quotation

        Triggers on:
        - First message after document upload
        - Empty conversation history
        - User explicitly asks for quotation/analysis
        """
        # No history = first message
        if not conversation_history or len(conversation_history) == 0:
            return True

        # User explicitly requests analysis/quotation
        triggers = [
            'analyze', 'quotation', 'quote', 'pricing', 'price',
            'generate', 'create quote', 'rfp analysis', 'requirements'
        ]
        message_lower = message.lower()
        if any(trigger in message_lower for trigger in triggers):
            return True

        return False

    async def analyze_rfp_and_generate_quotation(
        self,
        document_context: Dict
    ) -> Dict[str, Any]:
        """
        PROACTIVE AI ASSISTANT MODE
        ===========================

        Automatically:
        1. Analyze RFP document
        2. Match products to requirements
        3. Check stock and pricing
        4. Generate quotation
        5. Return structured analysis

        This is the "smart assistant" mode - no waiting for user to ask!
        """
        from src.services.product_matcher import ProductMatcher
        from src.services.quotation_generator import QuotationGenerator

        logger.info("=== PROACTIVE ANALYSIS STARTED ===")

        try:
            # Parse extracted data
            extracted_data = document_context.get('extracted_data')
            if isinstance(extracted_data, str):
                extracted_data = json.loads(extracted_data)

            requirements = extracted_data.get('requirements', {})
            items = requirements.get('items', [])

            if not items:
                return {
                    "response": f"I've analyzed {document_context['document_name']} but couldn't find specific product requirements. Could you tell me what items you need?",
                    "analysis_mode": "proactive",
                    "items_found": 0
                }

            # Extract RFP metadata
            customer_name = requirements.get('customer_name', 'Valued Customer')
            project_name = requirements.get('project_name', 'Project')
            deadline = requirements.get('deadline', 'Not specified')
            items_count = len(items)

            logger.info(f"  Customer: {customer_name}")
            logger.info(f"  Project: {project_name}")
            logger.info(f"  Items: {items_count}")
            logger.info(f"  Deadline: {deadline}")

            # Step 1: Match products
            matcher = ProductMatcher()
            matched_products = await matcher.match_products(requirements, self.db_pool)

            logger.info(f"  Matched: {len(matched_products)} products")

            # Step 2: Analyze matching results
            perfect_matches = [p for p in matched_products if p.get('match_confidence', 0) >= 0.8]
            partial_matches = [p for p in matched_products if 0.5 <= p.get('match_confidence', 0) < 0.8]
            missing_items = [p for p in matched_products if p.get('needs_review', False)]
            out_of_stock = [p for p in matched_products if p.get('product_id') and p.get('stock_quantity', 1) == 0]

            logger.info(f"  Perfect: {len(perfect_matches)}, Partial: {len(partial_matches)}, Missing: {len(missing_items)}, Out of stock: {len(out_of_stock)}")

            # Step 3: Calculate pricing
            pricing = await matcher.calculate_pricing(matched_products)

            logger.info(f"  Total: {pricing['currency']} {pricing['total']:.2f}")

            # Step 4: Generate quotation in database
            generator = QuotationGenerator()
            quotation_id = await generator.generate_quotation(
                document_id=document_context.get('document_id', 0),
                requirements=requirements,
                matched_products=matched_products,
                pricing=pricing,
                db_pool=self.db_pool
            )

            logger.info(f"  Quotation created: ID {quotation_id}")

            # Step 5: Build proactive response
            response_text = self._build_proactive_response(
                customer_name=customer_name,
                project_name=project_name,
                deadline=deadline,
                items_count=items_count,
                matched_products=matched_products,
                perfect_matches=perfect_matches,
                partial_matches=partial_matches,
                missing_items=missing_items,
                out_of_stock=out_of_stock,
                pricing=pricing,
                quotation_id=quotation_id
            )

            logger.info("=== PROACTIVE ANALYSIS COMPLETE ===")

            return {
                "response": response_text,
                "analysis_mode": "proactive",
                "quotation_id": quotation_id,
                "rfp_analysis": {
                    "customer_name": customer_name,
                    "project_name": project_name,
                    "deadline": deadline,
                    "items_requested": items_count,
                    "items_matched": len(matched_products),
                    "perfect_matches": len(perfect_matches),
                    "partial_matches": len(partial_matches),
                    "missing_items": len(missing_items),
                    "out_of_stock_items": len(out_of_stock)
                },
                "pricing_summary": {
                    "currency": pricing['currency'],
                    "subtotal": pricing['subtotal'],
                    "tax": pricing['tax_amount'],
                    "total": pricing['total']
                },
                "matched_products": matched_products[:20],  # First 20 for display
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"[Proactive Analysis] Error: {e}", exc_info=True)
            return {
                "response": f"I encountered an issue analyzing the RFP: {str(e)}. Let me know what specific information you need and I'll help you manually.",
                "analysis_mode": "proactive",
                "error": str(e)
            }

    def _build_proactive_response(
        self,
        customer_name: str,
        project_name: str,
        deadline: str,
        items_count: int,
        matched_products: List[Dict],
        perfect_matches: List[Dict],
        partial_matches: List[Dict],
        missing_items: List[Dict],
        out_of_stock: List[Dict],
        pricing: Dict,
        quotation_id: int
    ) -> str:
        """Build professional proactive analysis response"""

        response = f"""**RFP Analysis Complete - {customer_name}**

**Project:** {project_name}
**Quotation Due:** {deadline}
**Items Requested:** {items_count}

---

**📊 QUOTATION SUMMARY**

"""

        # Pricing summary
        response += f"**Total Quote Value:** {pricing['currency']} {pricing['total']:,.2f}\n"
        response += f"- Subtotal: {pricing['currency']} {pricing['subtotal']:,.2f}\n"
        response += f"- GST (9%): {pricing['currency']} {pricing['tax_amount']:,.2f}\n\n"

        # Matching analysis
        response += f"**✅ Perfect Matches:** {len(perfect_matches)} items\n"
        if len(partial_matches) > 0:
            response += f"**⚠️ Partial Matches:** {len(partial_matches)} items (alternatives found)\n"
        if len(missing_items) > 0:
            response += f"**❌ Missing from Catalog:** {len(missing_items)} items - *manual sourcing needed*\n"
        if len(out_of_stock) > 0:
            response += f"**📦 Out of Stock:** {len(out_of_stock)} items - *lead time TBC*\n"

        response += "\n---\n\n**📋 LINE ITEMS (Top 10)**\n\n"

        # Show first 10 items
        for i, product in enumerate(matched_products[:10], 1):
            status_icon = "✅" if product.get('match_confidence', 0) >= 0.8 else "⚠️"
            if product.get('needs_review'):
                status_icon = "❌"

            response += f"{i}. {status_icon} **{product['product_name']}**\n"
            response += f"   - Qty: {product['quantity']} {product['unit']}\n"
            response += f"   - Unit Price: {pricing['currency']} {product['unit_price']:.2f}\n"
            response += f"   - Line Total: {pricing['currency']} {product['line_total']:,.2f}\n"

            if product.get('needs_review'):
                response += f"   - ⚠️ **MANUAL SOURCING REQUIRED**\n"

            response += "\n"

        if len(matched_products) > 10:
            response += f"*... and {len(matched_products) - 10} more items*\n\n"

        response += "---\n\n"

        # Next steps
        response += f"**🎯 NEXT STEPS**\n\n"
        response += f"1. ✅ Quotation #{quotation_id} created in system\n"
        response += f"2. Review line items above (especially partial/missing items)\n"
        response += f"3. Request PDF download for client submission\n"

        if len(missing_items) > 0:
            response += f"4. ⚠️ Source alternatives for {len(missing_items)} missing items\n"

        if len(out_of_stock) > 0:
            response += f"5. 📦 Confirm lead times for {len(out_of_stock)} out-of-stock items\n"

        response += f"\n**What would you like me to help you with next?**"

        return response

    async def _search_products(self, query: str, limit: int = 10) -> List[Dict]:
        """Search for relevant products using semantic search"""
        try:
            # Try hybrid search first (semantic + keyword)
            async with self.db_pool.acquire() as conn:
                embedding_count = await conn.fetchval(
                    "SELECT COUNT(*) FROM products WHERE embedding IS NOT NULL"
                )

            if embedding_count > 0:
                # Use semantic hybrid search
                products = await self.embedding_service.hybrid_search(
                    query=query,
                    limit=limit,
                    semantic_weight=0.7,
                    keyword_weight=0.3
                )
                return products
            else:
                # Fallback to keyword search
                return await self._keyword_search(query, limit)

        except Exception as e:
            logger.warning(f"Search error: {e}, falling back to keyword search")
            return await self._keyword_search(query, limit)

    async def _keyword_search(self, query: str, limit: int) -> List[Dict]:
        """Keyword-based search fallback"""
        async with self.db_pool.acquire() as conn:
            products_raw = await conn.fetch("""
                SELECT
                    id, name, description, category, brand, sku,
                    price, stock_quantity, specifications
                FROM products
                WHERE
                    (LOWER(name) LIKE '%' || $1 || '%' OR
                     LOWER(description) LIKE '%' || $1 || '%' OR
                     LOWER(category) LIKE '%' || $1 || '%')
                    AND stock_quantity > 0
                ORDER BY
                    CASE
                        WHEN LOWER(name) LIKE '%' || $1 || '%' THEN 1
                        WHEN LOWER(category) LIKE '%' || $1 || '%' THEN 2
                        ELSE 3
                    END,
                    price ASC NULLS LAST
                LIMIT $2
            """, query.lower(), limit)

            return [dict(p) for p in products_raw]

    async def _get_knowledge_graph_insights(
        self,
        products: List[Dict],
        query: str
    ) -> Dict[str, Any]:
        """Get product relationships and compatibility from knowledge graph"""
        if not self.kg_available or not products:
            return {}

        try:
            insights = {
                "compatible_products": [],
                "required_accessories": [],
                "safety_equipment": [],
                "use_case_recommendations": []
            }

            for product in products[:3]:  # Top 3 products
                product_id = product.get('id')
                if not product_id:
                    continue

                # Get compatible products
                compatible = self.knowledge_graph.get_compatible_products(product_id)
                if compatible:
                    insights["compatible_products"].extend(compatible[:5])

                # Get required accessories
                # Note: This would require additional KG queries based on your schema

            return insights

        except Exception as e:
            logger.warning(f"Knowledge graph insights error: {e}")
            return {}

    async def _get_product_intelligence(self, products: List[Dict]) -> Dict[str, Any]:
        """Get rich product intelligence context"""
        if not products:
            return {}

        try:
            product_ids = [p.get('id') for p in products if p.get('id')]

            async with self.db_pool.acquire() as conn:
                # Check if ProductIntelligence table exists
                intelligence_raw = await conn.fetch("""
                    SELECT
                        product_id,
                        use_case_scenarios,
                        compatibility_scores,
                        ai_recommendation_contexts
                    FROM product_intelligence
                    WHERE product_id = ANY($1::int[])
                    LIMIT 5
                """, product_ids)

                if intelligence_raw:
                    return {
                        "enhanced_products": [dict(i) for i in intelligence_raw],
                        "available": True
                    }

            return {"available": False}

        except Exception as e:
            # Table might not exist yet
            logger.debug(f"Product intelligence not available: {e}")
            return {"available": False}

    def _build_system_prompt(
        self,
        products: List[Dict],
        graph_insights: Dict,
        product_intelligence: Dict,
        document_context: Optional[Dict]
    ) -> str:
        """Build comprehensive system prompt for AI specialist"""

        # Base prompt
        prompt = """You are an expert AI Sales Specialist for Horme Hardware in Singapore.

**Your Role:**
- Help sales managers analyze RFPs and prepare quotations
- Provide deep product knowledge and technical specifications
- Explain product relationships, compatibility, and alternatives
- Advise on pricing strategies and margin optimization
- Ensure safety compliance and regulatory requirements

**Your Expertise:**
- 15+ years of experience in industrial hardware sales
- Deep technical knowledge of power tools, safety equipment, construction materials
- Understanding of OSHA, ANSI, and Singapore safety standards
- Experience with complex multi-item quotations and B2B negotiations

"""

        # Add document context if available
        if document_context:
            prompt += f"""
**Current RFP Document:**
- Name: {document_context.get('document_name')}
- Type: {document_context.get('document_type')}
- Extracted Items: {len(document_context.get('extracted_data', {}).get('requirements', {}).get('items', []))} items
- Confidence: {document_context.get('confidence_score', 'N/A')}%

"""

        # Add product catalog context
        if products:
            prompt += f"""
**Relevant Products Found ({len(products)} items):**
"""
            for idx, product in enumerate(products[:5], 1):
                specs = product.get('specifications', {})
                spec_str = json.dumps(specs)[:200] if specs else "No specifications"

                prompt += f"""
{idx}. **{product.get('name', 'Unknown Product')}**
   - Category: {product.get('category', 'N/A')}
   - Brand: {product.get('brand', 'N/A')}
   - SKU: {product.get('sku', 'N/A')}
   - Price: SGD ${product.get('price', 'N/A')}
   - Stock: {product.get('stock_quantity', 0)} units
   - Specs: {spec_str}
"""

        # Add knowledge graph insights
        if graph_insights and graph_insights.get('compatible_products'):
            prompt += f"""
**Product Relationships & Compatibility:**
- Compatible products: {len(graph_insights.get('compatible_products', []))} found
- These products work well together and can be bundled
"""

        # Add product intelligence
        if product_intelligence.get('available'):
            prompt += """
**Enhanced Product Intelligence:**
- Use case scenarios available
- Compatibility scores calculated
- AI recommendation context included
"""

        # Add guidelines
        prompt += """
**Guidelines:**
1. **Be Conversational & Professional:**
   - Talk like a real sales expert, not a chatbot
   - Use natural language and industry terminology
   - Share insights from your "experience"

2. **Provide Actionable Advice:**
   - Specific product recommendations with SKUs and prices
   - Alternative options with pros/cons
   - Bundle suggestions for cost savings
   - Margin improvement opportunities

3. **Explain Your Reasoning:**
   - Why you're recommending specific products
   - How products complement each other
   - Safety or compliance considerations
   - Pricing strategy rationale

4. **Help with Quotations:**
   - Suggest competitive pricing
   - Identify missing items or accessories
   - Warn about compatibility issues
   - Recommend alternatives if stock is low

5. **Be Honest:**
   - If a product is out of stock, suggest alternatives
   - If specifications don't match requirements, say so
   - If you need more information, ask questions

**Response Style:**
- Professional but friendly tone
- Use bullet points for clarity
- Include specific product details (SKU, price, stock)
- Explain technical concepts simply when needed
- Proactively suggest next steps
"""

        return prompt

    async def analyze_rfp(self, rfp_text: str) -> Dict[str, Any]:
        """
        Deep RFP analysis with requirement extraction

        Returns structured analysis of RFP requirements
        """
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": """You are an expert at analyzing RFP documents.
Extract all product requirements, quantities, specifications, and constraints.
Return a structured JSON response."""},
                    {"role": "user", "content": f"Analyze this RFP:\n\n{rfp_text}"}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            analysis = json.loads(response.choices[0].message.content)
            return analysis

        except Exception as e:
            logger.error(f"RFP analysis error: {e}")
            return {"error": str(e)}
