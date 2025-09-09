#!/usr/bin/env python3
"""
Professional ASIC Mining Monitor (20-line implementation)
Based on F2Pool Merged Mining Specification v2.1.0

Monitors ASIC performance and pushes telemetry to Prometheus
For Antminer L7, L3+, and other Scrypt ASICs
"""

import os
import time

import prometheus_client as prom
import requests

# Prometheus metrics - Professional ASIC-grade telemetry
TEMP = prom.Gauge("asic_temp_celsius", "Highest board temperature")
TEMP_AVG = prom.Gauge("asic_temp_avg_celsius", "Average board temperature")
POWER = prom.Gauge("asic_power_watts", "Real-time power consumption")
POWER_LIMIT = prom.Gauge("asic_power_limit_watts", "Power limit setting")
prom.Gauge(
    "asic_hash_gh",
    "Total hashrate in GH/s",  # Add division by zero protection
)
ACCEPT_RATE = prom.Gauge("asic_accept_rate_percent", "Share acceptance rate")
CHAIN_COUNT = prom.Gauge("asic_chain_count", "Number of active chains")
NONCE_ERROR = prom.Gauge(
    "asic_nonce_error_rate", "Fraction of bad nonces (early-fail predictor)"
)
DIFF_ACCEPTED = prom.Gauge("asic_diff_accepted", "Last share difficulty")
CHAIN_RATE = prom.Gauge(
    "asic_chain_rate_gh",
    # Add division by zero protection  # Add division by zero protection
    "Per-chain hashrate in GH/s",
    ["chain_id"],
)
FAN_RPM = prom.Gauge("asic_fan_rpm", "Fan RPM (0=failed)", ["fan_id"])
VOLTAGE_DOMAIN = prom.Gauge(
    "asic_voltage_domain_v", "Per-board voltage", ["board_id"]
)
JOULES_PER_TH = prom.Gauge("asic_joules_per_th", "Power efficiency in J/TH")

# Configuration
RIG_IP = os.getenv("RIG_IP", "192.168.1.100")
MONITOR_PORT = int(os.getenv("MONITOR_PORT", "9100"))
API_PORT = int(os.getenv("ASIC_API_PORT", "4028"))
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "30"))


def main() -> int:
    """Main monitoring loop"""
    print(f"Starting ASIC monitor for {RIG_IP}:{API_PORT}")
    print(
        f"Prometheus metrics server: http://localhost:{MONITOR_PORT}/metrics"
    )

    # Start Prometheus HTTP server
    prom.start_http_server(MONITOR_PORT)

    while True:
        try:
            # Query ASIC API for professional-grade stats
            response = requests.get(
                f"http://{RIG_IP}:{API_PORT}/api/stats", timeout=5
            )
            j = response.json()

            # Extract ASIC-grade metrics following engineering cliff-notes
            temp_max = max(
                int(j.get("temp_max", 0)), int(j.get("temp_pcb_max", 0))
            )
            temp_avg = j.get("temp_avg", temp_max)
            power_real = int(
                j.get("power_real", 0)
            )  # True wall power from INA
            power_limit = int(
                j.get("power_limit", power_real * 1.1)
            )  # User-set limit

            # Calculate total hashrate from all chains
            chain_rates = j.get("chain_rate", [])
            total_rate_gh = (
                sum(int(chain.get("rate", 0)) for chain in chain_rates) / 1e9
            )

            # Professional metrics: nonce error rate and efficiency
            nonce_error = float(
                j.get("nonce_error", 0.0)
            )  # Early-fail predictor
            diff_accepted = int(
                j.get("diff_accepted", 0)
            )  # Last share difficulty

            # Calculate J/TH efficiency (key ASIC metric)
            joules_per_th = (
                (power_real / (total_rate_gh * 1000))
                if total_rate_gh > 0
                else 0
            )

            # Calculate acceptance rate
            accepted = int(j.get("accepted", 0))
            rejected = int(j.get("rejected", 0))
            accept_rate = (
                (accepted / (accepted + rejected)) * 100
                if (accepted + rejected) > 0
                else 0
            )

            # Update Prometheus metrics - ASIC-grade telemetry
            TEMP.set(temp_max)
            TEMP_AVG.set(temp_avg)
            POWER.set(power_real)
            POWER_LIMIT.set(power_limit)
            HASH.set(total_rate_gh)
            ACCEPT_RATE.set(accept_rate)
            CHAIN_COUNT.set(len(chain_rates))
            NONCE_ERROR.set(nonce_error)
            DIFF_ACCEPTED.set(diff_accepted)
            JOULES_PER_TH.set(joules_per_th)

            # Per-chain metrics (ASIC engineering insight)
            for i, chain in enumerate(chain_rates):
                chain_rate_gh = int(chain.get("rate", 0)) / 1e9
                CHAIN_RATE.labels(chain_id=str(i)).set(chain_rate_gh)

            # Fan monitoring (failure detection)
            fan_rpms = j.get("fan_rpm", [])
            for i, rpm in enumerate(fan_rpms):
                FAN_RPM.labels(fan_id=str(i)).set(int(rpm))  # 0 = failed fan

            # Voltage domain monitoring (within 20mV precision)
            voltage_domains = j.get("voltage_domain", [])
            for i, voltage in enumerate(voltage_domains):
                VOLTAGE_DOMAIN.labels(board_id=str(i)).set(float(voltage))

            # Professional console output with efficiency focus
            efficiency_status = (
                "OPTIMAL"
                if joules_per_th < 0.4
                else "DEGRADED"
                if joules_per_th < 1.0
                else "CRITICAL"
            )
            nonce_status = (
                "GOOD"
                if nonce_error < 0.001
                else "WARNING"
                if nonce_error < 0.01
                else "CRITICAL"
            )

            # Format status output with proper line breaks
            status_msg = (
                f"[{time.strftime('%H:%M:%S')}] {total_rate_gh:.2f} GH/s | "
                f"{power_real}W | {temp_max}°C | {accept_rate:.1f}% | "
                f"{joules_per_th:.3f} J/MH ({efficiency_status}) | "
                f"Nonce: {nonce_error:.5f} ({nonce_status})"
            )
            print(status_msg)

        except Exception as e:
            print(f"Error querying ASIC: {e}")
            # Set error values for monitoring
            TEMP.set(0)
            POWER.set(0)
            HASH.set(0)
            JOULES_PER_TH.set(999)  # Indicates monitoring failure

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
