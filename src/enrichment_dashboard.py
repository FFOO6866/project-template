#!/usr/bin/env python3
"""
Horme Product Enrichment Dashboard
==================================

Real-time monitoring dashboard for the enrichment pipeline:
- Live progress tracking
- Quality metrics visualization
- Performance monitoring
- Alert management
- Interactive controls
"""

import asyncio
import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import threading
from pathlib import Path
import sys
import os

# Rich for beautiful console output
try:
    from rich.console import Console
    from rich.table import Table
    from rich.progress import Progress, TaskID, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
    from rich.live import Live
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.text import Text
    from rich.align import Align
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Rich library not available. Using basic console output.")

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__)))

try:
    from horme_product_enrichment_pipeline import ProductEnrichmentPipeline, EnrichmentMetrics
    from enrichment_quality_monitor import EnrichmentQualityMonitor, QualityMetrics
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure all pipeline files are in the correct location")
    sys.exit(1)

logging.basicConfig(level=logging.WARNING)  # Reduce log noise for dashboard
logger = logging.getLogger(__name__)

class EnrichmentDashboard:
    """Real-time dashboard for enrichment monitoring"""
    
    def __init__(self):
        self.console = Console() if RICH_AVAILABLE else None
        self.running = False
        self.pipeline = None
        self.quality_monitor = EnrichmentQualityMonitor()
        
        # Dashboard state
        self.current_metrics = EnrichmentMetrics()
        self.quality_metrics = QualityMetrics()
        self.pipeline_status = "Stopped"
        self.start_time = None
        self.last_update = None
        
        # Progress tracking
        self.progress_task = None
        self.processing_history = []
        self.quality_history = []
        
    def create_dashboard_layout(self) -> Layout:
        """Create the dashboard layout"""
        layout = Layout()
        
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3)
        )
        
        layout["main"].split_row(
            Layout(name="left"),
            Layout(name="right")
        )
        
        layout["left"].split_column(
            Layout(name="progress", size=8),
            Layout(name="quality", size=12)
        )
        
        layout["right"].split_column(
            Layout(name="metrics", size=10),
            Layout(name="alerts", size=10)
        )
        
        return layout
    
    def create_header_panel(self) -> Panel:
        """Create header panel with title and status"""
        status_color = "green" if self.pipeline_status == "Running" else "red"
        
        header_text = Text()
        header_text.append("HORME PRODUCT ENRICHMENT DASHBOARD", style="bold blue")
        header_text.append(f" | Status: ", style="white")
        header_text.append(f"{self.pipeline_status}", style=f"bold {status_color}")
        
        if self.start_time:
            elapsed = datetime.now() - self.start_time
            header_text.append(f" | Runtime: {str(elapsed).split('.')[0]}", style="white")
        
        return Panel(
            Align.center(header_text),
            style="bold blue"
        )
    
    def create_progress_panel(self) -> Panel:
        """Create progress tracking panel"""
        if not self.current_metrics.total_products:
            return Panel("No pipeline data available", title="Progress", border_style="dim")
        
        # Progress bar
        progress_pct = (self.current_metrics.processed_products / self.current_metrics.total_products) * 100
        
        progress_text = f"""
Products Processed: {self.current_metrics.processed_products:,} / {self.current_metrics.total_products:,}
Progress: {progress_pct:.1f}%
Success Rate: {(self.current_metrics.successful_enrichments / max(self.current_metrics.processed_products, 1)) * 100:.1f}%
Processing Rate: {self.current_metrics.processing_rate:.1f} products/min
"""
        
        if self.current_metrics.estimated_completion:
            try:
                est_completion = datetime.fromisoformat(self.current_metrics.estimated_completion)
                remaining = est_completion - datetime.now()
                progress_text += f"Estimated Completion: {remaining.total_seconds() / 3600:.1f} hours\n"
            except:
                pass
        
        return Panel(
            progress_text.strip(),
            title="Pipeline Progress",
            border_style="green" if progress_pct > 0 else "dim"
        )
    
    def create_quality_panel(self) -> Panel:
        """Create quality metrics panel"""
        if not hasattr(self.quality_metrics, 'overall_quality_score'):
            return Panel("Quality analysis not available", title="Quality Metrics", border_style="dim")
        
        # Quality level color coding
        quality_colors = {
            "excellent": "green",
            "good": "blue", 
            "fair": "yellow",
            "poor": "red",
            "critical": "bright_red"
        }
        
        quality_color = quality_colors.get(getattr(self.quality_metrics, 'quality_level', 'poor').value if hasattr(self.quality_metrics, 'quality_level') else 'poor', 'white')
        
        quality_text = f"""
Overall Quality: {getattr(self.quality_metrics, 'overall_quality_score', 0):.1f}/100
Data Completeness:
  • Pricing: {getattr(self.quality_metrics, 'pricing_completeness', 0):.1f}%
  • Availability: {getattr(self.quality_metrics, 'availability_completeness', 0):.1f}%
  • Specifications: {getattr(self.quality_metrics, 'specifications_completeness', 0):.1f}%
  • Images: {getattr(self.quality_metrics, 'images_completeness', 0):.1f}%
"""
        
        return Panel(
            quality_text.strip(),
            title="Quality Metrics",
            border_style=quality_color
        )
    
    def create_metrics_table(self) -> Table:
        """Create detailed metrics table"""
        table = Table(title="Detailed Metrics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")
        table.add_column("Target", style="green")
        table.add_column("Status", style="bold")
        
        metrics_data = [
            ("Total Products", f"{self.current_metrics.total_products:,}", "17,266", "✓" if self.current_metrics.total_products >= 17266 else "○"),
            ("Processed", f"{self.current_metrics.processed_products:,}", "17,266", "✓" if self.current_metrics.processed_products >= 17266 else "○"),
            ("Success Rate", f"{(self.current_metrics.successful_enrichments / max(self.current_metrics.processed_products, 1)) * 100:.1f}%", ">80%", "✓" if (self.current_metrics.successful_enrichments / max(self.current_metrics.processed_products, 1)) * 100 > 80 else "⚠"),
            ("Pricing Data", f"{getattr(self.quality_metrics, 'pricing_completeness', 0):.1f}%", ">60%", "✓" if getattr(self.quality_metrics, 'pricing_completeness', 0) > 60 else "⚠"),
            ("Processing Rate", f"{self.current_metrics.processing_rate:.1f}/min", ">50/min", "✓" if self.current_metrics.processing_rate > 50 else "⚠"),
        ]
        
        for metric, value, target, status in metrics_data:
            table.add_row(metric, value, target, status)
        
        return table
    
    def create_alerts_panel(self) -> Panel:
        """Create alerts panel"""
        # Simulated alerts - in real implementation, get from quality monitor
        alerts_text = "No active alerts"
        alert_style = "green"
        
        # Check for issues
        issues = []
        
        if getattr(self.quality_metrics, 'pricing_completeness', 0) < 50:
            issues.append("🔴 LOW: Pricing data <50%")
            alert_style = "red"
        
        if (self.current_metrics.successful_enrichments / max(self.current_metrics.processed_products, 1)) * 100 < 70:
            issues.append("🟡 WARN: Success rate <70%")
            if alert_style != "red":
                alert_style = "yellow"
        
        if self.current_metrics.processing_rate < 30:
            issues.append("🟡 WARN: Slow processing rate")
            if alert_style != "red":
                alert_style = "yellow"
        
        if issues:
            alerts_text = "\n".join(issues)
        else:
            alerts_text = "✅ All systems operational"
        
        return Panel(
            alerts_text,
            title="System Alerts",
            border_style=alert_style
        )
    
    def create_footer_panel(self) -> Panel:
        """Create footer with controls and info"""
        footer_text = "Controls: [q] Quit | [r] Refresh | [s] Start Pipeline | [p] Pause | [t] Test Sample"
        
        if self.last_update:
            footer_text += f" | Last Update: {self.last_update.strftime('%H:%M:%S')}"
        
        return Panel(
            Align.center(footer_text),
            style="dim"
        )
    
    def update_dashboard_data(self) -> Dict[str, Any]:
        """Update dashboard data (called periodically)"""
        # In a real implementation, this would:
        # 1. Query the database for current metrics
        # 2. Get pipeline status
        # 3. Run quality analysis
        # 4. Check for alerts
        
        self.last_update = datetime.now()
        
        # Simulate some progress for demo
        if self.pipeline_status == "Running":
            if self.current_metrics.processed_products < self.current_metrics.total_products:
                # Simulate processing
                increment = min(50, self.current_metrics.total_products - self.current_metrics.processed_products)
                self.current_metrics.processed_products += increment
                self.current_metrics.successful_enrichments += int(increment * 0.85)  # 85% success rate
                
                # Update processing rate
                if self.start_time:
                    elapsed_minutes = (datetime.now() - self.start_time).total_seconds() / 60
                    if elapsed_minutes > 0:
                        self.current_metrics.processing_rate = self.current_metrics.processed_products / elapsed_minutes
                
                # Simulate quality metrics improvement
                progress_pct = self.current_metrics.processed_products / self.current_metrics.total_products
                self.quality_metrics.pricing_completeness = min(75, progress_pct * 80)
                self.quality_metrics.availability_completeness = min(85, progress_pct * 90)
                self.quality_metrics.specifications_completeness = min(60, progress_pct * 65)
                self.quality_metrics.images_completeness = min(45, progress_pct * 50)
                self.quality_metrics.overall_quality_score = (
                    self.quality_metrics.pricing_completeness * 0.3 +
                    self.quality_metrics.availability_completeness * 0.25 +
                    self.quality_metrics.specifications_completeness * 0.25 +
                    self.quality_metrics.images_completeness * 0.2
                )
        
        return {
            "metrics": self.current_metrics,
            "quality": self.quality_metrics,
            "status": self.pipeline_status,
            "last_update": self.last_update
        }
    
    def render_dashboard(self):
        """Render the complete dashboard"""
        layout = self.create_dashboard_layout()
        
        # Update data
        self.update_dashboard_data()
        
        # Populate layout
        layout["header"].update(self.create_header_panel())
        layout["progress"].update(self.create_progress_panel())
        layout["quality"].update(self.create_quality_panel())
        layout["metrics"].update(Panel(self.create_metrics_table()))
        layout["alerts"].update(self.create_alerts_panel())
        layout["footer"].update(self.create_footer_panel())
        
        return layout
    
    async def start_pipeline(self):
        """Start the enrichment pipeline"""
        try:
            self.pipeline_status = "Starting..."
            self.start_time = datetime.now()
            
            # Initialize pipeline
            excel_file = "docs/reference/ProductData (Top 3 Cats).xlsx"
            if not Path(excel_file).exists():
                self.pipeline_status = "Error: Excel file not found"
                return
            
            self.pipeline = ProductEnrichmentPipeline(excel_file, max_workers=5)
            
            # Set initial metrics
            import pandas as pd
            df = pd.read_excel(excel_file)
            self.current_metrics.total_products = len(df)
            self.current_metrics.processed_products = 0
            self.current_metrics.successful_enrichments = 0
            
            self.pipeline_status = "Running"
            
            # Run pipeline in background
            await self.pipeline.run_pipeline()
            
            self.pipeline_status = "Completed"
            
        except Exception as e:
            self.pipeline_status = f"Error: {str(e)}"
            logger.error(f"Pipeline failed: {e}")
    
    def start_pipeline_thread(self):
        """Start pipeline in separate thread"""
        def run_pipeline():
            asyncio.run(self.start_pipeline())
        
        pipeline_thread = threading.Thread(target=run_pipeline)
        pipeline_thread.daemon = True
        pipeline_thread.start()
    
    async def test_sample(self):
        """Run pipeline with small sample for testing"""
        try:
            self.pipeline_status = "Testing..."
            self.start_time = datetime.now()
            
            # Create sample data for testing
            self.current_metrics.total_products = 100
            self.current_metrics.processed_products = 0
            self.current_metrics.successful_enrichments = 0
            
            self.pipeline_status = "Running (Test)"
            
            # Simulate test processing
            for i in range(100):
                await asyncio.sleep(0.1)  # Simulate processing time
                self.current_metrics.processed_products += 1
                self.current_metrics.successful_enrichments += 1 if i % 10 != 0 else 0  # 90% success rate
            
            self.pipeline_status = "Test Completed"
            
        except Exception as e:
            self.pipeline_status = f"Test Error: {str(e)}"
    
    def run_interactive_dashboard(self):
        """Run interactive dashboard with keyboard controls"""
        if not RICH_AVAILABLE:
            self.run_basic_dashboard()
            return
        
        self.console.print("[bold green]Starting Horme Product Enrichment Dashboard...[/]")
        
        try:
            with Live(self.render_dashboard(), refresh_per_second=1, screen=True) as live:
                self.running = True
                
                # Input handling in separate thread
                def handle_input():
                    while self.running:
                        try:
                            key = input().lower().strip()
                            
                            if key == 'q':
                                self.running = False
                                break
                            elif key == 's':
                                self.console.print("Starting full enrichment pipeline...")
                                self.start_pipeline_thread()
                            elif key == 't':
                                self.console.print("Starting test with sample data...")
                                asyncio.run(self.test_sample())
                            elif key == 'p':
                                if self.pipeline_status == "Running":
                                    self.pipeline_status = "Paused"
                                elif self.pipeline_status == "Paused":
                                    self.pipeline_status = "Running"
                            elif key == 'r':
                                self.update_dashboard_data()
                                
                        except (EOFError, KeyboardInterrupt):
                            self.running = False
                            break
                
                input_thread = threading.Thread(target=handle_input)
                input_thread.daemon = True
                input_thread.start()
                
                # Main dashboard loop
                while self.running:
                    live.update(self.render_dashboard())
                    time.sleep(1)
                    
        except KeyboardInterrupt:
            pass
        finally:
            self.running = False
            self.console.print("\n[bold red]Dashboard stopped.[/]")
    
    def run_basic_dashboard(self):
        """Run basic text-based dashboard without Rich"""
        print("HORME PRODUCT ENRICHMENT DASHBOARD (Basic Mode)")
        print("=" * 60)
        print("Commands: q=quit, s=start, t=test, r=refresh")
        print("=" * 60)
        
        self.running = True
        
        while self.running:
            try:
                # Display basic metrics
                print(f"\nStatus: {self.pipeline_status}")
                print(f"Processed: {self.current_metrics.processed_products:,} / {self.current_metrics.total_products:,}")
                
                if self.current_metrics.processed_products > 0:
                    success_rate = (self.current_metrics.successful_enrichments / self.current_metrics.processed_products) * 100
                    print(f"Success Rate: {success_rate:.1f}%")
                    print(f"Processing Rate: {self.current_metrics.processing_rate:.1f} products/min")
                
                # Get user input
                command = input("\nEnter command (q/s/t/r): ").lower().strip()
                
                if command == 'q':
                    break
                elif command == 's':
                    print("Starting full enrichment pipeline...")
                    self.start_pipeline_thread()
                elif command == 't':
                    print("Starting test with sample data...")
                    asyncio.run(self.test_sample())
                elif command == 'r':
                    self.update_dashboard_data()
                    print("Dashboard refreshed")
                else:
                    print("Unknown command")
                    
            except KeyboardInterrupt:
                break
        
        print("\nDashboard stopped.")

async def run_quality_monitoring():
    """Run continuous quality monitoring"""
    monitor = EnrichmentQualityMonitor()
    
    while True:
        try:
            await monitor.monitor_enrichment_quality()
            await asyncio.sleep(300)  # Monitor every 5 minutes
        except Exception as e:
            logger.error(f"Quality monitoring error: {e}")
            await asyncio.sleep(60)  # Wait 1 minute before retry

def main():
    """Main function"""
    print("Horme Product Enrichment Dashboard")
    print("==================================")
    
    dashboard = EnrichmentDashboard()
    
    try:
        # Start quality monitoring in background
        if RICH_AVAILABLE:
            # Use rich interactive dashboard
            dashboard.run_interactive_dashboard()
        else:
            # Use basic text dashboard
            dashboard.run_basic_dashboard()
            
    except KeyboardInterrupt:
        print("\nShutting down dashboard...")
    except Exception as e:
        print(f"Dashboard error: {e}")

if __name__ == "__main__":
    main()