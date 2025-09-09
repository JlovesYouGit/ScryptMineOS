#!/usr/bin/env python3
"""
Professional ASIC API Simulator
Implements the professional telemetry fields from engineering cliff-notes

Extends standard bmminer API with professional-grade monitoring:
- power_real: True wall power from on-board INA sensor
- nonce_error: Fraction of bad nonces (early-fail predictor)
- chain_rate[]: Per-hash-board GH/s monitoring
- voltage_domain[]: Per-board voltage precision (within 20mV)
- fan_rpm[]: Fan monitoring with failure detection (0 = failed)

Designed for fleet management and professional mining operations.
"""

import json
import logging
import random
import threading
import time
from dataclasses import asdict, dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("professional_asic_api")


@dataclass
class ChainTelemetry:
    """Per-hash-board telemetry"""
    chain_id: int
    rate: int           # Hash rate in H/s
    temp: float         # °C chain temperature
    voltage: float      # V chain voltage
    frequency: int      # MHz chain frequency
    hw_errors: int      # Hardware error count
    accepted: int       # Accepted shares
    rejected: int       # Rejected shares


@dataclass
class ASICStatus:
    """Professional ASIC status with engineering-grade telemetry"""
    # Core performance metrics
    power_real: float           # Watts from on-board INA sensor
    power_limit: float          # Watts user-configured limit
    asic_temp_max: float        # °C hottest diode reading
    asic_temp_avg: float        # °C average temperature
    nonce_error: float          # Fraction of bad nonces (0.0-1.0)
    diff_accepted: int          # Last accepted share difficulty

    # Per-chain monitoring (professional insight)
    chain_rate: List[int]       # Per-hash-board H/s
    chain_temp: List[float]     # Per-chain temperatures
    chain_voltage: List[float]  # Per-chain voltages
    chain_frequency: List[int]  # Per-chain frequencies

    # Cooling and power infrastructure
    fan_rpm: List[int]          # Fan RPMs (0 = failed fan)
    voltage_domain: List[float]  # Per-board voltage domains

    # Fleet management metrics
    total_hash_rate: float      # Total GH/s
    accept_rate: float          # Share acceptance percentage
    uptime: int                 # Seconds since last restart
    firmware_version: str       # Firmware version string

    # Economic efficiency metrics
    joules_per_th: float        # J/TH power efficiency
    daily_power_cost: float     # USD daily electricity cost
    estimated_revenue: float    # USD daily revenue estimate


