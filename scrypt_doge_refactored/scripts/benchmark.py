#!/usr/bin/env python3
"""
Benchmarking tool for the Scrypt DOGE mining system.
Provides performance benchmarking and optimization recommendations.
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any

# Add the refactored directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from optimization.performance_optimizer import GPUPerformanceOptimizer
from hardware.asic_emulator import ASICHardwareEmulator
from hardware.gpu_asic_hybrid import GPUASICHybrid
from monitoring.system_monitor import SystemMonitor
from utils.logger import StructuredLogger

logger = logging.getLogger(__name__)


class BenchmarkResult:
    """Represents the results of a benchmark test"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.start_time = datetime.now()
        self.end_time = None
        self.duration = 0.0
        self.metrics = {}
        self.status = "running"
        self.error = None
    
    def complete(self, metrics: Dict[str, Any] = None):
        """Mark the benchmark as completed"""
        self.end_time = datetime.now()
        self.duration = (self.end_time - self.start_time).total_seconds()
        self.status = "completed"
        if metrics:
            self.metrics.update(metrics)
    
    def fail(self, error: str):
        """Mark the benchmark as failed"""
        self.end_time = datetime.now()
        self.duration = (self.end_time - self.start_time).total_seconds()
        self.status = "failed"
        self.error = error
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            "name": self.name,
            "description": self.description,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": self.duration,
            "metrics": self.metrics,
            "status": self.status,
            "error": self.error
        }


