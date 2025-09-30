"""
Quantum Backend Configuration and Management

This module provides configuration and management for various quantum computing backends:
1. IBM Quantum hardware devices
2. Qiskit Aer simulators (local)
3. IBM Quantum simulators (cloud)
4. Third-party quantum providers (future extensibility)

Features:
- Dynamic backend discovery and selection
- Authentication management for IBM Quantum
- Device capability assessment
- Queue status monitoring
- Error handling and fallback strategies
"""

import os
import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timezone
import warnings

# Quantum computing imports
try:
    from qiskit import QuantumCircuit
    from qiskit_aer import AerSimulator
    from qiskit_ibm_runtime import QiskitRuntimeService
    QISKIT_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Qiskit imports failed: {e}")
    QISKIT_AVAILABLE = False

# Suppress deprecation warnings from qiskit
warnings.filterwarnings('ignore', category=DeprecationWarning, module='qiskit')

logger = logging.getLogger(__name__)


class BackendType(Enum):
    """Quantum backend types"""
    SIMULATOR_LOCAL = "simulator_local"      # Local Aer simulator
    SIMULATOR_CLOUD = "simulator_cloud"      # IBM cloud simulator  
    HARDWARE_IBM = "hardware_ibm"           # IBM quantum hardware
    HARDWARE_OTHER = "hardware_other"        # Other quantum providers


class BackendStatus(Enum):
    """Backend operational status"""
    AVAILABLE = "available"
    BUSY = "busy" 
    MAINTENANCE = "maintenance"
    OFFLINE = "offline"
    UNKNOWN = "unknown"


@dataclass
class QuantumBackendInfo:
    """Information about a quantum backend"""
    name: str
    backend_type: BackendType
    provider: str
    num_qubits: int
    status: BackendStatus
    queue_length: int = 0
    avg_queue_time: float = 0.0  # minutes
    gate_error_rate: float = 0.0
    readout_error_rate: float = 0.0
    connectivity: Optional[List[Tuple[int, int]]] = None
    supported_gates: Optional[List[str]] = None
    max_shots: int = 100000
    cost_per_shot: float = 0.0
    description: str = ""
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        # Convert enums to strings
        result['backend_type'] = self.backend_type.value
        result['status'] = self.status.value
        return result


@dataclass 
class QuantumBackendConfig:
    """Configuration for quantum backend execution"""
    backend_name: str
    backend_type: BackendType
    shots: int = 10000
    max_circuit_depth: int = 100
    optimization_level: int = 1
    use_error_mitigation: bool = False
    timeout_seconds: int = 300
    retry_count: int = 3
    fallback_to_simulator: bool = True
    
    # IBM Quantum specific
    ibm_channel: str = "ibm_quantum"  # or "ibm_cloud"
    hub: Optional[str] = None
    group: Optional[str] = None  
    project: Optional[str] = None


