"""
Generate High-Resolution Engineering Publication Plots for K15B Telemetry
===========================================================================
Generates 300 DPI analytical charts:
1. K15B Dyno Torque & Power vs RPM (138 Nm @ 4400 RPM, 77 kW @ 6000 RPM)
2. Cold-Start Thermal Warmup & Fast-Idle Flare
3. SHVS Dual-Battery Energy Management (Torque Assist & Regen Braking)

Author: RATHLAVATH NAVEEN (rathlavathnaveen90@gmail.com)
Copyright (c) 2026 RATHLAVATH NAVEEN. All Rights Reserved.
"""

import os
import sys
import math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Ensure parent directory is on sys.path to import k15b_engine_model
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from k15b_engine_model import K15BPowertrainPlant

def generate_plots(output_dir):
    os.makedirs(output_dir, exist_ok=True)
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.size'] = 10
    plt.rcParams['axes.edgecolor'] = '#333333'
    plt.rcParams['axes.linewidth'] = 1.0

    plant = K15BPowertrainPlant(ambient_temp_c=25.0)

    # -------------------------------------------------------------------------
    # Plot 1: K15B Dynamometer Performance Curves
    # -------------------------------------------------------------------------
    rpms = np.linspace(800, 6500, 300)
    torques = [plant.get_k15b_wide_open_throttle_torque(r) for r in rpms]
    powers_kw = [(t * 2.0 * math.pi * r) / 60000.0 for t, r in zip(torques, rpms)]
    powers_bhp = [p * 1.34102 for p in powers_kw]

    fig, ax1 = plt.subplots(figsize=(9, 5.5), dpi=300)
    color_torque = '#C0392B'  # Deep Red
    color_power = '#2980B9'   # Blue

    ax1.plot(rpms, torques, color=color_torque, linewidth=2.5, label='Brake Torque (Nm)')
    ax1.set_xlabel('Engine Speed (RPM)', fontweight='bold')
    ax1.set_ylabel('Brake Torque (Nm)', color=color_torque, fontweight='bold')
    ax1.tick_params(axis='y', labelcolor=color_torque)
    ax1.set_ylim(70, 155)
    ax1.grid(True, linestyle='--', alpha=0.5)

    # Annotate Peak Torque
    peak_t_idx = np.argmax(torques)
    peak_t_rpm = rpms[peak_t_idx]
    peak_t_val = torques[peak_t_idx]
    ax1.scatter([peak_t_rpm], [peak_t_val], color=color_torque, s=70, zorder=5)
    ax1.annotate(f'Peak Torque: {peak_t_val:.1f} Nm\n@ {peak_t_rpm:.0f} RPM',
                 xy=(peak_t_rpm, peak_t_val), xytext=(peak_t_rpm - 1400, peak_t_val + 6),
                 arrowprops=dict(facecolor=color_torque, shrink=0.08, width=1.5, headwidth=6),
                 fontweight='bold', fontsize=9, bbox=dict(boxstyle="round,pad=0.3", fc="#FDEDEC", ec=color_torque))

    # Right Axis: Power
    ax2 = ax1.twinx()
    ax2.plot(rpms, powers_bhp, color=color_power, linewidth=2.5, linestyle='-', label='Brake Power (bhp)')
    ax2.set_ylabel('Brake Power (bhp / kW)', color=color_power, fontweight='bold')
    ax2.tick_params(axis='y', labelcolor=color_power)
    ax2.set_ylim(0, 120)

    # Annotate Peak Power
    peak_p_idx = np.argmax(powers_bhp)
    peak_p_rpm = rpms[peak_p_idx]
    peak_p_val = powers_bhp[peak_p_idx]
    peak_p_kw = powers_kw[peak_p_idx]
    ax2.scatter([peak_p_rpm], [peak_p_val], color=color_power, s=70, zorder=5)
    ax2.annotate(f'Peak Power: {peak_p_val:.1f} bhp ({peak_p_kw:.1f} kW)\n@ {peak_p_rpm:.0f} RPM',
                 xy=(peak_p_rpm, peak_p_val), xytext=(peak_p_rpm - 2200, peak_p_val - 16),
                 arrowprops=dict(facecolor=color_power, shrink=0.08, width=1.5, headwidth=6),
                 fontweight='bold', fontsize=9, bbox=dict(boxstyle="round,pad=0.3", fc="#EBF5FB", ec=color_power))

    plt.title('Maruti Suzuki K15B 1.5L DOHC VVT Dynamometer Calibration\nWide-Open-Throttle (WOT) Torque & Power vs. Engine RPM',
              fontweight='bold', fontsize=12, pad=12)
    plt.tight_layout()
    p1_path = os.path.join(output_dir, "k15b_dynamometer_torque_power_curves.png")
    plt.savefig(p1_path, dpi=300)
    plt.close()
    print(f"Saved: {p1_path}")

    # -------------------------------------------------------------------------
    # Plot 2: Cold-Start Thermal Warmup & Fast Idle Flare
    # -------------------------------------------------------------------------
    plant_cold = K15BPowertrainPlant(ambient_temp_c=20.0)
    time_sim = []
    ect_sim = []
    rpm_sim = []
    fuel_sim = []

    dt = 0.5
    for step_i in range(360):  # 180 seconds (3 minutes)
        t_sec = step_i * dt
        # Light idle / warmup
        state = plant_cold.step(dt=dt, throttle_demand_pct=0.0)
        time_sim.append(t_sec)
        ect_sim.append(state['CoolantTemperature'])
        rpm_sim.append(state['EngineSpeed'])
        fuel_sim.append(state['FuelFlowRate'])

    fig, ax1 = plt.subplots(figsize=(9, 5), dpi=300)
    color_ect = '#D35400'
    color_rpm = '#27AE60'

    ax1.plot(time_sim, ect_sim, color=color_ect, linewidth=2.5, label='Coolant Temperature (°C)')
    ax1.axhline(88.0, color=color_ect, linestyle='--', alpha=0.7, label='Thermostat Opening (88°C)')
    ax1.set_xlabel('Time Elapsed (seconds)', fontweight='bold')
    ax1.set_ylabel('Engine Coolant Temperature (°C)', color=color_ect, fontweight='bold')
    ax1.tick_params(axis='y', labelcolor=color_ect)
    ax1.set_ylim(15, 100)
    ax1.grid(True, linestyle='--', alpha=0.5)

    ax2 = ax1.twinx()
    ax2.plot(time_sim, rpm_sim, color=color_rpm, linewidth=2.2, label='Engine Idle Speed (RPM)')
    ax2.set_ylabel('Idle Engine Speed (RPM)', color=color_rpm, fontweight='bold')
    ax2.tick_params(axis='y', labelcolor=color_rpm)
    ax2.set_ylim(600, 1400)

    plt.title('K15B Cold-Start Thermal Transient & Automatic Fast-Idle Decay\n1,250 RPM Cold Flare -> 750 RPM Warm Idle Stabilization',
              fontweight='bold', fontsize=12, pad=12)
    plt.tight_layout()
    p2_path = os.path.join(output_dir, "k15b_coldstart_thermal_idle_flare.png")
    plt.savefig(p2_path, dpi=300)
    plt.close()
    print(f"Saved: {p2_path}")

    # -------------------------------------------------------------------------
    # Plot 3: SHVS Smart Hybrid Energy Management Cycle
    # -------------------------------------------------------------------------
    plant_hyb = K15BPowertrainPlant(ambient_temp_c=88.0)
    time_hyb = []
    speed_hyb = []
    isg_torq_hyb = []
    soc_hyb = []
    mode_hyb = []

    dt = 0.1
    for step_i in range(500):  # 50 seconds
        t_sec = step_i * dt
        if t_sec < 10.0:
            th = 15.0; brk = 0.0
        elif t_sec < 25.0:
            th = 85.0; brk = 0.0  # Torque Assist event!
        elif t_sec < 38.0:
            th = 0.0; brk = 60.0  # Regen Braking event!
        else:
            th = 30.0; brk = 0.0

        st = plant_hyb.step(dt=dt, throttle_demand_pct=th, brake_demand_pct=brk)
        time_hyb.append(t_sec)
        speed_hyb.append(st['VehicleSpeed'])
        isg_torq_hyb.append(st['ISG_TorqueAssist'])
        soc_hyb.append(st['LiIon_BatterySOC'])
        mode_hyb.append(st['ISG_OperationalMode'])

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 6.5), dpi=300, sharex=True)

    ax1.plot(time_hyb, speed_hyb, color='#2C3E50', linewidth=2.0, label='Vehicle Speed (km/h)')
    ax1.set_ylabel('Speed (km/h)', fontweight='bold')
    ax1.grid(True, linestyle='--', alpha=0.5)
    ax1.set_ylim(-5, 120)

    # Shade Assist and Regen regions
    ax1.axvspan(10.0, 25.0, color='#F9E79F', alpha=0.5, label='SHVS Torque Assist Active (+ISG)')
    ax1.axvspan(25.0, 38.0, color='#D5F5E3', alpha=0.5, label='SHVS Regen Braking Active (Energy Harvest)')
    ax1.legend(loc='upper left', fontsize=9)
    ax1.set_title('Smart Hybrid (SHVS) Multi-Mode Dynamic Drive Cycle', fontweight='bold', fontsize=12)

    ax2.plot(time_hyb, isg_torq_hyb, color='#8E44AD', linewidth=2.2, label='ISG Torque (Nm) [+Assist / -Regen]')
    ax2.set_ylabel('ISG Torque (Nm)', color='#8E44AD', fontweight='bold')
    ax2.set_xlabel('Cycle Time (seconds)', fontweight='bold')
    ax2.tick_params(axis='y', labelcolor='#8E44AD')
    ax2.set_ylim(-55, 55)
    ax2.axhline(0, color='#7F8C8D', linestyle='-', linewidth=0.8)
    ax2.grid(True, linestyle='--', alpha=0.5)

    ax2_soc = ax2.twinx()
    ax2_soc.plot(time_hyb, soc_hyb, color='#16A085', linewidth=2.2, linestyle='--', label='12V Li-Ion Battery SOC (%)')
    ax2_soc.set_ylabel('Li-Ion SOC (%)', color='#16A085', fontweight='bold')
    ax2_soc.tick_params(axis='y', labelcolor='#16A085')
    ax2_soc.set_ylim(70, 90)

    plt.tight_layout()
    p3_path = os.path.join(output_dir, "shvs_hybrid_energy_assist_regen_cycle.png")
    plt.savefig(p3_path, dpi=300)
    plt.close()
    print(f"Saved: {p3_path}")

if __name__ == "__main__":
    out = os.path.join(os.path.dirname(__file__), "figures")
    generate_plots(out)
