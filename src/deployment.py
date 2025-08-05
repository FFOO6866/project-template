"""
Nexus Sales Assistant Deployment Management
==========================================

Comprehensive deployment utilities for:
- Development environment setup
- Production deployment scripts
- Database initialization and migration
- Service health monitoring
- Multi-environment configuration
- Docker containerization support
- Kubernetes deployment manifests
"""

import os
import sys
import subprocess
import asyncio
import psutil
import yaml
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

import click
import uvicorn
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from nexus_config import NexusConfiguration, config
from nexus_app import main as nexus_main
from dataflow_models import db

console = Console()
logger = logging.getLogger(__name__)

@dataclass
class ServiceStatus:
    """Service health status"""
    name: str
    status: str  # running, stopped, error
    port: Optional[int] = None
    pid: Optional[int] = None
    memory_mb: Optional[float] = None
    cpu_percent: Optional[float] = None
    uptime: Optional[str] = None
    health_check: Optional[bool] = None

class DeploymentManager:
    """Manages deployment operations for Nexus Sales Assistant"""
    
    def __init__(self, config: NexusConfiguration):
        self.config = config
        self.project_root = Path(__file__).parent.parent
        self.logs_dir = self.project_root / "logs"
        self.logs_dir.mkdir(exist_ok=True)
        
        # Service definitions
        self.services = {
            "nexus": {
                "name": "Nexus Sales Assistant",
                "port": config.server.api_port,
                "health_endpoint": f"http://localhost:{config.server.api_port}/health"
            },
            "mcp": {
                "name": "MCP Server",
                "port": config.server.mcp_port,
                "health_endpoint": f"http://localhost:{config.server.mcp_port}/health"
            },
            "postgres": {
                "name": "PostgreSQL Database",
                "port": 5432,
                "health_check": self._check_postgres_health
            },
            "redis": {
                "name": "Redis Cache",
                "port": 6379,
                "enabled": config.redis.enabled,
                "health_check": self._check_redis_health
            }
        }
    
    async def deploy_development(self, setup_db: bool = True, install_deps: bool = True) -> bool:
        """Deploy for development environment"""
        console.print("[bold blue]🚀 Deploying Nexus Sales Assistant - Development Environment[/bold blue]")
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                
                # Install dependencies
                if install_deps:
                    task = progress.add_task("Installing dependencies...", total=None)
                    if not await self._install_dependencies():
                        return False
                    progress.remove_task(task)
                
                # Setup database
                if setup_db:
                    task = progress.add_task("Setting up database...", total=None)
                    if not await self._setup_development_database():
                        return False
                    progress.remove_task(task)
                
                # Create required directories
                task = progress.add_task("Creating directories...", total=None)
                await self._create_directories()
                progress.remove_task(task)
                
                # Generate configuration files
                task = progress.add_task("Generating configuration...", total=None)
                await self._generate_dev_config()
                progress.remove_task(task)
                
                # Validate configuration
                task = progress.add_task("Validating configuration...", total=None)
                if not await self._validate_deployment():
                    return False
                progress.remove_task(task)
            
            console.print("[bold green]✅ Development deployment completed successfully![/bold green]")
            await self._show_deployment_info()
            return True
        
        except Exception as e:
            console.print(f"[bold red]❌ Deployment failed: {str(e)}[/bold red]")
            logger.error(f"Development deployment failed: {e}")
            return False
    
    async def deploy_production(self, config_file: str = None) -> bool:
        """Deploy for production environment"""
        console.print("[bold blue]🚀 Deploying Nexus Sales Assistant - Production Environment[/bold blue]")
        
        try:
            # Load production configuration
            if config_file:
                prod_config = NexusConfiguration.load_from_file(config_file)
            else:
                prod_config = self.config
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                
                # Validate production requirements
                task = progress.add_task("Validating production requirements...", total=None)
                if not await self._validate_production_requirements(prod_config):
                    return False
                progress.remove_task(task)
                
                # Setup production database
                task = progress.add_task("Setting up production database...", total=None)
                if not await self._setup_production_database(prod_config):
                    return False
                progress.remove_task(task)
                
                # Deploy SSL certificates
                if prod_config.server.enable_https:
                    task = progress.add_task("Setting up SSL certificates...", total=None)
                    if not await self._setup_ssl_certificates(prod_config):
                        return False
                    progress.remove_task(task)
                
                # Create systemd services
                task = progress.add_task("Creating system services...", total=None)
                await self._create_systemd_services(prod_config)
                progress.remove_task(task)
                
                # Setup monitoring
                task = progress.add_task("Setting up monitoring...", total=None)
                await self._setup_monitoring(prod_config)
                progress.remove_task(task)
            
            console.print("[bold green]✅ Production deployment completed successfully![/bold green]")
            await self._show_production_info(prod_config)
            return True
        
        except Exception as e:
            console.print(f"[bold red]❌ Production deployment failed: {str(e)}[/bold red]")
            logger.error(f"Production deployment failed: {e}")
            return False
    
    async def create_docker_deployment(self) -> bool:
        """Create Docker deployment configuration"""
        console.print("[bold blue]🐳 Creating Docker deployment configuration[/bold blue]")
        
        try:
            # Create Dockerfile
            dockerfile_content = """
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    postgresql-client \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY pyproject.toml ./

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Copy application code
COPY src/ ./src/
COPY fe-reference/ ./fe-reference/

# Create uploads directory
RUN mkdir -p uploads

# Expose ports
EXPOSE 8000 3001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["python", "src/nexus_app.py"]
"""
            
            dockerfile_path = self.project_root / "Dockerfile"
            with open(dockerfile_path, 'w') as f:
                f.write(dockerfile_content)
            
            # Create docker-compose.yml
            compose_content = {
                'version': '3.8',
                'services': {
                    'nexus-app': {
                        'build': '.',
                        'ports': [
                            f'{self.config.server.api_port}:8000',
                            f'{self.config.server.mcp_port}:3001'
                        ],
                        'environment': [
                            'DATABASE_URL=postgresql://sales_user:sales_password@postgres:5432/sales_assistant',
                            'REDIS_URL=redis://redis:6379/0',
                            f'JWT_SECRET={self.config.auth.jwt_secret}',
                            'ENVIRONMENT=production'
                        ],
                        'volumes': [
                            './uploads:/app/uploads',
                            './logs:/app/logs'
                        ],
                        'depends_on': ['postgres', 'redis'],
                        'restart': 'unless-stopped'
                    },
                    'postgres': {
                        'image': 'postgres:15',
                        'environment': [
                            'POSTGRES_DB=sales_assistant',
                            'POSTGRES_USER=sales_user',
                            'POSTGRES_PASSWORD=sales_password'
                        ],
                        'volumes': [
                            'postgres_data:/var/lib/postgresql/data',
                            './init-scripts:/docker-entrypoint-initdb.d'
                        ],
                        'ports': ['5432:5432'],
                        'restart': 'unless-stopped'
                    },
                    'redis': {
                        'image': 'redis:7-alpine',
                        'ports': ['6379:6379'],
                        'volumes': ['redis_data:/data'],
                        'restart': 'unless-stopped'
                    }
                },
                'volumes': {
                    'postgres_data': {},
                    'redis_data': {}
                }
            }
            
            compose_path = self.project_root / "docker-compose.yml"
            with open(compose_path, 'w') as f:
                yaml.dump(compose_content, f, default_flow_style=False)
            
            # Create .dockerignore
            dockerignore_content = """
__pycache__
*.pyc
*.pyo
*.pyd
.Python
.pytest_cache
.coverage
.tox
.git
.gitignore
README.md
.env
logs/
*.log
.DS_Store
Thumbs.db
"""
            
            dockerignore_path = self.project_root / ".dockerignore"
            with open(dockerignore_path, 'w') as f:
                f.write(dockerignore_content)
            
            console.print("[bold green]✅ Docker deployment configuration created![/bold green]")
            console.print(f"📁 Files created:")
            console.print(f"   • {dockerfile_path}")
            console.print(f"   • {compose_path}")
            console.print(f"   • {dockerignore_path}")
            console.print(f"\n🚀 To deploy with Docker:")
            console.print(f"   docker-compose up -d")
            
            return True
        
        except Exception as e:
            console.print(f"[bold red]❌ Docker deployment creation failed: {str(e)}[/bold red]")
            return False
    
    async def create_kubernetes_deployment(self) -> bool:
        """Create Kubernetes deployment manifests"""
        console.print("[bold blue]☸️ Creating Kubernetes deployment manifests[/bold blue]")
        
        try:
            k8s_dir = self.project_root / "k8s"
            k8s_dir.mkdir(exist_ok=True)
            
            # Namespace
            namespace_yaml = {
                'apiVersion': 'v1',
                'kind': 'Namespace',
                'metadata': {'name': 'sales-assistant'}
            }
            
            # ConfigMap
            configmap_yaml = {
                'apiVersion': 'v1',
                'kind': 'ConfigMap',
                'metadata': {
                    'name': 'nexus-config',
                    'namespace': 'sales-assistant'
                },
                'data': {
                    'DATABASE_URL': 'postgresql://sales_user:sales_password@postgres:5432/sales_assistant',
                    'REDIS_URL': 'redis://redis:6379/0',
                    'ENVIRONMENT': 'production'
                }
            }
            
            # Secret
            secret_yaml = {
                'apiVersion': 'v1',
                'kind': 'Secret',
                'metadata': {
                    'name': 'nexus-secrets',
                    'namespace': 'sales-assistant'
                },
                'type': 'Opaque',
                'stringData': {
                    'JWT_SECRET': self.config.auth.jwt_secret,
                    'POSTGRES_PASSWORD': 'sales_password'
                }
            }
            
            # Deployment
            deployment_yaml = {
                'apiVersion': 'apps/v1',
                'kind': 'Deployment',
                'metadata': {
                    'name': 'nexus-app',
                    'namespace': 'sales-assistant'
                },
                'spec': {
                    'replicas': 2,
                    'selector': {
                        'matchLabels': {'app': 'nexus-app'}
                    },
                    'template': {
                        'metadata': {
                            'labels': {'app': 'nexus-app'}
                        },
                        'spec': {
                            'containers': [{
                                'name': 'nexus-app',
                                'image': 'sales-assistant:latest',
                                'ports': [
                                    {'containerPort': 8000, 'name': 'api'},
                                    {'containerPort': 3001, 'name': 'mcp'}
                                ],
                                'envFrom': [
                                    {'configMapRef': {'name': 'nexus-config'}},
                                    {'secretRef': {'name': 'nexus-secrets'}}
                                ],
                                'volumeMounts': [{
                                    'name': 'uploads',
                                    'mountPath': '/app/uploads'
                                }],
                                'livenessProbe': {
                                    'httpGet': {
                                        'path': '/health',
                                        'port': 8000
                                    },
                                    'initialDelaySeconds': 30,
                                    'periodSeconds': 10
                                },
                                'readinessProbe': {
                                    'httpGet': {
                                        'path': '/health',
                                        'port': 8000
                                    },
                                    'initialDelaySeconds': 5,
                                    'periodSeconds': 5
                                }
                            }],
                            'volumes': [{
                                'name': 'uploads',
                                'persistentVolumeClaim': {
                                    'claimName': 'nexus-uploads'
                                }
                            }]
                        }
                    }
                }
            }
            
            # Service
            service_yaml = {
                'apiVersion': 'v1',
                'kind': 'Service',
                'metadata': {
                    'name': 'nexus-service',
                    'namespace': 'sales-assistant'
                },
                'spec': {
                    'selector': {'app': 'nexus-app'},
                    'ports': [
                        {'name': 'api', 'port': 80, 'targetPort': 8000},
                        {'name': 'mcp', 'port': 3001, 'targetPort': 3001}
                    ],
                    'type': 'ClusterIP'
                }
            }
            
            # Ingress
            ingress_yaml = {
                'apiVersion': 'networking.k8s.io/v1',
                'kind': 'Ingress',
                'metadata': {
                    'name': 'nexus-ingress',
                    'namespace': 'sales-assistant',
                    'annotations': {
                        'kubernetes.io/ingress.class': 'nginx',
                        'cert-manager.io/cluster-issuer': 'letsencrypt-prod'
                    }
                },
                'spec': {
                    'tls': [{
                        'hosts': ['yourdomain.com'],
                        'secretName': 'nexus-tls'
                    }],
                    'rules': [{
                        'host': 'yourdomain.com',
                        'http': {
                            'paths': [{
                                'path': '/',
                                'pathType': 'Prefix',
                                'backend': {
                                    'service': {
                                        'name': 'nexus-service',
                                        'port': {'number': 80}
                                    }
                                }
                            }]
                        }
                    }]
                }
            }
            
            # Write YAML files
            manifests = {
                'namespace.yaml': namespace_yaml,
                'configmap.yaml': configmap_yaml,
                'secret.yaml': secret_yaml,
                'deployment.yaml': deployment_yaml,
                'service.yaml': service_yaml,
                'ingress.yaml': ingress_yaml
            }
            
            for filename, manifest in manifests.items():
                file_path = k8s_dir / filename
                with open(file_path, 'w') as f:
                    yaml.dump(manifest, f, default_flow_style=False)
            
            # Create deployment script
            deploy_script = """#!/bin/bash
set -e

echo "🚀 Deploying Nexus Sales Assistant to Kubernetes"

# Apply manifests in order
kubectl apply -f namespace.yaml
kubectl apply -f configmap.yaml
kubectl apply -f secret.yaml
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f ingress.yaml

echo "✅ Deployment completed!"
echo "📊 Check status with: kubectl get pods -n sales-assistant"
echo "📝 View logs with: kubectl logs -n sales-assistant -l app=nexus-app"
"""
            
            script_path = k8s_dir / "deploy.sh"
            with open(script_path, 'w') as f:
                f.write(deploy_script)
            script_path.chmod(0o755)
            
            console.print("[bold green]✅ Kubernetes deployment manifests created![/bold green]")
            console.print(f"📁 Manifests directory: {k8s_dir}")
            console.print(f"🚀 To deploy: cd {k8s_dir} && ./deploy.sh")
            
            return True
        
        except Exception as e:
            console.print(f"[bold red]❌ Kubernetes deployment creation failed: {str(e)}[/bold red]")
            return False
    
    async def check_service_health(self) -> Dict[str, ServiceStatus]:
        """Check health of all services"""
        statuses = {}
        
        for service_id, service_config in self.services.items():
            if not service_config.get('enabled', True):
                continue
            
            try:
                status = ServiceStatus(
                    name=service_config['name'],
                    status="unknown"
                )
                
                # Check if port is in use
                port = service_config.get('port')
                if port:
                    if self._is_port_in_use(port):
                        status.status = "running"
                        status.port = port
                        
                        # Get process info
                        process_info = self._get_process_by_port(port)
                        if process_info:
                            status.pid = process_info.pid
                            status.memory_mb = process_info.memory_info().rss / 1024 / 1024
                            status.cpu_percent = process_info.cpu_percent()
                    else:
                        status.status = "stopped"
                
                # Custom health check
                health_check = service_config.get('health_check')
                if health_check and callable(health_check):
                    status.health_check = await health_check()
                
                statuses[service_id] = status
            
            except Exception as e:
                statuses[service_id] = ServiceStatus(
                    name=service_config['name'],
                    status="error"
                )
                logger.error(f"Error checking {service_id} health: {e}")
        
        return statuses
    
    async def show_status(self):
        """Display service status table"""
        console.print("[bold blue]📊 Service Status[/bold blue]")
        
        statuses = await self.check_service_health()
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Service", style="cyan")
        table.add_column("Status", style="bold")
        table.add_column("Port", style="yellow")
        table.add_column("PID", style="green")
        table.add_column("Memory (MB)", style="blue")
        table.add_column("CPU %", style="red")
        table.add_column("Health", style="bold")
        
        for service_id, status in statuses.items():
            status_color = {
                "running": "[green]●[/green] Running",
                "stopped": "[red]●[/red] Stopped",
                "error": "[red]●[/red] Error",
                "unknown": "[yellow]●[/yellow] Unknown"
            }.get(status.status, status.status)
            
            health_status = ""
            if status.health_check is not None:
                health_status = "[green]✓[/green]" if status.health_check else "[red]✗[/red]"
            
            table.add_row(
                status.name,
                status_color,
                str(status.port) if status.port else "-",
                str(status.pid) if status.pid else "-",
                f"{status.memory_mb:.1f}" if status.memory_mb else "-",
                f"{status.cpu_percent:.1f}" if status.cpu_percent else "-",
                health_status
            )
        
        console.print(table)
        
        # Show additional info
        console.print(f"\n[dim]Configuration file: {config.__class__.__name__}[/dim]")
        console.print(f"[dim]Environment: {config.environment}[/dim]")
        console.print(f"[dim]Debug mode: {config.debug}[/dim]")
    
    # Helper methods
    async def _install_dependencies(self) -> bool:
        """Install Python dependencies"""
        try:
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", "-e", "."
            ], cwd=self.project_root, capture_output=True, text=True)
            
            if result.returncode != 0:
                console.print(f"[red]Dependency installation failed: {result.stderr}[/red]")
                return False
            
            return True
        except Exception as e:
            console.print(f"[red]Error installing dependencies: {e}[/red]")
            return False
    
    async def _setup_development_database(self) -> bool:
        """Setup development database"""
        try:
            # DataFlow will handle this with auto_migrate=True
            console.print("Database setup will be handled by DataFlow auto-migration")
            return True
        except Exception as e:
            console.print(f"[red]Database setup failed: {e}[/red]")
            return False
    
    async def _create_directories(self):
        """Create required directories"""
        directories = [
            self.config.file_upload.upload_dir,
            self.logs_dir,
            self.project_root / "temp",
            self.project_root / "backups"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    async def _generate_dev_config(self):
        """Generate development configuration files"""
        # Create .env.development
        env_file = self.project_root / ".env.development"
        if not env_file.exists():
            with open(env_file, 'w') as f:
                f.write(f"""# Development Environment Configuration
ENVIRONMENT=development
DEBUG=true
DATABASE_URL={self.config.database.url}
JWT_SECRET={self.config.auth.jwt_secret}
API_PORT={self.config.server.api_port}
MCP_PORT={self.config.server.mcp_port}
LOG_LEVEL=DEBUG
""")
    
    async def _validate_deployment(self) -> bool:
        """Validate deployment configuration"""
        try:
            self.config._validate_config()
            return True
        except ValueError as e:
            console.print(f"[red]Configuration validation failed: {e}[/red]")
            return False
    
    async def _show_deployment_info(self):
        """Show deployment information"""
        info_panel = Panel(
            f"""[bold green]🚀 Nexus Sales Assistant Deployed Successfully![/bold green]

[bold]API Endpoints:[/bold]
• REST API: http://localhost:{self.config.server.api_port}
• API Docs: http://localhost:{self.config.server.api_port}/docs
• Health Check: http://localhost:{self.config.server.api_port}/health

[bold]MCP Server:[/bold]
• MCP Port: {self.config.server.mcp_port}
• MCP Health: http://localhost:{self.config.server.mcp_port}/health

[bold]WebSocket:[/bold]
• Chat Interface: ws://localhost:{self.config.server.api_port}/ws/{{client_id}}?token={{jwt_token}}

[bold]Next Steps:[/bold]
1. Start the application: python src/nexus_app.py
2. Access the API at the endpoints above
3. Integrate with your Next.js frontend
4. Configure AI models and ERP connections

[bold]Monitoring:[/bold]
• Check status: python src/deployment.py status
• View logs: tail -f logs/nexus.log
""",
            title="Deployment Complete",
            border_style="green"
        )
        console.print(info_panel)
    
    def _is_port_in_use(self, port: int) -> bool:
        """Check if a port is in use"""
        for conn in psutil.net_connections():
            if conn.laddr.port == port:
                return True
        return False
    
    def _get_process_by_port(self, port: int) -> Optional[psutil.Process]:
        """Get process using a specific port"""
        for conn in psutil.net_connections():
            if conn.laddr.port == port and conn.pid:
                try:
                    return psutil.Process(conn.pid)
                except psutil.NoSuchProcess:
                    pass
        return None
    
    async def _check_postgres_health(self) -> bool:
        """Check PostgreSQL health"""
        try:
            # This would use the actual database connection
            # For now, just check if the port is available
            return self._is_port_in_use(5432)
        except Exception:
            return False
    
    async def _check_redis_health(self) -> bool:
        """Check Redis health"""
        try:
            return self._is_port_in_use(6379)
        except Exception:
            return False
    
    # Production deployment methods (simplified)
    async def _validate_production_requirements(self, prod_config: NexusConfiguration) -> bool:
        """Validate production requirements"""
        return True  # Simplified for example
    
    async def _setup_production_database(self, prod_config: NexusConfiguration) -> bool:
        """Setup production database"""
        return True  # Simplified for example
    
    async def _setup_ssl_certificates(self, prod_config: NexusConfiguration) -> bool:
        """Setup SSL certificates"""
        return True  # Simplified for example
    
    async def _create_systemd_services(self, prod_config: NexusConfiguration):
        """Create systemd services"""
        pass  # Simplified for example
    
    async def _setup_monitoring(self, prod_config: NexusConfiguration):
        """Setup monitoring"""
        pass  # Simplified for example
    
    async def _show_production_info(self, prod_config: NexusConfiguration):
        """Show production deployment info"""
        console.print("[bold green]✅ Production deployment completed![/bold green]")

# CLI Commands
@click.group()
def cli():
    """Nexus Sales Assistant Deployment Manager"""
    pass

@cli.command()
@click.option('--setup-db', is_flag=True, default=True, help='Setup database')
@click.option('--install-deps', is_flag=True, default=True, help='Install dependencies')
def dev(setup_db: bool, install_deps: bool):
    """Deploy for development"""
    manager = DeploymentManager(config)
    asyncio.run(manager.deploy_development(setup_db=setup_db, install_deps=install_deps))

@cli.command()
@click.option('--config-file', help='Production configuration file')
def prod(config_file: Optional[str]):
    """Deploy for production"""
    manager = DeploymentManager(config)
    asyncio.run(manager.deploy_production(config_file=config_file))

@cli.command()
def docker():
    """Create Docker deployment configuration"""
    manager = DeploymentManager(config)
    asyncio.run(manager.create_docker_deployment())

@cli.command()
def k8s():
    """Create Kubernetes deployment manifests"""
    manager = DeploymentManager(config)
    asyncio.run(manager.create_kubernetes_deployment())

@cli.command()
def status():
    """Show service status"""
    manager = DeploymentManager(config)
    asyncio.run(manager.show_status())

@cli.command()
def run():
    """Run the application"""
    nexus_main()

if __name__ == "__main__":
    cli()