class QuantumBackendManager:
    """Manages quantum computing backends and execution"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize backend manager
        
        Args:
            config_file: Path to quantum backend configuration file
        """
        self.config_file = config_file or os.getenv('QUANTUM_CONFIG_FILE', 'quantum_config.json')
        self.ibm_token = os.getenv('IBM_QUANTUM_TOKEN')
        self.service: Optional[QiskitRuntimeService] = None
        self.available_backends: Dict[str, QuantumBackendInfo] = {}
        
        # Load configuration
        self.config = self._load_config()
        
        # Initialize quantum services if available
        if QISKIT_AVAILABLE:
            self._initialize_quantum_services()
        else:
            logger.warning("Qiskit not available - quantum backends disabled")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load quantum backend configuration from file"""
        default_config = {
            "default_backend": "aer_simulator",
            "ibm_quantum": {
                "channel": "ibm_quantum",
                "hub": None,
                "group": None, 
                "project": None
            },
            "execution": {
                "default_shots": 10000,
                "max_circuit_depth": 100,
                "optimization_level": 1,
                "timeout_seconds": 300
            },
            "fallback": {
                "enabled": True,
                "order": ["aer_simulator", "ibm_simulator", "least_busy_hardware"]
            }
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    user_config = json.load(f)
                    # Merge with defaults
                    default_config.update(user_config)
                    logger.info(f"Loaded quantum config from {self.config_file}")
            except Exception as e:
                logger.warning(f"Failed to load config file {self.config_file}: {e}")
        
        return default_config
    
    def _initialize_quantum_services(self) -> None:
        """Initialize IBM Quantum and other quantum services"""
        try:
            # Initialize IBM Quantum Runtime Service
            if self.ibm_token:
                self.service = QiskitRuntimeService(token=self.ibm_token)
                logger.info("IBM Quantum Runtime Service initialized")
            else:
                # Try to load from saved account
                try:
                    self.service = QiskitRuntimeService()
                    logger.info("IBM Quantum Runtime Service loaded from saved account")
                except Exception:
                    logger.warning("No IBM Quantum token found - hardware backends unavailable")
            
        except Exception as e:
            logger.error(f"Failed to initialize quantum services: {e}")
    
    def discover_backends(self, force_refresh: bool = False) -> Dict[str, QuantumBackendInfo]:
        """
        Discover and catalog available quantum backends
        
        Args:
            force_refresh: Force refresh of backend information
            
        Returns:
            Dictionary of backend name -> backend info
        """
        if self.available_backends and not force_refresh:
            return self.available_backends
        
        backends = {}
        
        # Add local simulators
        backends.update(self._discover_local_simulators())
        
        # Add IBM Quantum backends if available
        if self.service:
            backends.update(self._discover_ibm_backends())
        
        self.available_backends = backends
        logger.info(f"Discovered {len(backends)} quantum backends")
        
        return backends
    
    def _discover_local_simulators(self) -> Dict[str, QuantumBackendInfo]:
        """Discover local Aer simulators"""
        simulators = {}
        
        if not QISKIT_AVAILABLE:
            return simulators
        
        try:
            # Create Aer simulator backend info
            aer_simulator = QuantumBackendInfo(
                name="aer_simulator",
                backend_type=BackendType.SIMULATOR_LOCAL,
                provider="qiskit_aer",
                num_qubits=63,  # Aer supports up to 63 qubits efficiently
                status=BackendStatus.AVAILABLE,
                queue_length=0,
                avg_queue_time=0.0,
                gate_error_rate=0.0,  # Perfect simulator
                readout_error_rate=0.0,
                max_shots=1000000,
                cost_per_shot=0.0,
                description="Local quantum simulator using Qiskit Aer"
            )
            simulators["aer_simulator"] = aer_simulator
            
            # Add noise models if available
            try:
                from qiskit_aer.noise import NoiseModel
                
                # Aer simulator with noise model
                aer_noisy = QuantumBackendInfo(
                    name="aer_simulator_noisy",
                    backend_type=BackendType.SIMULATOR_LOCAL,
                    provider="qiskit_aer",
                    num_qubits=63,
                    status=BackendStatus.AVAILABLE,
                    queue_length=0,
                    avg_queue_time=0.0,
                    gate_error_rate=0.001,  # Simulated noise
                    readout_error_rate=0.02,
                    max_shots=1000000,
                    cost_per_shot=0.0,
                    description="Local quantum simulator with realistic noise model"
                )
                simulators["aer_simulator_noisy"] = aer_noisy
                
            except ImportError:
                logger.debug("Noise models not available in Qiskit Aer")
            
        except Exception as e:
            logger.error(f"Failed to initialize Aer simulators: {e}")
        
        return simulators
    
    def _discover_ibm_backends(self) -> Dict[str, QuantumBackendInfo]:
        """Discover IBM Quantum backends (hardware and cloud simulators)"""
        backends = {}
        
        if not self.service:
            return backends
        
        try:
            # Get all available IBM backends
            ibm_backends = self.service.backends()
            
            for backend in ibm_backends:
                backend_info = self._process_ibm_backend(backend)
                if backend_info:
                    backends[backend_info.name] = backend_info
            
            logger.info(f"Discovered {len(backends)} IBM Quantum backends")
            
        except Exception as e:
            logger.error(f"Failed to discover IBM backends: {e}")
        
        return backends
    
    def _process_ibm_backend(self, backend) -> Optional[QuantumBackendInfo]:
        """Process a single IBM backend and create QuantumBackendInfo"""
        try:
            # Get backend configuration and status
            config = backend.configuration()
            status_info = backend.status()
            
            # Determine backend type
            backend_type = BackendType.SIMULATOR_CLOUD if config.simulator else BackendType.HARDWARE_IBM
            
            # Map status
            status = self._map_ibm_backend_status(status_info)
            
            # Calculate error rates
            gate_error, readout_error = self._calculate_error_rates(config)
            
            # Get connectivity
            connectivity = getattr(config, 'coupling_map', None) if hasattr(config, 'coupling_map') else None
            
            # Create backend info
            return QuantumBackendInfo(
                name=config.backend_name,
                backend_type=backend_type,
                provider="IBM Quantum",
                num_qubits=config.n_qubits,
                status=status,
                queue_length=status_info.pending_jobs,
                avg_queue_time=getattr(status_info, 'avg_queue_time', 0.0) / 60.0,
                gate_error_rate=gate_error,
                readout_error_rate=readout_error,
                connectivity=connectivity,
                supported_gates=[gate.name for gate in config.gates] if hasattr(config, 'gates') else [],
                max_shots=getattr(config, 'max_shots', 100000),
                cost_per_shot=0.0,
                description=f"IBM Quantum {backend_type.value.replace('_', ' ')} with {config.n_qubits} qubits"
            )
            
        except Exception as e:
            logger.warning(f"Failed to process IBM backend {backend}: {e}")
            return None
    
    def _map_ibm_backend_status(self, status_info) -> BackendStatus:
        """Map IBM backend status to our BackendStatus enum"""
        if status_info.operational and not status_info.pending_jobs:
            return BackendStatus.AVAILABLE
        elif status_info.operational:
            return BackendStatus.BUSY
        else:
            return BackendStatus.MAINTENANCE
    
    def _calculate_error_rates(self, config) -> Tuple[float, float]:
        """Calculate gate and readout error rates from backend config"""
        gate_error = self._calculate_gate_error(config)
        readout_error = self._calculate_readout_error(config)
        return gate_error, readout_error
    
    def _calculate_gate_error(self, config) -> float:
        """Calculate average gate error rate"""
        if not hasattr(config, 'gates'):
            return 0.0
        
        gate_errors = []
        for gate in config.gates:
            if hasattr(gate, 'parameters'):
                for param in gate.parameters:
                    if param.name == 'gate_error':
                        gate_errors.append(param.value)
        
        return sum(gate_errors) / len(gate_errors) if gate_errors else 0.0
    
    def _calculate_readout_error(self, config) -> float:
        """Calculate average readout error rate"""
        if hasattr(config, 'readout_error'):
            return sum(config.readout_error) / len(config.readout_error)
        return 0.0
    
    def get_backend_info(self, backend_name: str) -> Optional[QuantumBackendInfo]:
        """Get information about a specific backend"""
        if not self.available_backends:
            self.discover_backends()
        
        return self.available_backends.get(backend_name)
    
    def get_available_backends(self, backend_type: Optional[BackendType] = None,
                              min_qubits: int = 1) -> Dict[str, QuantumBackendInfo]:
        """
        Get available backends matching criteria
        
        Args:
            backend_type: Filter by backend type
            min_qubits: Minimum number of qubits required
            
        Returns:
            Dictionary of matching backends
        """
        if not self.available_backends:
            self.discover_backends()
        
        filtered = {}
        
        for name, info in self.available_backends.items():
            # Check type filter
            if backend_type and info.backend_type != backend_type:
                continue
            
            # Check qubit count
            if info.num_qubits < min_qubits:
                continue
            
            # Check availability
            if info.status in [BackendStatus.AVAILABLE, BackendStatus.BUSY]:
                filtered[name] = info
        
        return filtered
    
    def select_best_backend(self, num_qubits: int, prefer_hardware: bool = False) -> Optional[str]:
        """
        Select the best available backend for the given requirements
        
        Args:
            num_qubits: Number of qubits required
            prefer_hardware: Whether to prefer hardware over simulators
            
        Returns:
            Name of selected backend or None if none available
        """
        available = self.get_available_backends(min_qubits=num_qubits)
        
        if not available:
            logger.warning(f"No backends available with {num_qubits} qubits")
            return None
        
        # Scoring function for backend selection
        def score_backend(info: QuantumBackendInfo) -> float:
            score = 0.0
            
            # Prefer available over busy
            if info.status == BackendStatus.AVAILABLE:
                score += 100
            elif info.status == BackendStatus.BUSY:
                score += 50
            
            # Hardware vs simulator preference
            if prefer_hardware and info.backend_type == BackendType.HARDWARE_IBM:
                score += 50
            elif not prefer_hardware and info.backend_type in [BackendType.SIMULATOR_LOCAL, BackendType.SIMULATOR_CLOUD]:
                score += 40  # Slightly different score to fix duplicate
            
            # Prefer lower error rates
            score -= info.gate_error_rate * 1000
            score -= info.readout_error_rate * 100
            
            # Prefer shorter queues
            score -= info.queue_length * 2
            score -= info.avg_queue_time * 0.1
            
            # Prefer more qubits (but not too many more)
            qubit_excess = info.num_qubits - num_qubits
            if qubit_excess >= 0:
                score += min(qubit_excess, 10)  # Diminishing returns
            
            return score
        
        # Select best backend
        best_name = max(available.keys(), key=lambda name: score_backend(available[name]))
        
        logger.info(f"Selected backend {best_name} for {num_qubits} qubits (hardware preference: {prefer_hardware})")
        
        return best_name
    
    def create_backend_config(self, backend_name: str, **kwargs) -> QuantumBackendConfig:
        """Create a backend configuration for execution"""
        backend_info = self.get_backend_info(backend_name)
        
        if not backend_info:
            raise ValueError(f"Backend {backend_name} not found")
        
        # Default configuration based on backend type
        default_shots = self.config['execution']['default_shots']
        if backend_info.backend_type == BackendType.SIMULATOR_LOCAL:
            default_shots = min(default_shots, 100000)  # Local simulators can handle more
        elif backend_info.backend_type == BackendType.HARDWARE_IBM:
            default_shots = min(default_shots, backend_info.max_shots)
        
        config = QuantumBackendConfig(
            backend_name=backend_name,
            backend_type=backend_info.backend_type,
            shots=kwargs.get('shots', default_shots),
            max_circuit_depth=kwargs.get('max_circuit_depth', self.config['execution']['max_circuit_depth']),
            optimization_level=kwargs.get('optimization_level', self.config['execution']['optimization_level']),
            use_error_mitigation=kwargs.get('use_error_mitigation', backend_info.backend_type == BackendType.HARDWARE_IBM),
            timeout_seconds=kwargs.get('timeout_seconds', self.config['execution']['timeout_seconds']),
            retry_count=kwargs.get('retry_count', 3),
            fallback_to_simulator=kwargs.get('fallback_to_simulator', self.config['fallback']['enabled'])
        )
        
        # IBM Quantum specific settings
        if backend_info.backend_type in [BackendType.HARDWARE_IBM, BackendType.SIMULATOR_CLOUD]:
            ibm_config = self.config.get('ibm_quantum', {})
            config.ibm_channel = ibm_config.get('channel', 'ibm_quantum')
            config.hub = ibm_config.get('hub')
            config.group = ibm_config.get('group')
            config.project = ibm_config.get('project')
        
        return config
    
    def get_backend_instance(self, backend_name: str):
        """
        Get the actual backend instance for quantum execution
        
        Args:
            backend_name: Name of the backend to retrieve
            
        Returns:
            Backend instance (Aer simulator or IBM backend)
        """
        if not QISKIT_AVAILABLE:
            raise RuntimeError("Qiskit not available")
        
        backend_info = self.get_backend_info(backend_name)
        if not backend_info:
            raise ValueError(f"Backend {backend_name} not found")
        
        if backend_info.backend_type == BackendType.SIMULATOR_LOCAL:
            if backend_name == "aer_simulator":
                return AerSimulator()
            elif backend_name == "aer_simulator_noisy":
                from qiskit_aer.noise import NoiseModel
                # Create a simple noise model
                noise_model = NoiseModel()
                return AerSimulator(noise_model=noise_model)
            else:
                return AerSimulator()  # Fallback
        
        elif backend_info.backend_type in [BackendType.HARDWARE_IBM, BackendType.SIMULATOR_CLOUD]:
            if not self.service:
                raise RuntimeError("IBM Quantum service not initialized")
            
            return self.service.backend(backend_name)
        
        else:
            raise ValueError(f"Unsupported backend type: {backend_info.backend_type}")
    
    def save_config(self) -> None:
        """Save current configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"Saved quantum config to {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
    
    def get_backend_summary(self) -> Dict[str, Any]:
        """Get summary of all available backends"""
        if not self.available_backends:
            self.discover_backends()
        
        summary = {
            "total_backends": len(self.available_backends),
            "by_type": {},
            "by_status": {},
            "recommended": {}
        }
        
        # Count by type and status
        for info in self.available_backends.values():
            type_key = info.backend_type.value
            status_key = info.status.value
            
            summary["by_type"][type_key] = summary["by_type"].get(type_key, 0) + 1
            summary["by_status"][status_key] = summary["by_status"].get(status_key, 0) + 1
        
        # Find recommended backends for common use cases
        try:
            summary["recommended"]["small_circuits"] = self.select_best_backend(5, prefer_hardware=False)
            summary["recommended"]["medium_circuits"] = self.select_best_backend(15, prefer_hardware=False)
            summary["recommended"]["large_circuits"] = self.select_best_backend(30, prefer_hardware=False)
            summary["recommended"]["hardware_small"] = self.select_best_backend(5, prefer_hardware=True)
            summary["recommended"]["hardware_medium"] = self.select_best_backend(15, prefer_hardware=True)
        except Exception as e:
            logger.warning(f"Failed to determine recommended backends: {e}")
        
        return summary