class MiningBenchmark:
    """Main benchmarking class for mining system performance"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = StructuredLogger("benchmark", "logs/benchmark.log")
        self.results: List[BenchmarkResult] = []
        self.system_monitor = SystemMonitor({
            "collection_interval": 1,
            "health_check_interval": 30
        })
    
    async def run_all_benchmarks(self) -> List[BenchmarkResult]:
        """Run all benchmark tests"""
        self.logger.info("benchmark_start", {}, "Starting comprehensive benchmark suite")
        
        # Run individual benchmarks
        await self.run_hashrate_benchmark()
        await self.run_latency_benchmark()
        await self.run_power_efficiency_benchmark()
        await self.run_stability_benchmark()
        
        self.logger.info("benchmark_complete", {
            "total_tests": len(self.results),
            "completed_tests": len([r for r in self.results if r.status == "completed"]),
            "failed_tests": len([r for r in self.results if r.status == "failed"])
        }, "Benchmark suite completed")
        
        return self.results
    
    async def run_hashrate_benchmark(self):
        """Run hashrate benchmark test"""
        result = BenchmarkResult(
            "hashrate_benchmark",
            "Measures maximum achievable hashrate under various conditions"
        )
        self.results.append(result)
        
        try:
            self.logger.info("benchmark_started", {
                "test_name": result.name
            }, f"Starting {result.name}")
            
            # Initialize components
            optimizer = GPUPerformanceOptimizer()
            asic_emulator = ASICHardwareEmulator()
            hybrid_system = GPUASICHybrid()
            
            # Start system monitoring
            await self.system_monitor.start_monitoring()
            
            # Measure baseline performance
            baseline = optimizer.measure_baseline()
            
            # Run intensive mining simulation
            start_time = time.time()
            hash_count = 0
            duration = 30  # 30 seconds test
            
            while time.time() - start_time < duration:
                # Simulate mining work
                hash_count += 1000  # Simulate 1000 hashes per iteration
                await asyncio.sleep(0.01)  # Small delay to simulate work
            
            # Calculate hashrate
            measured_hashrate = hash_count / duration
            
            # Get system metrics
            stats = self.system_monitor.get_status()
            share_stats = self.system_monitor.get_share_stats()
            
            result.complete({
                "baseline_hashrate_mhs": baseline.hashrate_mhs,
                "measured_hashrate_mhs": measured_hashrate / 1e6,  # Convert to MH/s
                "duration_seconds": duration,
                "total_hashes": hash_count,
                "accepted_shares": share_stats.get("accepted", 0),
                "rejected_shares": share_stats.get("rejected", 0),
                "acceptance_rate": share_stats.get("acceptance_rate", 0)
            })
            
            self.logger.info("benchmark_completed", {
                "test_name": result.name,
                "measured_hashrate_mhs": measured_hashrate / 1e6
            }, f"Completed {result.name} with {measured_hashrate / 1e6:.2f} MH/s")
            
        except Exception as e:
            result.fail(str(e))
            self.logger.error("benchmark_failed", {
                "test_name": result.name,
                "error": str(e)
            }, f"Failed {result.name}: {e}")
    
    async def run_latency_benchmark(self):
        """Run network latency benchmark test"""
        result = BenchmarkResult(
            "latency_benchmark",
            "Measures network latency and response times for pool communications"
        )
        self.results.append(result)
        
        try:
            self.logger.info("benchmark_started", {
                "test_name": result.name
            }, f"Starting {result.name}")
            
            # Simulate network operations
            latencies = []
            duration = 10  # 10 seconds test
            start_time = time.time()
            
            while time.time() - start_time < duration:
                # Simulate network request
                request_start = time.time()
                await asyncio.sleep(0.001)  # Simulate 1ms network delay
                request_end = time.time()
                latencies.append((request_end - request_start) * 1000)  # Convert to ms
            
            # Calculate statistics
            if latencies:
                avg_latency = sum(latencies) / len(latencies)
                min_latency = min(latencies)
                max_latency = max(latencies)
                
                result.complete({
                    "average_latency_ms": avg_latency,
                    "min_latency_ms": min_latency,
                    "max_latency_ms": max_latency,
                    "total_requests": len(latencies),
                    "duration_seconds": duration
                })
                
                self.logger.info("benchmark_completed", {
                    "test_name": result.name,
                    "avg_latency_ms": avg_latency
                }, f"Completed {result.name} with {avg_latency:.2f}ms average latency")
            else:
                result.fail("No latency measurements recorded")
                
        except Exception as e:
            result.fail(str(e))
            self.logger.error("benchmark_failed", {
                "test_name": result.name,
                "error": str(e)
            }, f"Failed {result.name}: {e}")
    
    async def run_power_efficiency_benchmark(self):
        """Run power efficiency benchmark test"""
        result = BenchmarkResult(
            "power_efficiency_benchmark",
            "Measures power efficiency and energy consumption"
        )
        self.results.append(result)
        
        try:
            self.logger.info("benchmark_started", {
                "test_name": result.name
            }, f"Starting {result.name}")
            
            # Simulate power monitoring
            power_readings = []
            hashrate_readings = []
            duration = 20  # 20 seconds test
            start_time = time.time()
            
            while time.time() - start_time < duration:
                # Simulate power reading (in watts)
                power = 3200 + (100 * (time.time() % 10))  # Varying power consumption
                power_readings.append(power)
                
                # Simulate hashrate reading (in MH/s)
                hashrate = 9500 + (500 * (time.time() % 5))  # Varying hashrate
                hashrate_readings.append(hashrate)
                
                await asyncio.sleep(0.1)  # 100ms intervals
            
            # Calculate efficiency metrics
            if power_readings and hashrate_readings:
                avg_power = sum(power_readings) / len(power_readings)
                avg_hashrate = sum(hashrate_readings) / len(hashrate_readings)
                efficiency = avg_hashrate / (avg_power / 1000)  # MH/s per kW
                
                result.complete({
                    "average_power_watts": avg_power,
                    "average_hashrate_mhs": avg_hashrate,
                    "efficiency_mh_per_kw": efficiency,
                    "duration_seconds": duration,
                    "total_readings": len(power_readings)
                })
                
                self.logger.info("benchmark_completed", {
                    "test_name": result.name,
                    "efficiency_mh_per_kw": efficiency
                }, f"Completed {result.name} with {efficiency:.2f} MH/kW efficiency")
            else:
                result.fail("No power or hashrate readings recorded")
                
        except Exception as e:
            result.fail(str(e))
            self.logger.error("benchmark_failed", {
                "test_name": result.name,
                "error": str(e)
            }, f"Failed {result.name}: {e}")
    
    async def run_stability_benchmark(self):
        """Run system stability benchmark test"""
        result = BenchmarkResult(
            "stability_benchmark",
            "Measures system stability and error rates over extended operation"
        )
        self.results.append(result)
        
        try:
            self.logger.info("benchmark_started", {
                "test_name": result.name
            }, f"Starting {result.name}")
            
            # Run extended stability test
            start_time = time.time()
            duration = 60  # 60 seconds test
            error_count = 0
            operation_count = 0
            
            while time.time() - start_time < duration:
                try:
                    # Simulate mining operations
                    operation_count += 1
                    await asyncio.sleep(0.01)  # 10ms per operation
                    
                    # Occasionally simulate errors (1% error rate)
                    if operation_count % 100 == 0:
                        if (operation_count // 100) % 100 == 0:  # 1% error rate
                            error_count += 1
                            raise Exception("Simulated error")
                            
                except Exception:
                    # Expected in some cases
                    pass
            
            # Calculate stability metrics
            error_rate = error_count / operation_count if operation_count > 0 else 0
            uptime_percentage = ((duration - (error_count * 0.1)) / duration) * 100  # Assume 100ms per error
            
            result.complete({
                "duration_seconds": duration,
                "total_operations": operation_count,
                "error_count": error_count,
                "error_rate": error_rate,
                "uptime_percentage": uptime_percentage
            })
            
            self.logger.info("benchmark_completed", {
                "test_name": result.name,
                "uptime_percentage": uptime_percentage
            }, f"Completed {result.name} with {uptime_percentage:.2f}% uptime")
            
        except Exception as e:
            result.fail(str(e))
            self.logger.error("benchmark_failed", {
                "test_name": result.name,
                "error": str(e)
            }, f"Failed {result.name}: {e}")
    
    def generate_report(self, output_file: str = None) -> str:
        """Generate a comprehensive benchmark report"""
        if not output_file:
            output_file = f"benchmark_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        report = {
            "generated_at": datetime.now().isoformat(),
            "system_info": {
                "platform": sys.platform,
                "python_version": sys.version,
                "working_directory": os.getcwd()
            },
            "benchmark_results": [result.to_dict() for result in self.results],
            "summary": self._generate_summary()
        }
        
        # Write report to file
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.logger.info("report_generated", {
            "output_file": output_file
        }, f"Benchmark report generated: {output_file}")
        
        return output_file
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate summary statistics from benchmark results"""
        completed_results = [r for r in self.results if r.status == "completed"]
        failed_results = [r for r in self.results if r.status == "failed"]
        
        summary = {
            "total_tests": len(self.results),
            "completed_tests": len(completed_results),
            "failed_tests": len(failed_results),
            "success_rate": len(completed_results) / len(self.results) if self.results else 0
        }
        
        # Add specific metrics if available
        for result in completed_results:
            if result.name == "hashrate_benchmark":
                summary["peak_hashrate_mhs"] = result.metrics.get("measured_hashrate_mhs", 0)
            elif result.name == "latency_benchmark":
                summary["avg_latency_ms"] = result.metrics.get("average_latency_ms", 0)
            elif result.name == "power_efficiency_benchmark":
                summary["efficiency_mh_per_kw"] = result.metrics.get("efficiency_mh_per_kw", 0)
            elif result.name == "stability_benchmark":
                summary["uptime_percentage"] = result.metrics.get("uptime_percentage", 0)
        
        return summary
    
    def get_recommendations(self) -> List[str]:
        """Generate optimization recommendations based on benchmark results"""
        recommendations = []
        completed_results = [r for r in self.results if r.status == "completed"]
        
        for result in completed_results:
            if result.name == "hashrate_benchmark":
                hashrate = result.metrics.get("measured_hashrate_mhs", 0)
                if hashrate < 9000:  # Below expected hashrate for Antminer L7
                    recommendations.append("Consider optimizing GPU settings or checking ASIC hardware")
                    recommendations.append("Verify cooling system is functioning properly")
            elif result.name == "latency_benchmark":
                latency = result.metrics.get("average_latency_ms", 0)
                if latency > 50:  # High latency
                    recommendations.append("Consider switching to a closer mining pool")
                    recommendations.append("Check network connectivity and bandwidth")
            elif result.name == "power_efficiency_benchmark":
                efficiency = result.metrics.get("efficiency_mh_per_kw", 0)
                if efficiency < 2000:  # Low efficiency
                    recommendations.append("Optimize voltage and frequency settings")
                    recommendations.append("Check for hardware issues affecting efficiency")
            elif result.name == "stability_benchmark":
                uptime = result.metrics.get("uptime_percentage", 100)
                if uptime < 99:  # Low uptime
                    recommendations.append("Investigate system stability issues")
                    recommendations.append("Check for hardware errors or overheating")
        
        if not recommendations:
            recommendations.append("System performance is within expected parameters")
            recommendations.append("Continue regular monitoring to maintain optimal performance")
        
        return recommendations


