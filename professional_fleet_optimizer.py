#!/usr/bin/env python3
"""
Professional Fleet Efficiency Optimizer
Direct implementation of the Go cliff-notes snippet: "Drop work from units below fleet median J/TH"

Key Engineering Insights:
- nonce_error is the early-fail predictor for ASIC degradation
- power_real from INA sensors provides true wall power consumption
- J/TH (Joules per Terahash) is the professional efficiency metric
- Fleet median J/TH is the benchmark for underperformer identification

Implements the exact logic from engineering cliff-notes for maximum profitability.
"""

import statistics
import requests
import logging
import json
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("professional_fleet_optimizer")

@dataclass
class AsicTelemetryProessional:
    """
    Professional ASIC telemetry exactly matching cliff-notes specification
    Direct translation of Go AsicTelemetry struct
    """
    ip: str                     # ASIC IP address
    power_real: float           # Watts from on-board INA sensor (true wall power)
    hash_rate: float            # GH/s total hashrate across all chains
    temp_max: float             # °C hottest diode reading
    nonce_error: float          # Fraction of bad nonces (early-fail predictor)
    
    # Calculated professional efficiency metric
    joules_per_th: float        # J/TH power efficiency (key fleet metric)
    
    # Additional professional monitoring
    diff_accepted: int          # Last share difficulty
    accept_rate: float          # Share acceptance percentage
    chain_rate: List[float]     # Per-hash-board GH/s
    fan_rpm: List[int]          # Fan RPMs (0 = failed fan)
    voltage_domain: List[float] # Per-board voltage
    online: bool                # Device accessibility status