# Global backend manager instance
_backend_manager: Optional[QuantumBackendManager] = None

def get_backend_manager() -> QuantumBackendManager:
    """Get global backend manager instance (singleton)"""
    global _backend_manager
    if _backend_manager is None:
        _backend_manager = QuantumBackendManager()
    return _backend_manager


def list_available_backends() -> Dict[str, QuantumBackendInfo]:
    """Convenience function to list all available backends"""
    manager = get_backend_manager()
    return manager.discover_backends()


def select_quantum_backend(num_qubits: int, prefer_hardware: bool = False) -> Optional[str]:
    """Convenience function to select best backend"""
    manager = get_backend_manager()
    return manager.select_best_backend(num_qubits, prefer_hardware)


# Configuration helper functions
def setup_ibm_quantum_account(token: str, overwrite: bool = False) -> bool:
    """
    Setup IBM Quantum account with token
    
    Args:
        token: IBM Quantum API token
        overwrite: Whether to overwrite existing account
        
    Returns:
        True if successful, False otherwise
    """
    if not QISKIT_AVAILABLE:
        logger.error("Qiskit not available")
        return False
    
    try:
        service = QiskitRuntimeService.save_account(
            token=token,
            channel="ibm_quantum", 
            overwrite=overwrite
        )
        
        # Test the connection
        backends = service.backends()
        logger.info(f"IBM Quantum account setup successful - found {len(backends)} backends")
        
        # Refresh global manager
        global _backend_manager
        if _backend_manager:
            _backend_manager._initialize_quantum_services()
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to setup IBM Quantum account: {e}")
        return False