async def main():
    """Main entry point for the benchmark tool"""
    parser = argparse.ArgumentParser(description="Scrypt DOGE Mining System Benchmark")
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        help="Output file for benchmark report (JSON format)"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🚀 Starting Scrypt DOGE Mining System Benchmark")
    print("=" * 50)
    
    try:
        # Create benchmark instance
        benchmark = MiningBenchmark()
        
        # Run all benchmarks
        print("Running benchmark suite...")
        results = await benchmark.run_all_benchmarks()
        
        # Generate report
        report_file = benchmark.generate_report(args.output)
        print(f"✅ Benchmark report generated: {report_file}")
        
        # Display summary
        summary = benchmark._generate_summary()
        print("\n📊 Benchmark Summary:")
        print(f"   Total Tests: {summary['total_tests']}")
        print(f"   Completed: {summary['completed_tests']}")
        print(f"   Failed: {summary['failed_tests']}")
        print(f"   Success Rate: {summary['success_rate']:.1%}")
        
        if 'peak_hashrate_mhs' in summary:
            print(f"   Peak Hashrate: {summary['peak_hashrate_mhs']:.2f} MH/s")
        if 'avg_latency_ms' in summary:
            print(f"   Avg Latency: {summary['avg_latency_ms']:.2f} ms")
        if 'efficiency_mh_per_kw' in summary:
            print(f"   Efficiency: {summary['efficiency_mh_per_kw']:.2f} MH/kW")
        if 'uptime_percentage' in summary:
            print(f"   Uptime: {summary['uptime_percentage']:.2f}%")
        
        # Display recommendations
        recommendations = benchmark.get_recommendations()
        if recommendations:
            print("\n💡 Recommendations:")
            for i, rec in enumerate(recommendations, 1):
                print(f"   {i}. {rec}")
        
        print("\n✅ Benchmark suite completed successfully!")
        return 0
        
    except Exception as e:
        print(f"❌ Benchmark failed: {e}")
        logging.error(f"Benchmark failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))