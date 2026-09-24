import random
import cocotb
from cocotb.triggers import Timer

# Import your updated Python Golden Model
from osoc1_core_uarch import module_sau


@cocotb.test()
async def automated_sau_test(dut):
    """Verify Data Replication, Strobe Generation, and Safety Gates."""

    MAX_VAL = 0xFFFFFFFF

    # Test Matrix: (Description, mem_we, rs2_val, adrs_1, adrs_0, f3)
    test_cases = [
        # --- Store Byte (sb) across all 4 lanes ---
        ("SB: Lane 0 (adrs 00)", 1, 0x12345678, 0, 0, 0b000),
        ("SB: Lane 1 (adrs 01)", 1, 0x12345678, 0, 1, 0b000),
        ("SB: Lane 2 (adrs 10)", 1, 0x12345678, 1, 0, 0b000),
        ("SB: Lane 3 (adrs 11)", 1, 0x12345678, 1, 1, 0b000),

        # --- Store Halfword (sh) across both halves ---
        ("SH: Lower Half (adrs 0X)", 1, 0xDEADBEEF, 0, 0, 0b001),
        ("SH: Upper Half (adrs 1X)", 1, 0xDEADBEEF, 1, 0, 0b001),

        # --- Store Word (sw) ---
        ("SW: Full Word", 1, MAX_VAL, 0, 0, 0b010),

        # --- THE SAFETY GATE (mem_we = 0) ---
        ("Safety Gate: Block SB", 0, MAX_VAL, 0, 0, 0b000),
        ("Safety Gate: Block SW", 0, MAX_VAL, 0, 0, 0b010),
    ]

    # Add Random Fuzzing
    for i in range(15):
        test_cases.append((
            f"Random Fuzz {i}",
            random.randint(0, 1),
            random.randint(0, MAX_VAL),
            random.randint(0, 1),
            random.randint(0, 1),
            random.choice([0b000, 0b001, 0b010])
        ))

    dut._log.info("Starting SAU Combinational Verification...")

    for desc, mem_we, rs2_val, adrs_1, adrs_0, f3 in test_cases:

        # Drive hardware inputs
        dut.mem_we_i.value = mem_we
        dut.rs2_val_i.value = rs2_val
        dut.adrs_1_i.value = adrs_1
        dut.adrs_0_i.value = adrs_0
        dut.f3_i.value = f3

        # Propagation delay for combinational logic
        await Timer(1, unit="ns")

        # Read hardware simulator
        hw_wdata = int(dut.wdata_o.value) & MAX_VAL
        hw_strobe = int(dut.strobe_o.value) & 0xF

        # Golden model comparison
        exp_wdata, exp_strobe = module_sau(
            mem_we, rs2_val, adrs_1, adrs_0, f3
        )

        # Assertions
        assert hw_wdata == exp_wdata, \
            f"FAIL ({desc}) WDATA! Exp: 0x{exp_wdata:08X} | Act: 0x{hw_wdata:08X}"

        assert hw_strobe == exp_strobe, \
            f"FAIL ({desc}) STROBE! Exp: {bin(exp_strobe)} | Act: {bin(hw_strobe)}"

        dut._log.info(
            f"PASS: {desc} | Strobe: {bin(hw_strobe)} | Data: 0x{hw_wdata:08X}"
        )

    dut._log.info(
        "SUCCESS: SAU perfectly replicates data and masks strobes!"
    )