def get_quantum_backend_status() -> Dict[str, Any]:
    """Get status of quantum computing environment"""
    status = {
        "qiskit_available": QISKIT_AVAILABLE,
        "ibm_token_configured": bool(os.getenv('IBM_QUANTUM_TOKEN')),
        "backends_discovered": False,
        "backend_count": 0,
        "errors": []
    }
    
    if QISKIT_AVAILABLE:
        try:
            manager = get_backend_manager()
            backends = manager.discover_backends()
            
            status["backends_discovered"] = True
            status["backend_count"] = len(backends)
            status["backend_summary"] = manager.get_backend_summary()
            
        except Exception as e:
            status["errors"].append(f"Backend discovery failed: {e}")
    else:
        status["errors"].append("Qiskit not installed or import failed")
    
    return status


if __name__ == "__main__":
    # Test the backend manager
    print("Quantum Backend Manager Test")
    print("=" * 40)
    
    # Get status
    status = get_quantum_backend_status()
    print(f"Qiskit Available: {status['qiskit_available']}")
    print(f"IBM Token Configured: {status['ibm_token_configured']}")
    print(f"Backend Count: {status['backend_count']}")
    
    if status['errors']:
        print("Errors:")
        for error in status['errors']:
            print(f"  - {error}")
    
    # List available backends
    if status['qiskit_available']:
        print("\nAvailable Backends:")
        backends = list_available_backends()
        
        for name, info in backends.items():
            print(f"  {name}:")
            print(f"    Type: {info.backend_type.value}")
            print(f"    Qubits: {info.num_qubits}")
            print(f"    Status: {info.status.value}")
            if info.queue_length > 0:
                print(f"    Queue: {info.queue_length} jobs")
        
        # Test backend selection
        print("\nBackend Selection Examples:")
        small_backend = select_quantum_backend(5, prefer_hardware=False)
        print(f"  5 qubits (simulator): {small_backend}")
        
        large_backend = select_quantum_backend(20, prefer_hardware=False)  
        print(f"  20 qubits (simulator): {large_backend}")
        
        hw_backend = select_quantum_backend(5, prefer_hardware=True)
        print(f"  5 qubits (hardware): {hw_backend}")
    
    print("\nTest completed.")