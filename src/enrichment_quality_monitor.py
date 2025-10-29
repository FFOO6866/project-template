#!/usr/bin/env python3
"""
Horme Product Enrichment Quality Monitor
=======================================

Advanced quality control and monitoring system for the enrichment pipeline:
- Real-time quality metrics tracking
- Data validation and integrity checks
- Performance monitoring and alerts
- Automated fallback mechanisms
- Quality scoring and recommendations
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import statistics
import pandas as pd
from pathlib import Path

from dataflow import DataFlow
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QualityLevel(Enum):
    """Quality assessment levels"""
    EXCELLENT = "excellent"  # 90%+ data completeness
    GOOD = "good"           # 70-89% data completeness  
    FAIR = "fair"           # 50-69% data completeness
    POOR = "poor"           # 30-49% data completeness
    CRITICAL = "critical"   # <30% data completeness

class DataType(Enum):
    """Types of product data"""
    PRICING = "pricing"
    AVAILABILITY = "availability"
    SPECIFICATIONS = "specifications"
    IMAGES = "images"
    DESCRIPTIONS = "descriptions"
    CATEGORIES = "categories"

@dataclass
class QualityMetrics:
    """Comprehensive quality metrics for enrichment process"""
    # Overall metrics
    total_products: int = 0
    processed_products: int = 0
    completion_rate: float = 0.0
    
    # Data quality metrics
    pricing_completeness: float = 0.0
    availability_completeness: float = 0.0
    specifications_completeness: float = 0.0
    images_completeness: float = 0.0
    
    # Quality scores (0-100)
    overall_quality_score: float = 0.0
    pricing_quality_score: float = 0.0
    availability_quality_score: float = 0.0
    specifications_quality_score: float = 0.0
    images_quality_score: float = 0.0
    
    # Performance metrics
    processing_rate: float = 0.0  # products per minute
    error_rate: float = 0.0
    retry_rate: float = 0.0
    
    # Data freshness
    last_update: Optional[str] = None
    average_data_age: float = 0.0  # hours
    
    # Category breakdown
    category_quality: Dict[str, float] = None
    brand_quality: Dict[str, float] = None
    
    # Recommendations
    quality_level: QualityLevel = QualityLevel.POOR
    recommendations: List[str] = None

@dataclass
class QualityAlert:
    """Quality alert for monitoring system"""
    alert_id: str
    severity: str  # critical, warning, info
    data_type: DataType
    message: str
    timestamp: str
    affected_products: int
    recommended_action: str

class ProductQualityAnalyzer:
    """Analyze quality of individual product data"""
    
    def __init__(self):
        self.price_patterns = [
            r'S\$\d+\.?\d*',
            r'\$\d+\.?\d*',
            r'SGD\s*\d+\.?\d*',
            r'\d+\.?\d*\s*SGD'
        ]
        
        self.availability_keywords = [
            'in stock', 'available', 'out of stock', 'discontinued',
            'pre-order', 'backorder', 'limited stock', 'sold out'
        ]
        
    def analyze_product_quality(self, product_data: Dict[str, Any]) -> Dict[str, float]:
        """Analyze quality of a single product's data"""
        scores = {}
        
        # Pricing quality (0-100)
        scores['pricing'] = self._score_pricing_quality(product_data.get('price'))
        
        # Availability quality (0-100)
        scores['availability'] = self._score_availability_quality(product_data.get('availability'))
        
        # Specifications quality (0-100)
        scores['specifications'] = self._score_specifications_quality(product_data.get('specifications'))
        
        # Images quality (0-100)
        scores['images'] = self._score_images_quality(product_data.get('images'))
        
        # Description quality (0-100)
        scores['description'] = self._score_description_quality(product_data.get('description'))
        
        # Overall score (weighted average)
        weights = {
            'pricing': 0.3,
            'availability': 0.25,
            'specifications': 0.2,
            'images': 0.15,
            'description': 0.1
        }
        
        scores['overall'] = sum(scores[key] * weights[key] for key in weights.keys())
        
        return scores
    
    def _score_pricing_quality(self, price: Optional[str]) -> float:
        """Score pricing data quality (0-100)"""
        if not price:
            return 0.0
        
        score = 40.0  # Base score for having any price
        
        # Check if price follows expected format
        import re
        if any(re.search(pattern, price, re.IGNORECASE) for pattern in self.price_patterns):
            score += 30.0
        
        # Check if price is reasonable (not 0 or extremely high)
        try:
            # Extract numeric value
            numeric_price = re.findall(r'\d+\.?\d*', price)
            if numeric_price:
                price_value = float(numeric_price[0])
                if 0.01 <= price_value <= 10000:  # Reasonable range
                    score += 20.0
                if not price.lower().endswith('(estimated)'):
                    score += 10.0  # Real data vs estimated
        except:
            pass
        
        return min(score, 100.0)
    
    def _score_availability_quality(self, availability: Optional[str]) -> float:
        """Score availability data quality (0-100)"""
        if not availability:
            return 0.0
        
        score = 50.0  # Base score for having availability info
        
        # Check if availability matches expected keywords
        if any(keyword in availability.lower() for keyword in self.availability_keywords):
            score += 30.0
        
        # Bonus for specific stock information
        if any(term in availability.lower() for term in ['in stock', 'available']):
            score += 10.0
        
        # Penalty for estimated data
        if 'estimated' in availability.lower():
            score -= 20.0
        
        return min(score, 100.0)
    
    def _score_specifications_quality(self, specifications: Optional[Dict]) -> float:
        """Score specifications data quality (0-100)"""
        if not specifications:
            return 0.0
        
        if not isinstance(specifications, dict):
            return 20.0  # Some data but not structured
        
        score = 30.0  # Base score for having specs
        
        # Score based on number of specifications
        spec_count = len(specifications)
        if spec_count >= 5:
            score += 40.0
        elif spec_count >= 3:
            score += 25.0
        elif spec_count >= 1:
            score += 15.0
        
        # Bonus for common important specs
        important_specs = ['weight', 'dimensions', 'power', 'voltage', 'capacity', 'material']
        matching_specs = sum(1 for key in specifications.keys() 
                            if any(imp in key.lower() for imp in important_specs))
        score += min(matching_specs * 5, 30.0)
        
        return min(score, 100.0)
    
    def _score_images_quality(self, images: Optional[List[str]]) -> float:
        """Score images data quality (0-100)"""
        if not images:
            return 0.0
        
        if not isinstance(images, list):
            return 20.0  # Some image data but not structured
        
        score = 40.0  # Base score for having images
        
        # Score based on number of images
        image_count = len(images)
        if image_count >= 5:
            score += 30.0
        elif image_count >= 3:
            score += 20.0
        elif image_count >= 1:
            score += 10.0
        
        # Check for valid image URLs
        valid_urls = sum(1 for img in images if self._is_valid_image_url(img))
        if valid_urls > 0:
            score += min(valid_urls * 5, 30.0)
        
        return min(score, 100.0)
    
    def _score_description_quality(self, description: Optional[str]) -> float:
        """Score description data quality (0-100)"""
        if not description:
            return 0.0
        
        score = 50.0  # Base score for having description
        
        # Length-based scoring
        desc_length = len(description)
        if desc_length >= 100:
            score += 30.0
        elif desc_length >= 50:
            score += 20.0
        elif desc_length >= 20:
            score += 10.0
        
        # Check for informative content (not just product code)
        informative_words = ['with', 'for', 'features', 'includes', 'suitable', 'professional']
        if any(word in description.lower() for word in informative_words):
            score += 20.0
        
        return min(score, 100.0)
    
    def _is_valid_image_url(self, url: str) -> bool:
        """Check if URL appears to be a valid image URL"""
        if not url or not isinstance(url, str):
            return False
        
        url_lower = url.lower()
        return (url_lower.startswith(('http://', 'https://')) and 
                any(ext in url_lower for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']))

class EnrichmentQualityMonitor:
    """Main quality monitoring system"""
    
    def __init__(self):
        self.db = DataFlow()
        self.analyzer = ProductQualityAnalyzer()
        self.alerts = []
        self._setup_dataflow_models()
    
    def _setup_dataflow_models(self):
        """Setup DataFlow models for quality monitoring"""
        
        @self.db.model
        class QualityMetricsLog:
            timestamp: str
            total_products: int
            processed_products: int
            completion_rate: float
            pricing_completeness: float
            availability_completeness: float
            specifications_completeness: float
            images_completeness: float
            overall_quality_score: float
            pricing_quality_score: float
            availability_quality_score: float
            specifications_quality_score: float
            images_quality_score: float
            processing_rate: float
            error_rate: float
            quality_level: str
            
        @self.db.model
        class QualityAlertLog:
            alert_id: str
            severity: str
            data_type: str
            message: str
            timestamp: str
            affected_products: int
            recommended_action: str
            resolved: bool = False
            
        @self.db.model
        class ProductQualityScore:
            sku: str
            overall_score: float
            pricing_score: float
            availability_score: float
            specifications_score: float
            images_score: float
            description_score: float
            last_updated: str
    
    async def monitor_enrichment_quality(self) -> QualityMetrics:
        """Main monitoring function - analyze current enrichment quality"""
        logger.info("Starting enrichment quality monitoring...")
        
        try:
            await self.db.initialize()
            
            # Get current product data
            products = await self._get_all_enriched_products()
            
            if not products:
                logger.warning("No enriched products found for quality analysis")
                return QualityMetrics()
            
            # Calculate comprehensive metrics
            metrics = await self._calculate_quality_metrics(products)
            
            # Generate quality alerts
            alerts = await self._generate_quality_alerts(products, metrics)
            
            # Log metrics to database
            await self._log_quality_metrics(metrics)
            
            # Log alerts to database
            if alerts:
                await self._log_quality_alerts(alerts)
            
            # Generate quality report
            await self._generate_quality_report(metrics, alerts)
            
            logger.info(f"Quality monitoring completed. Overall score: {metrics.overall_quality_score:.1f}")
            
            return metrics
            
        except Exception as e:
            logger.error(f"Quality monitoring failed: {e}")
            raise
    
    async def _get_all_enriched_products(self) -> List[Dict[str, Any]]:
        """Get all enriched products from database"""
        try:
            workflow = WorkflowBuilder()
            workflow.add_node("EnrichedProductListNode", "get_all", {
                "limit": 50000  # Get all products
            })
            
            runtime = LocalRuntime()
            results, run_id = runtime.execute(workflow.build())
            
            if results and 'get_all' in results:
                return results['get_all'].get('data', [])
            
            return []
            
        except Exception as e:
            logger.error(f"Failed to get enriched products: {e}")
            return []
    
    async def _calculate_quality_metrics(self, products: List[Dict[str, Any]]) -> QualityMetrics:
        """Calculate comprehensive quality metrics"""
        
        if not products:
            return QualityMetrics()
        
        total_products = len(products)
        
        # Count data completeness
        pricing_count = sum(1 for p in products if p.get('price'))
        availability_count = sum(1 for p in products if p.get('availability'))
        specifications_count = sum(1 for p in products if p.get('specifications'))
        images_count = sum(1 for p in products if p.get('images'))
        
        # Calculate completeness percentages
        pricing_completeness = (pricing_count / total_products) * 100
        availability_completeness = (availability_count / total_products) * 100
        specifications_completeness = (specifications_count / total_products) * 100
        images_completeness = (images_count / total_products) * 100
        
        # Calculate quality scores
        quality_scores = []
        pricing_scores = []
        availability_scores = []
        specifications_scores = []
        images_scores = []
        
        for product in products:
            scores = self.analyzer.analyze_product_quality(product)
            quality_scores.append(scores['overall'])
            pricing_scores.append(scores['pricing'])
            availability_scores.append(scores['availability'])
            specifications_scores.append(scores['specifications'])
            images_scores.append(scores['images'])
        
        # Calculate averages
        overall_quality = statistics.mean(quality_scores) if quality_scores else 0
        pricing_quality = statistics.mean(pricing_scores) if pricing_scores else 0
        availability_quality = statistics.mean(availability_scores) if availability_scores else 0
        specifications_quality = statistics.mean(specifications_scores) if specifications_scores else 0
        images_quality = statistics.mean(images_scores) if images_scores else 0
        
        # Determine quality level
        quality_level = self._determine_quality_level(overall_quality)
        
        # Calculate category and brand quality breakdown
        category_quality = self._calculate_category_quality(products)
        brand_quality = self._calculate_brand_quality(products)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            pricing_completeness, availability_completeness, 
            specifications_completeness, images_completeness,
            overall_quality
        )
        
        return QualityMetrics(
            total_products=total_products,
            processed_products=total_products,
            completion_rate=100.0,
            pricing_completeness=pricing_completeness,
            availability_completeness=availability_completeness,
            specifications_completeness=specifications_completeness,
            images_completeness=images_completeness,
            overall_quality_score=overall_quality,
            pricing_quality_score=pricing_quality,
            availability_quality_score=availability_quality,
            specifications_quality_score=specifications_quality,
            images_quality_score=images_quality,
            last_update=datetime.now().isoformat(),
            category_quality=category_quality,
            brand_quality=brand_quality,
            quality_level=quality_level,
            recommendations=recommendations
        )
    
    def _determine_quality_level(self, overall_score: float) -> QualityLevel:
        """Determine overall quality level based on score"""
        if overall_score >= 90:
            return QualityLevel.EXCELLENT
        elif overall_score >= 70:
            return QualityLevel.GOOD
        elif overall_score >= 50:
            return QualityLevel.FAIR
        elif overall_score >= 30:
            return QualityLevel.POOR
        else:
            return QualityLevel.CRITICAL
    
    def _calculate_category_quality(self, products: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate quality scores by category"""
        category_scores = {}
        category_counts = {}
        
        for product in products:
            category = product.get('category', 'Unknown')
            scores = self.analyzer.analyze_product_quality(product)
            
            if category not in category_scores:
                category_scores[category] = 0
                category_counts[category] = 0
            
            category_scores[category] += scores['overall']
            category_counts[category] += 1
        
        # Calculate averages
        return {
            category: score / category_counts[category]
            for category, score in category_scores.items()
        }
    
    def _calculate_brand_quality(self, products: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate quality scores by brand"""
        brand_scores = {}
        brand_counts = {}
        
        for product in products:
            brand = product.get('brand', 'Unknown')
            scores = self.analyzer.analyze_product_quality(product)
            
            if brand not in brand_scores:
                brand_scores[brand] = 0
                brand_counts[brand] = 0
            
            brand_scores[brand] += scores['overall']
            brand_counts[brand] += 1
        
        # Calculate averages and return top 20 brands
        brand_averages = {
            brand: score / brand_counts[brand]
            for brand, score in brand_scores.items()
        }
        
        # Sort by score and return top 20
        sorted_brands = sorted(brand_averages.items(), key=lambda x: x[1], reverse=True)
        return dict(sorted_brands[:20])
    
    def _generate_recommendations(self, pricing_completeness: float, availability_completeness: float,
                                specifications_completeness: float, images_completeness: float,
                                overall_quality: float) -> List[str]:
        """Generate actionable recommendations based on quality metrics"""
        recommendations = []
        
        # Data completeness recommendations
        if pricing_completeness < 50:
            recommendations.append("CRITICAL: Pricing data missing for >50% of products. Focus on price extraction from product pages.")
        elif pricing_completeness < 75:
            recommendations.append("Improve pricing data coverage - currently only {:.1f}% complete".format(pricing_completeness))
        
        if availability_completeness < 60:
            recommendations.append("Availability data needs improvement - implement stock status checking")
        
        if specifications_completeness < 40:
            recommendations.append("Product specifications very limited - enhance technical data extraction")
        
        if images_completeness < 30:
            recommendations.append("Image coverage is low - improve product image extraction and validation")
        
        # Quality-based recommendations
        if overall_quality < 40:
            recommendations.append("URGENT: Overall data quality is poor. Review and enhance all scraping algorithms")
        elif overall_quality < 60:
            recommendations.append("Data quality needs improvement. Focus on validation and fallback mechanisms")
        
        # Strategic recommendations
        recommendations.extend([
            "Implement regular re-scraping schedule for products with missing data",
            "Set up automated alerts for quality drops below acceptable thresholds",
            "Consider implementing manual data entry for high-value products with missing information",
            "Monitor competitor pricing for products with estimated prices"
        ])
        
        return recommendations
    
    async def _generate_quality_alerts(self, products: List[Dict[str, Any]], 
                                     metrics: QualityMetrics) -> List[QualityAlert]:
        """Generate quality alerts based on current metrics"""
        alerts = []
        timestamp = datetime.now().isoformat()
        
        # Critical data quality alerts
        if metrics.pricing_completeness < 30:
            alerts.append(QualityAlert(
                alert_id=f"PRICING_CRITICAL_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                severity="critical",
                data_type=DataType.PRICING,
                message=f"Pricing data critically low: {metrics.pricing_completeness:.1f}% completeness",
                timestamp=timestamp,
                affected_products=int(len(products) * (100 - metrics.pricing_completeness) / 100),
                recommended_action="Immediately review pricing extraction algorithms and implement fallbacks"
            ))
        
        if metrics.overall_quality_score < 40:
            alerts.append(QualityAlert(
                alert_id=f"QUALITY_CRITICAL_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                severity="critical", 
                data_type=DataType.DESCRIPTIONS,
                message=f"Overall data quality critically low: {metrics.overall_quality_score:.1f}/100",
                timestamp=timestamp,
                affected_products=len(products),
                recommended_action="Review entire enrichment pipeline and enhance data validation"
            ))
        
        # Warning level alerts
        if metrics.availability_completeness < 50:
            alerts.append(QualityAlert(
                alert_id=f"AVAILABILITY_WARNING_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                severity="warning",
                data_type=DataType.AVAILABILITY,
                message=f"Availability data below target: {metrics.availability_completeness:.1f}% completeness",
                timestamp=timestamp,
                affected_products=int(len(products) * (100 - metrics.availability_completeness) / 100),
                recommended_action="Enhance stock status detection and implement inventory tracking"
            ))
        
        if metrics.images_completeness < 25:
            alerts.append(QualityAlert(
                alert_id=f"IMAGES_WARNING_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                severity="warning",
                data_type=DataType.IMAGES,
                message=f"Product images very limited: {metrics.images_completeness:.1f}% completeness",
                timestamp=timestamp,
                affected_products=int(len(products) * (100 - metrics.images_completeness) / 100),
                recommended_action="Improve image extraction and implement placeholder images for products without photos"
            ))
        
        return alerts
    
    async def _log_quality_metrics(self, metrics: QualityMetrics):
        """Log quality metrics to database"""
        try:
            workflow = WorkflowBuilder()
            workflow.add_node("QualityMetricsLogCreateNode", "log_metrics", {
                "timestamp": metrics.last_update,
                "total_products": metrics.total_products,
                "processed_products": metrics.processed_products,
                "completion_rate": metrics.completion_rate,
                "pricing_completeness": metrics.pricing_completeness,
                "availability_completeness": metrics.availability_completeness,
                "specifications_completeness": metrics.specifications_completeness,
                "images_completeness": metrics.images_completeness,
                "overall_quality_score": metrics.overall_quality_score,
                "pricing_quality_score": metrics.pricing_quality_score,
                "availability_quality_score": metrics.availability_quality_score,
                "specifications_quality_score": metrics.specifications_quality_score,
                "images_quality_score": metrics.images_quality_score,
                "processing_rate": metrics.processing_rate,
                "error_rate": metrics.error_rate,
                "quality_level": metrics.quality_level.value
            })
            
            runtime = LocalRuntime()
            results, run_id = runtime.execute(workflow.build())
            
        except Exception as e:
            logger.error(f"Failed to log quality metrics: {e}")
    
    async def _log_quality_alerts(self, alerts: List[QualityAlert]):
        """Log quality alerts to database"""
        try:
            if not alerts:
                return
            
            workflow = WorkflowBuilder()
            
            alerts_data = []
            for alert in alerts:
                alerts_data.append({
                    "alert_id": alert.alert_id,
                    "severity": alert.severity,
                    "data_type": alert.data_type.value,
                    "message": alert.message,
                    "timestamp": alert.timestamp,
                    "affected_products": alert.affected_products,
                    "recommended_action": alert.recommended_action,
                    "resolved": False
                })
            
            workflow.add_node("QualityAlertLogBulkCreateNode", "log_alerts", {
                "data": alerts_data
            })
            
            runtime = LocalRuntime()
            results, run_id = runtime.execute(workflow.build())
            
        except Exception as e:
            logger.error(f"Failed to log quality alerts: {e}")
    
    async def _generate_quality_report(self, metrics: QualityMetrics, alerts: List[QualityAlert]):
        """Generate comprehensive quality report"""
        try:
            report = {
                "report_info": {
                    "generated_at": datetime.now().isoformat(),
                    "report_type": "Product Enrichment Quality Analysis",
                    "total_products_analyzed": metrics.total_products
                },
                "executive_summary": {
                    "overall_quality_level": metrics.quality_level.value.upper(),
                    "overall_quality_score": f"{metrics.overall_quality_score:.1f}/100",
                    "data_completeness": f"{metrics.completion_rate:.1f}%",
                    "critical_alerts": len([a for a in alerts if a.severity == "critical"]),
                    "warning_alerts": len([a for a in alerts if a.severity == "warning"])
                },
                "data_completeness_analysis": {
                    "pricing_data": f"{metrics.pricing_completeness:.1f}%",
                    "availability_data": f"{metrics.availability_completeness:.1f}%",
                    "specifications_data": f"{metrics.specifications_completeness:.1f}%",
                    "images_data": f"{metrics.images_completeness:.1f}%"
                },
                "quality_scores": {
                    "overall_score": f"{metrics.overall_quality_score:.1f}/100",
                    "pricing_quality": f"{metrics.pricing_quality_score:.1f}/100",
                    "availability_quality": f"{metrics.availability_quality_score:.1f}/100",
                    "specifications_quality": f"{metrics.specifications_quality_score:.1f}/100",
                    "images_quality": f"{metrics.images_quality_score:.1f}/100"
                },
                "category_analysis": metrics.category_quality,
                "top_brands_quality": metrics.brand_quality,
                "active_alerts": [
                    {
                        "severity": alert.severity,
                        "data_type": alert.data_type.value,
                        "message": alert.message,
                        "affected_products": alert.affected_products,
                        "recommended_action": alert.recommended_action
                    }
                    for alert in alerts
                ],
                "recommendations": metrics.recommendations
            }
            
            # Save detailed report
            report_path = f"enrichment_quality_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            # Print executive summary
            print("\n" + "="*70)
            print("HORME PRODUCT ENRICHMENT - QUALITY ANALYSIS REPORT")
            print("="*70)
            print(f"Overall Quality Level: {report['executive_summary']['overall_quality_level']}")
            print(f"Overall Quality Score: {report['executive_summary']['overall_quality_score']}")
            print(f"Products Analyzed: {report['report_info']['total_products_analyzed']:,}")
            print()
            print("DATA COMPLETENESS:")
            for key, value in report['data_completeness_analysis'].items():
                print(f"  {key.replace('_', ' ').title()}: {value}")
            print()
            print("QUALITY SCORES:")
            for key, value in report['quality_scores'].items():
                print(f"  {key.replace('_', ' ').title()}: {value}")
            print()
            if alerts:
                print(f"ACTIVE ALERTS: {len(alerts)}")
                for alert in alerts[:5]:  # Show top 5 alerts
                    print(f"  [{alert.severity.upper()}] {alert.message}")
            print()
            print("TOP RECOMMENDATIONS:")
            for i, rec in enumerate(metrics.recommendations[:5], 1):
                print(f"  {i}. {rec}")
            print("="*70)
            print(f"Full report saved to: {report_path}")
            
        except Exception as e:
            logger.error(f"Failed to generate quality report: {e}")

async def main():
    """Main function to run quality monitoring"""
    monitor = EnrichmentQualityMonitor()
    
    try:
        metrics = await monitor.monitor_enrichment_quality()
        print(f"\nQuality monitoring completed successfully!")
        print(f"Overall quality score: {metrics.overall_quality_score:.1f}/100")
    except Exception as e:
        logger.error(f"Quality monitoring failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())