class ProfessionalASICSimulator:
    """
    Simulates professional-grade ASIC telemetry
    Implements engineering cliff-notes specifications for fleet management
    """

    def __init__(
        self,
        asic_model: str = "Antminer_L7",
        base_hashrate_gh: float = TARGET_HASHRATE_GHS
    ):
        self.asic_model = asic_model
        self.base_hashrate_gh = base_hashrate_gh
        self.start_time = time.time()

        # Professional ASIC specifications (from cliff-notes)
        self.specifications = {
            "Antminer_L7": {
                "nominal_hashrate_gh": TARGET_HASHRATE_GHS,
                "nominal_power_w": 3425,
                "chain_count": 3,
                "optimal_temp_c": OPTIMAL_TEMP_C,
                "voltage_precision_mv": 20,  # Engineering cliff-notes: within 20mV
                "power_gating_us": 1,        # <1μs power gating response
                "cooling_watt_per_cm2": 500,  # vs 250 W/cm² GPU limit
                "target_jth": 0.36           # J/MH for professional efficiency
            },
            "Antminer_S21_XP": {
                "nominal_hashrate_th": 270,
                "nominal_power_w": 5150,
                "chain_count": 4,
                "optimal_temp_c": 75,
                "target_jth": 19.0           # J/TH for SHA-256
            }
        }
        
        self.current_spec = self.specifications.get(
            asic_model,
            self.specifications["Antminer_L7"]
        )
        self.chain_count = self.current_spec["chain_count"]
        
        # Initialize realistic chain performance with variation
        self.chains = []
        base_rate_per_chain = (self.base_hashrate_gh * 1e9) / self.chain_count
        
        for i in range(self.chain_count):
            # Each chain has slight performance variation (realistic)
            variation = random.uniform(0.95, 1.05)  # ±5% variation
            chain = ChainTelemetry(
                chain_id=i,
                rate=int(base_rate_per_chain * variation),
                temp=random.uniform(75, 85),  # Realistic operating temperature
                voltage=random.uniform(12.3, 12.7),  # ±0.2V variation
                frequency=random.uniform(980, 1020),  # ±2% frequency variation
                hw_errors=random.randint(0, 5),
                accepted=random.randint(50, 100),
                rejected=random.randint(0, 3)
            )
            self.chains.append(chain)
        
        # Initialize cooling system
        self.fans = [
            random.randint(4200, 4500),  # Fan 1 RPM
            random.randint(4200, 4500),  # Fan 2 RPM
            random.randint(4200, 4500),  # Fan 3 RPM
            random.randint(4200, 4500)   # Fan 4 RPM
        ]
        
        # Professional degradation simulation
        self.degradation_factor = 1.0
        self.nonce_error_base = 0.0001  # 0.01% base error rate
        
    def simulate_realistic_degradation(self) -> None:
        """Simulate realistic ASIC degradation over time"""
        uptime_hours = (time.time() - self.start_time) / 3600
        
        # Gradual performance degradation (very slow)
        yearly_degradation = 0.95  # 5% per year
        hourly_degradation = yearly_degradation ** (1 / (365 * 24))
        self.degradation_factor = hourly_degradation ** uptime_hours
        
        # Temperature-dependent nonce error rate increase
        avg_temp = sum(chain.temp for chain in self.chains) / len(self.chains)
        max(
            0,
            avg_temp - OPTIMAL_TEMP_C
        )
        
        # Nonce error rate increases with temperature and time
        self.nonce_error_rate = self.nonce_error_base * (1 + temp_stress * 2 + uptime_hours * 0.00001)
        
    def simulate_chain_variation(self) -> None:
        """Simulate realistic per-chain variation"""
        for chain in self.chains:
            # Small random variations in performance
            chain.rate += random.randint(-1000, 1000)  # ±1 kH/s variation
            chain.temp += random.uniform(-0.5, 0.5)    # ±0.5°C variation
            chain.voltage += random.uniform(
                -0.02,
                0.02)  # ±20mV variation (cliff-notes precision
            )
            chain.frequency += random.randint(-5, 5)   # ±5 MHz variation
            
            # Clamp to realistic ranges
            chain.rate = max(0, chain.rate)
            chain.temp = max(25, min(95, chain.temp))
            chain.voltage = max(11.5, min(13.0, chain.voltage))
            chain.frequency = max(900, min(1100, chain.frequency))
    
    def simulate_fan_failure(self, failure_probability: float = 0.001) -> None:
        """Simulate random fan failures"""
        for i in range(len(self.fans)):  # Consider using enumerate()  # Consider using enumerate()
            if random.random() < failure_probability:
                if self.fans[i] > 0:  # Fan was working
                    self.fans[i] = 0  # Fan failed
                    logger.warning(f"Fan {i} failed in simulation")
            elif self.fans[i] == 0 and random.random() < 0.1:
                # MAX_RETRIES% chance to "repair" failed fan (simulation convenience)
                self.fans[i] = random.randint(4000, 4500)
                logger.info(f"Fan {i} restored in simulation")
    
    def get_professional_telemetry(self) -> ASICStatus:
        """
        Generate professional-grade ASIC telemetry
        Implements all fields from engineering cliff-notes
        """
        # Update simulation state
        self.simulate_realistic_degradation()
        self.simulate_chain_variation()
        self.simulate_fan_failure()
        
        # Calculate aggregated metrics
        total_hashrate_hs = sum(chain.rate for chain in self.chains)
        total_hashrate_gh = total_hashrate_hs / 1e9
        
        avg_temp = sum(chain.temp for chain in self.chains) / len(self.chains)
        max_temp = max(chain.temp for chain in self.chains)
        
        # Professional power calculation with realistic variation
        base_power = self.current_spec["nominal_power_w"]
        temp_scaling = 1.0 + (avg_temp - OPTIMAL_TEMP_C) * 0.01  # 1% per degree above OPTIMAL_TEMP_C°C
        load_scaling = total_hashrate_gh / self.base_hashrate_gh
        power_real = base_power * temp_scaling * load_scaling * self.degradation_factor
        
        # Add realistic power measurement noise (±1% INA precision)
        power_real += random.uniform(-power_real * 0.01, power_real * 0.01)
        
        # Calculate acceptance metrics
        total_accepted = sum(chain.accepted for chain in self.chains)
        total_rejected = sum(chain.rejected for chain in self.chains)
        accept_rate = (total_accepted / (total_accepted + total_rejected)) * 100 if (total_accepted + total_rejected) > 0 else 100
        
        # Professional efficiency calculation (cliff-notes metric)
        joules_per_th = (power_real / (total_hashrate_gh * 1000)) if total_hashrate_gh > 0 else 999.0
        
        # Economic calculations (for fleet management)
        electricity_cost_kwh = ELECTRICITY_COST_KWH  # $ELECTRICITY_COST_KWH/kWh
        daily_power_cost = (power_real / 1000) * 24 * electricity_cost_kwh
        estimated_revenue = total_hashrate_gh * 0.15  # $0.15 per GH/s per day (rough estimate)
        
        return ASICStatus(
            # Core performance metrics
            power_real=round(power_real, 1),
            power_limit=round(power_real * 1.1, 1),  # 10% headroom
            asic_temp_max=round(max_temp, 1),
            asic_temp_avg=round(avg_temp, 1),
            nonce_error=round(self.nonce_error_rate, 6),
            diff_accepted=random.randint(
                60000000000,
                70000000000),  # Realistic difficulty
            
            # Per-chain monitoring (professional insight)
            chain_rate=[chain.rate for chain in self.chains],
            chain_temp=[round(chain.temp, 1) for chain in self.chains],
            chain_voltage=[round(chain.voltage, 3) for chain in self.chains],
            chain_frequency=[chain.frequency for chain in self.chains],
            
            # Cooling and power infrastructure
            fan_rpm=self.fans.copy(),
            voltage_domain=[round(chain.voltage, 3) for chain in self.chains],
            
            # Fleet management metrics
            total_hash_rate=round(total_hashrate_gh, 3),
            accept_rate=round(accept_rate, 2),
            uptime=int(time.time() - self.start_time),
            firmware_version=f"{self.asic_model}_v2025.03.15",
            
            # Economic efficiency metrics
            joules_per_th=round(joules_per_th, 3),
            daily_power_cost=round(daily_power_cost, 2),
            estimated_revenue=round(estimated_revenue, 2)
        )

