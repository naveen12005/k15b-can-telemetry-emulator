"""
Generate Master Word Portfolio Dossier (.docx) for K15B Telemetry Digital Twin
==============================================================================
Creates a publication-quality engineering report with embedded figures,
signal matrices, powertrain equations, and formal academic citations.

Author: RATHLAVATH NAVEEN (rathlavathnaveen90@gmail.com)
Copyright (c) 2026 RATHLAVATH NAVEEN. All Rights Reserved.
"""

import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

def generate_dossier(target_path, fig_dir):
    doc = docx.Document()

    # 1-inch margins
    for s in doc.sections:
        s.top_margin = Inches(1.0)
        s.bottom_margin = Inches(1.0)
        s.left_margin = Inches(1.0)
        s.right_margin = Inches(1.0)

    # Palette
    C_PRIMARY = RGBColor(27, 54, 93)     # Navy
    C_SECONDARY = RGBColor(192, 57, 43)  # Automotive Crimson Red
    C_DARK = RGBColor(40, 40, 40)
    C_MUTED = RGBColor(90, 105, 120)

    def add_title(text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after = Pt(4)
        run = p.add_run(text)
        run.font.name = 'Calibri'
        run.font.size = Pt(22)
        run.font.bold = True
        run.font.color.rgb = C_PRIMARY
        return p

    def add_subtitle(text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(18)
        run = p.add_run(text)
        run.font.name = 'Calibri'
        run.font.size = Pt(12)
        run.font.italic = True
        run.font.color.rgb = C_MUTED
        return p

    def add_h1(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(16)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.font.name = 'Calibri'
        run.font.size = Pt(15)
        run.font.bold = True
        run.font.color.rgb = C_PRIMARY
        return p

    def add_h2(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.font.name = 'Calibri'
        run.font.size = Pt(12)
        run.font.bold = True
        run.font.color.rgb = C_SECONDARY
        return p

    def add_p(text, bold_pre=None, space_after=6):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(space_after)
        p.paragraph_format.line_spacing = 1.15
        if bold_pre:
            r_pre = p.add_run(bold_pre)
            r_pre.font.name = 'Calibri'
            r_pre.font.size = Pt(10.5)
            r_pre.font.bold = True
            r_pre.font.color.rgb = C_DARK
        run = p.add_run(text)
        run.font.name = 'Calibri'
        run.font.size = Pt(10.5)
        run.font.color.rgb = C_DARK
        return p

    def add_bullet(text):
        p = doc.add_paragraph(style='List Bullet')
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.line_spacing = 1.15
        run = p.add_run(text)
        run.font.name = 'Calibri'
        run.font.size = Pt(10)
        run.font.color.rgb = C_DARK
        return p

    # --- Title ---
    add_title("Maruti K15B 1.5L Powertrain & Smart Hybrid (SHVS)\nCAN Telemetry Digital Twin & Diagnostic Pipeline")
    add_subtitle("Automotive Model-Based Systems Engineering (MBSE), CAN 2.0A DBC Matrix & OBD-II Verification")

    add_p(
        "Author / Lead Systems Engineer: RATHLAVATH NAVEEN (rathlavathnaveen90@gmail.com)\n"
        "Repository: https://github.com/naveen12005/k15b-can-telemetry-emulator\n"
        "Governing Automotive Standards: ISO 11898 (CAN 2.0A/B), SAE J1939, SAE J1979 (OBD-II), ISO 14229 (UDS), ISO 26262 (ASIL-D)\n"
        "Platform: Python 3.10+, SocketCAN / VirtualBus, Cantools, Matplotlib"
    )

    # --- 1. Executive Summary ---
    add_h1("1. Executive Summary & Automotive Problem Context")
    add_p(
        "Modern vehicle electronic control units (ECUs) and hybrid supervisory controllers communicate over high-speed "
        "Controller Area Network (CAN) buses operating under sub-millisecond real-time timing constraints. Testing instrument "
        "clusters, battery management systems, and diagnostic scan tools against physical vehicles on dyno test cells is expensive, "
        "hazard-prone, and constrained by physical test bench availability.",
        bold_pre="The Industry Testing Dilemma: "
    )
    add_p(
        "This project implements a complete Software-in-the-Loop (SIL) Powertrain Digital Twin for the Suzuki / Maruti K15B 1.5L "
        "naturally aspirated DOHC VVT engine equipped with the Dual-Battery Smart Hybrid Vehicle System (SHVS). It synthesizes a "
        "Mean-Value Engine Model (MVEM), dyno-calibrated full-load torque curves (138 Nm @ 4,400 RPM), 12V Li-ion ISG torque assist "
        "and regenerative braking, and SAE J1979 OBD-II diagnostic query processing across a multi-node CAN 2.0A network (vehicle.dbc).",
        bold_pre="The Engineering Solution: "
    )

    # --- 2. CAN Matrix Specification ---
    add_h1("2. Multi-Node CAN Bus Matrix Architecture (vehicle.dbc)")
    add_p(
        "The communication bus simulates an authentic automotive topology with dedicated Electronic Control Module (ECM), "
        "Smart Hybrid Controller (SHVS_CTRL), Instrument Cluster, and Diagnostic Tool nodes:"
    )

    headers = ["CAN ID", "Message Name", "Cycle Rate", "DLC", "Primary Telemetry Signals"]
    table_data = [
        ["0x100 (256)", "ECM_EngineGeneralStatus", "20 Hz (50 ms)", "8 Bytes", "EngineSpeed (0.25 rpm), VehicleSpeed (1 km/h), ThrottlePos (0.4%), CoolantTemp (-40..215°C), EngineLoad, FuelFlowRate (0.01 L/h)"],
        ["0x105 (261)", "ECM_DynamicEngineKinetics", "50 Hz (20 ms)", "8 Bytes", "EngineTorque (0.1 Nm), MAP (1 kPa), IntakeAirTemp, Lambda AFR (0.001), SparkAdvance (0.5°CA), KnockRetard, MIL_Status"],
        ["0x200 (512)", "SHVS_HybridStatus", "20 Hz (50 ms)", "8 Bytes", "ISG_Mode (Assist/Regen/Charge), ISG_Torque (-50..+50 Nm), Current (-100..+100 A), Li-Ion SOC (0.5%), Pack Voltage, Energy Recovered (kWh)"],
        ["0x7E0 (2016)", "OBD2_DiagnosticRequest", "Event-driven", "8 Bytes", "Client Request: Service Mode (0x01, 0x03, 0x04), Parameter ID (PID: 0x0C, 0x0D, 0x05, 0x0B, 0x11), Data Payload A-D"],
        ["0x7E8 (2024)", "OBD2_DiagnosticResponse", "Event-driven", "8 Bytes", "ECU Positive/Negative Response (+0x40 Service Echo), PID echo, Encoded physical sensor data bytes A-D"]
    ]

    t = doc.add_table(rows=len(table_data) + 1, cols=len(headers))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, h in enumerate(headers):
        cell = t.cell(0, j)
        cell.paragraphs[0].text = h
        cell.paragraphs[0].runs[0].font.bold = True
        cell.paragraphs[0].runs[0].font.size = Pt(9)
        cell.paragraphs[0].runs[0].font.color.rgb = C_PRIMARY

    for i, row in enumerate(table_data):
        for j, val in enumerate(row):
            cell = t.cell(i + 1, j)
            cell.paragraphs[0].text = val
            cell.paragraphs[0].runs[0].font.size = Pt(8.5)

    # --- 3. Embedded Engineering Figures ---
    add_h1("3. Powertrain Simulation Verification & High-Resolution Figures")

    fig1 = os.path.join(fig_dir, "k15b_dynamometer_torque_power_curves.png")
    if os.path.exists(fig1):
        doc.add_paragraph().paragraph_format.space_before = Pt(8)
        p_img1 = doc.add_paragraph()
        p_img1.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img1.add_run().add_picture(fig1, width=Inches(6.2))
        cap1 = doc.add_paragraph()
        cap1.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r1 = cap1.add_run("Figure 1: Maruti Suzuki K15B 1.5L Dynamometer Full-Load Torque & Power Curves (138 Nm @ 4,400 RPM, 77 kW @ 6,000 RPM).")
        r1.font.size = Pt(9); r1.font.italic = True; r1.font.color.rgb = C_MUTED

    fig2 = os.path.join(fig_dir, "k15b_coldstart_thermal_idle_flare.png")
    if os.path.exists(fig2):
        doc.add_paragraph().paragraph_format.space_before = Pt(8)
        p_img2 = doc.add_paragraph()
        p_img2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img2.add_run().add_picture(fig2, width=Inches(6.2))
        cap2 = doc.add_paragraph()
        cap2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r2 = cap2.add_run("Figure 2: Cold-Start Thermal Warmup ODE and Automatic Fast-Idle Flare (1,250 RPM Cold -> 750 RPM Warm Idle Stabilization).")
        r2.font.size = Pt(9); r2.font.italic = True; r2.font.color.rgb = C_MUTED

    fig3 = os.path.join(fig_dir, "shvs_hybrid_energy_assist_regen_cycle.png")
    if os.path.exists(fig3):
        doc.add_paragraph().paragraph_format.space_before = Pt(8)
        p_img3 = doc.add_paragraph()
        p_img3.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img3.add_run().add_picture(fig3, width=Inches(6.2))
        cap3 = doc.add_paragraph()
        cap3.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r3 = cap3.add_run("Figure 3: Dual-Battery Smart Hybrid (SHVS) Drive Cycle: +50 Nm Torque Assist under Hard Tip-In and -35 Nm Regenerative Energy Harvesting.")
        r3.font.size = Pt(9); r3.font.italic = True; r3.font.color.rgb = C_MUTED

    # --- 4. Automotive Verification Suite ---
    add_h1("4. Automated CI/CD Safety & Invariant Verification Suite")
    add_p("The project test suite (test_pipeline.py) asserts 10 formal automotive engineering requirements:")
    add_bullet("Test 1: DBC Structural Integrity — Message ID allocation and strict 8-byte DLC constraints.")
    add_bullet("Test 2: Signal Quantization Fidelity — Zero bit-drift across 0.25 rpm quantization steps.")
    add_bullet("Test 3: K15B Torque Invariants — Physical torque output bounded strictly within the 0 to 138 Nm envelope.")
    add_bullet("Test 4: Thermal Warmup Convergence — First-order thermal ODE stability to 88°C thermostat regulation.")
    add_bullet("Test 5: SHVS Torque Assist Activation — Verified assist trigger when Throttle > 60% and Li-Ion SOC > 30%.")
    add_bullet("Test 6: Regenerative Braking Energy Balance — Kinetic energy harvest into Li-ion battery during deceleration.")
    add_bullet("Test 7: SAE J1979 OBD-II Query Response — Positive response (+0x40) for PIDs 0x0C (RPM), 0x05 (ECT), 0x0B (MAP).")
    add_bullet("Test 8: DTC Fault Injection & MIL Flag — Accurate emission of P0118 / P0300 and diagnostic trouble clearing.")
    add_bullet("Test 9: Manifold Air Charging Dynamics — MAP accurately tracks throttle demand from 32 kPa idle vacuum to 100 kPa WOT.")
    add_bullet("Test 10: Bitstream Roundtrip Integrity — End-to-end byte buffer encoding/decoding without drift across all 4 frames.")

    # --- 5. Academic References ---
    add_h1("5. Academic References & Automotive Engineering Standards")
    add_p("The mathematical formulations and network architecture implement standards from peer-reviewed literature and international bodies:")
    add_bullet("1. Robert Bosch GmbH. (1991). CAN Specification Version 2.0. Stuttgart, Germany.")
    add_bullet("2. International Organization for Standardization. (2015). ISO 11898-1: Road vehicles — Controller area network (CAN) — Part 1: Data link layer and physical signalling.")
    add_bullet("3. Society of Automotive Engineers. (2012). SAE J1979 / ISO 15031-5: E/E Diagnostic Test Modes.")
    add_bullet("4. International Organization for Standardization. (2020). ISO 14229-1: Road vehicles — Unified diagnostic services (UDS) — Part 1: Application layer.")
    add_bullet("5. Hendricks, E., & Sorenson, S. C. (1990). Mean Value Modelling of SI Engines. SAE Transactions, 99, 1359–1373.")
    add_bullet("6. Guzzella, L., & Onder, C. H. (2010). Introduction to Modeling and Control of Internal Combustion Engine Systems (2nd ed.). Springer-Verlag.")

    # --- 6. Author & License Notice ---
    add_h1("6. Author & Intellectual Property Notice")
    p_auth = doc.add_paragraph()
    r_a = p_auth.add_run("Author / Lead Systems Engineer: ")
    r_a.font.bold = True
    p_auth.add_run("RATHLAVATH NAVEEN (rathlavathnaveen90@gmail.com)\n")
    r_u = p_auth.add_run("GitHub Profile: ")
    r_u.font.bold = True
    p_auth.add_run("https://github.com/naveen12005\n")
    r_r = p_auth.add_run("Project Repository: ")
    r_r.font.bold = True
    p_auth.add_run("https://github.com/naveen12005/k15b-can-telemetry-emulator\n")
    r_l = p_auth.add_run("Copyright & License: ")
    r_l.font.bold = True
    p_auth.add_run("Copyright © 2026 RATHLAVATH NAVEEN. All Rights Reserved. Protected under the Proprietary Portfolio Evaluation License (incorporating CC BY-NC-ND 4.0 terms).")

    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    doc.save(target_path)
    print(f"Master Word Dossier successfully created at: {target_path}")

if __name__ == "__main__":
    rep_dir = os.path.dirname(os.path.abspath(__file__))
    f_dir = os.path.join(rep_dir, "figures")
    out_docx = os.path.join(rep_dir, "K15B_Powertrain_CAN_Telemetry_Engineering_Dossier.docx")
    generate_dossier(out_docx, f_dir)