class ProfessionalFleetOptimizer:
    """
    Professional fleet efficiency optimizer
    Direct implementation of engineering cliff-notes Go code snippet
    
    Core algorithm: \"Drop work from units below fleet median J/TH\"
    """
    
    def __init__(self, fleet_ips: List[str], api_port: int = 4028):
        self.fleet_ips = fleet_ips
        self.api_port = api_port
        self.fleet_telemetry: Dict[str, AsicTelemetryProessional] = {}
        
        # Professional spare pool configuration
        self.spare_pools = [
            "spare-pool-1.example.com:4444",
            "spare-pool-2.example.com:4444", 
            "maintenance-pool.example.com:4444"
        ]
        
        # Professional thresholds from engineering experience
        self.efficiency_threshold_multiplier = 1.10  # 10% above median triggers redirect
        self.nonce_error_threshold = 0.01            # 1% nonce error = early failure
        self.query_timeout = 5.0
        
    def query_professional_asic_telemetry(self, ip: str) -> Optional[AsicTelemetryProessional]:
        """
        Query single ASIC for professional-grade telemetry
        Extracts the exact fields specified in engineering cliff-notes
        """
        try:
            response = requests.get(f'http://{ip}:{self.api_port}/api/stats', timeout=self.query_timeout)
            response.raise_for_status()
            j = response.json()
            
            # Extract professional metrics per cliff-notes specification
            power_real = float(j.get('power_real', 0))  # True wall power from INA
            
            # Calculate total hashrate from chain_rate array
            chain_rates = j.get('chain_rate', [])
            if isinstance(chain_rates, list) and len(chain_rates) > 0:
                # Sum all chain rates and convert to GH/s
                total_hash_rate = sum(float(rate) for rate in chain_rates) / 1e9
                chain_rate_list = [float(rate) / 1e9 for rate in chain_rates]
            else:
                total_hash_rate = 0.0
                chain_rate_list = []
            
            # Professional efficiency calculation (cliff-notes key metric)
            joules_per_th = (power_real / (total_hash_rate * 1000)) if total_hash_rate > 0 else 999.0
            
            # Extract critical monitoring fields
            temp_max = float(j.get('asic_temp_max', j.get('temp_max', 0)) or 0)
            nonce_error = float(j.get('nonce_error', 0) or 0)  # Early-fail predictor
            diff_accepted = int(j.get('diff_accepted', 0) or 0)
            
            # Acceptance rate calculation
            accepted = int(j.get('accepted', 0) or 0)
            rejected = int(j.get('rejected', 0) or 0)
            accept_rate = (accepted / (accepted + rejected)) * 100 if (accepted + rejected) > 0 else 100
            
            # Infrastructure monitoring
            fan_rpms = j.get('fan_rpm', [])
            fan_rpm_list = [int(rpm) for rpm in fan_rpms] if isinstance(fan_rpms, list) else []
            
            voltage_domains = j.get('voltage_domain', [])
            voltage_list = [float(v) for v in voltage_domains] if isinstance(voltage_domains, list) else []
            
            return AsicTelemetryProessional(
                ip=ip,
                power_real=power_real,
                hash_rate=total_hash_rate,
                temp_max=temp_max,
                nonce_error=nonce_error,
                joules_per_th=joules_per_th,
                diff_accepted=diff_accepted,
                accept_rate=accept_rate,
                chain_rate=chain_rate_list,
                fan_rpm=fan_rpm_list,
                voltage_domain=voltage_list,
                online=True
            )
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"ASIC {ip} network error: {e}")
            # Return offline telemetry
            return AsicTelemetryProessional(
                ip=ip, power_real=0, hash_rate=0, temp_max=0, nonce_error=1.0,
                joules_per_th=999.0, diff_accepted=0, accept_rate=0,
                chain_rate=[], fan_rpm=[], voltage_domain=[], online=False
            )
        except Exception as e:
            logger.error(f"ASIC {ip} unexpected error: {e}")
            return None
    
    def calculate_median_jth(self, fleet: List[AsicTelemetryProessional]) -> float:
        """
        Calculate fleet median J/TH - core metric from cliff-notes
        Direct implementation of Go calculateMedianJTH() function
        """
        online_units = [unit for unit in fleet if unit.online and unit.joules_per_th < 900]
        
        if not online_units:
            logger.warning("No online units for median J/TH calculation")
            return 999.0
        
        jth_values = [unit.joules_per_th for unit in online_units]
        median_jth = statistics.median(jth_values)
        
        logger.info(f"Fleet median J/TH: {median_jth:.3f} ({len(online_units)} units)")
        return median_jth
    
    def identify_underperformers_professional(self, fleet: List[AsicTelemetryProessional], 
                                           median_jth: float) -> List[AsicTelemetryProessional]:
        """Identify units below fleet efficiency standard (cliff-notes algorithm)"""
        efficiency_threshold = median_jth * self.efficiency_threshold_multiplier
        underperformers = []
        
        for unit in fleet:
            if not unit.online:
                continue
                
            # Primary cliff-notes criterion: J/TH efficiency
            efficiency_fail = unit.joules_per_th > efficiency_threshold
            
            # Secondary professional criteria
            nonce_error_fail = unit.nonce_error > self.nonce_error_threshold
            temp_fail = unit.temp_max > 90  # Thermal protection
            accept_rate_fail = unit.accept_rate < 95  # Share quality
            fan_fail = any(rpm == 0 for rpm in unit.fan_rpm) if unit.fan_rpm else False
            
            if efficiency_fail or nonce_error_fail or temp_fail or accept_rate_fail or fan_fail:
                underperformers.append(unit)
                
                # Professional diagnostic logging
                reasons = []
                if efficiency_fail:
                    reasons.append(f"J/TH: {unit.joules_per_th:.3f} > {efficiency_threshold:.3f}")
                if nonce_error_fail:
                    reasons.append(f"Nonce error: {unit.nonce_error:.4f} (early-fail predictor)")
                if temp_fail:
                    reasons.append(f"Temperature: {unit.temp_max:.1f}°C")
                if accept_rate_fail:
                    reasons.append(f"Accept rate: {unit.accept_rate:.1f}%")
                if fan_fail:
                    failed_fans = [i for i, rpm in enumerate(unit.fan_rpm) if rpm == 0]
                    reasons.append(f"Failed fans: {failed_fans}")
                
                logger.info(f"⚠️  Underperformer {unit.ip}: {'; '.join(reasons)}")
        
        return underperformers
    
    def send_stratum_redirect_professional(self, unit_ip: str, spare_pool: str) -> bool:
        """Send Stratum redirect to underperforming unit - cliff-notes implementation"""
        try:
            # Professional Stratum redirect payload
            redirect_payload = {
                "command": "pools",
                "parameter": f"addpool|{spare_pool}|worker|password"
            }
            
            response = requests.post(
                f'http://{unit_ip}:{self.api_port}/api/command',
                json=redirect_payload,
                timeout=self.query_timeout
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Redirected {unit_ip} to spare pool {spare_pool}")
                return True
            else:
                logger.error(f"❌ Redirect failed {unit_ip}: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Redirect error {unit_ip}: {e}")
            return False
    
    def optimize_fleet_efficiency_professional(self) -> Dict[str, any]:
        """Main fleet optimization - exact implementation of cliff-notes Go code"""
        logger.info(f"🔬 Starting professional fleet efficiency optimization")
        logger.info(f"   Fleet size: {len(self.fleet_ips)} units")
        logger.info(f"   Algorithm: Drop work from units below fleet median J/TH")
        
        # Step 1: Query all units concurrently for efficiency
        fleet_telemetry = []
        
        with ThreadPoolExecutor(max_workers=min(len(self.fleet_ips), 20)) as executor:
            future_to_ip = {executor.submit(self.query_professional_asic_telemetry, ip): ip 
                           for ip in self.fleet_ips}
            
            for future in as_completed(future_to_ip):
                ip = future_to_ip[future]
                try:
                    result = future.result()
                    if result is not None:
                        fleet_telemetry.append(result)
                        self.fleet_telemetry[ip] = result
                except Exception as e:
                    logger.error(f"Fleet query error for {ip}: {e}")
        
        if not fleet_telemetry:
            logger.error("❌ No telemetry data available")
            return {"success": False, "reason": "No telemetry"}
        
        # Step 2: Calculate fleet median J/TH (cliff-notes core algorithm)
        median_jth = self.calculate_median_jth(fleet_telemetry)
        
        # Step 3: Identify units below fleet median J/TH
        underperformers = self.identify_underperformers_professional(fleet_telemetry, median_jth)
        
        # Step 4: Redirect underperformers to spare pools
        redirected_count = 0
        for unit in underperformers:
            spare_pool = self.spare_pools[redirected_count % len(self.spare_pools)]
            if self.send_stratum_redirect_professional(unit.ip, spare_pool):
                redirected_count += 1
        
        # Professional optimization results
        online_units = [u for u in fleet_telemetry if u.online]
        total_hashrate = sum(u.hash_rate for u in online_units)
        total_power = sum(u.power_real for u in online_units)
        fleet_efficiency = (total_power / (total_hashrate * 1000)) if total_hashrate > 0 else 999.0
        
        optimization_result = {
            "success": True,
            "algorithm": "fleet_median_jth_optimization",
            "fleet_metrics": {
                "total_units": len(fleet_telemetry),
                "online_units": len(online_units),
                "median_jth": median_jth,
                "fleet_efficiency_jth": fleet_efficiency,
                "total_hashrate_gh": total_hashrate,
                "total_power_w": total_power,
                "efficiency_threshold": median_jth * self.efficiency_threshold_multiplier
            },
            "optimization_actions": {
                "underperformers_found": len(underperformers),
                "units_redirected": redirected_count,
                "redirection_success_rate": (redirected_count / len(underperformers)) * 100 if underperformers else 100
            }
        }
        
        # Professional summary logging
        logger.info(f"📊 Fleet Optimization Results:")
        logger.info(f"   Online units: {len(online_units)}/{len(fleet_telemetry)}")
        logger.info(f"   Fleet median J/TH: {median_jth:.3f}")
        logger.info(f"   Fleet efficiency: {fleet_efficiency:.3f} J/TH")
        logger.info(f"   Total hashrate: {total_hashrate:.2f} GH/s")
        logger.info(f"   Total power: {total_power:.0f} W")
        logger.info(f"   Underperformers: {len(underperformers)} found, {redirected_count} redirected")
        logger.info(f"   Efficiency gain: {((median_jth - fleet_efficiency) / median_jth * 100):.1f}%")
        
        return optimization_result
    
    def get_professional_fleet_summary(self) -> Dict[str, any]:
        """Professional fleet status summary for monitoring dashboards"""
        if not self.fleet_telemetry:
            # Trigger fresh telemetry collection
            self.optimize_fleet_efficiency_professional()
        
        online_units = [u for u in self.fleet_telemetry.values() if u.online]
        
        if not online_units:
            return {"status": "no_online_units", "timestamp": time.time()}
        
        # Professional metrics calculation
        jth_values = [u.joules_per_th for u in online_units if u.joules_per_th < 900]
        median_jth = statistics.median(jth_values) if jth_values else 999.0
        
        # Health categorization based on efficiency relative to fleet median
        health_categories = {
            "optimal": [],      # Below median J/TH
            "acceptable": [],   # Within 10% of median
            "degraded": [],     # 10-50% above median
            "critical": [],     # >50% above median
            "offline": []       # Not responding
        }
        
        for unit in self.fleet_telemetry.values():
            if not unit.online:
                health_categories["offline"].append(unit.ip)
            elif unit.joules_per_th < median_jth:
                health_categories["optimal"].append(unit.ip)
            elif unit.joules_per_th < median_jth * 1.1:
                health_categories["acceptable"].append(unit.ip)
            elif unit.joules_per_th < median_jth * 1.5:
                health_categories["degraded"].append(unit.ip)
            else:
                health_categories["critical"].append(unit.ip)
        
        return {
            "fleet_health": {k: len(v) for k, v in health_categories.items()},
            "health_details": health_categories,
            "efficiency_metrics": {
                "median_jth": median_jth,
                "total_hashrate_gh": sum(u.hash_rate for u in online_units),
                "total_power_w": sum(u.power_real for u in online_units),
                "online_ratio": len(online_units) / len(self.fleet_telemetry) * 100
            },
            "timestamp": time.time()
        }

# Professional CLI interface matching cliff-notes workflow
def main_professional_fleet_optimizer():
    """Professional fleet management CLI"""
    import argparse
    import time
    
    parser = argparse.ArgumentParser(
        description="Professional ASIC Fleet Efficiency Optimizer",
        epilog="Implements engineering cliff-notes: 'Drop work from units below fleet median J/TH'"

    )
    
    parser.add_argument("--fleet-ips", nargs="+", required=True,
                       help="List of ASIC IP addresses for fleet management")
    parser.add_argument("--api-port", type=int, default=4028,
                       help="ASIC API port (default: 4028)")
    parser.add_argument("--optimize", action="store_true",
                       help="Run professional fleet efficiency optimization")
    parser.add_argument("--status", action="store_true",
                       help="Show professional fleet status summary")
    parser.add_argument("--continuous", type=int, metavar="INTERVAL",
                       help="Run continuously with specified interval (seconds)")
    parser.add_argument("--json-output", action="store_true",
                       help="Output results in JSON format")
    
    args = parser.parse_args()
    
    # Initialize professional fleet optimizer
    fleet_optimizer = ProfessionalFleetOptimizer(args.fleet_ips, args.api_port)
    
    logger.info(f"🔬 Professional Fleet Optimizer initialized")
    logger.info(f"   Fleet IPs: {len(args.fleet_ips)} units")
    logger.info(f"   API Port: {args.api_port}")
    logger.info(f"   Algorithm: Median J/TH efficiency optimization")
    
    if args.continuous:
        logger.info(f"Starting continuous optimization (interval: {args.continuous}s)")
        try:
            while True:
                if args.optimize:
                    result = fleet_optimizer.optimize_fleet_efficiency_professional()
                    if args.json_output:
                        print(json.dumps(result, indent=2))
                    else:
                        print(f"Optimization: {result['optimization_actions']['units_redirected']}/{result['optimization_actions']['underperformers_found']} units redirected")
                
                if args.status:
                    status = fleet_optimizer.get_professional_fleet_summary()
                    if args.json_output:
                        print(json.dumps(status, indent=2))
                    else:
                        print(f"Fleet health: {status['fleet_health']}")
                
                time.sleep(args.continuous)
        except KeyboardInterrupt:
            logger.info("Professional fleet optimization stopped by user")
    else:
        if args.optimize:
            result = fleet_optimizer.optimize_fleet_efficiency_professional()
            if args.json_output:
                print(json.dumps(result, indent=2))
            else:
                print(f"Professional fleet optimization completed: {result['optimization_actions']['units_redirected']} units redirected")
        
        if args.status:
            status = fleet_optimizer.get_professional_fleet_summary()
            if args.json_output:
                print(json.dumps(status, indent=2))
            else:
                print(f"Professional fleet status: {status['fleet_health']}")

if __name__ == "__main__":
    main_professional_fleet_optimizer()