class ASICAPIHandler(BaseHTTPRequestHandler):
    """HTTP handler for professional ASIC API"""
    
    def __init__(self, *args, asic_simulator=None, **kwargs):
        self.asic_simulator = asic_simulator
        super().__init__(*args, **kwargs)
    
    def do_GET(self) -> None:
        """Handle GET requests for ASIC telemetry"""
        if self.path == "/api/stats":
            # Return professional telemetry
            telemetry = self.asic_simulator.get_professional_telemetry()
            response_data = asdict(telemetry)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response_data, indent=2).encode())
            
        elif self.path == "/api/summary":
            # Return summary for quick monitoring
            telemetry = self.asic_simulator.get_professional_telemetry()
            summary = {
                "model": self.asic_simulator.asic_model,
                "hashrate_gh": telemetry.total_hash_rate,
                "power_w": telemetry.power_real,
                "efficiency_jth": telemetry.joules_per_th,
                "temp_max": telemetry.asic_temp_max,
                "accept_rate": telemetry.accept_rate,
                "status": "optimal" if telemetry.joules_per_th < 0.5 else "degraded"
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(summary, indent=2).encode())
            
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args) -> None:
        """Suppress default logging"""
        pass

def create_asic_api_handler(simulator) -> None:
    """Create API handler with simulator instance"""
    def handler(*args, **kwargs) -> None:
        return ASICAPIHandler(*args, asic_simulator=simulator, **kwargs)
    return handler

def run_professional_asic_api(
    asic_model: str = "Antminer_L7",
    port: int = 4028):
)
    """Run professional ASIC API server"""
    simulator = ProfessionalASICSimulator(asic_model)
    handler = create_asic_api_handler(simulator)
    
    server = HTTPServer(('localhost', port), handler)
    
    logger.info(f"🔬 Professional ASIC API running on port {port}")
    logger.info(f"   Model: {asic_model}")
    logger.info(f"   Endpoints:")
    logger.info(f"     http://localhost:{port}/api/stats   - Full telemetry")
    logger.info(f"     http://localhost:{port}/api/summary - Quick summary")
    logger.info(f"   Engineering cliff-notes compliance: ✅")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Professional ASIC API stopped")
        server.shutdown()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Professional ASIC API Simulator")
    parser.add_argument("--model", default="Antminer_L7", 
                       choices=["Antminer_L7", "Antminer_S21_XP"],
                       help="ASIC model to simulate")
    parser.add_argument("--port", type=int, default=4028,
                       help="API port (default: 4028)")
    
    args = parser.parse_args()
    run_professional_asic_api(args.model, args.port)