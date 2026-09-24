import random
import cocotb
from cocotb.triggers import Timer
from osoc1_core_uarch import module_pc_plus_4

@cocotb.test()
async def automated_pc_plus_4_test(dut):
    """Verify dedicated PC+4 adder with strict max/min boundaries."""

    MAX_VAL = 0xFFFFFFFF
    MIN_VAL = 0x00000000

    # Test Matrix: (Description, pc_curr)
    test_cases = [
        # --- Absolute Minimum Boundary ---
        ("Min Boundary (0x0)", MIN_VAL),

        # --- Standard Execution ---
        ("Standard Alignment", 0x00000100),

        # --- Absolute Maximum Rollover Boundaries ---
        ("Max Boundary (Aligned Wrap: 0xFFFFFFFC)", 0xFFFFFFFC),
        ("Max Boundary (Absolute Wrap: 0xFFFFFFFF)", MAX_VAL),
    ]

    # Add Random Fuzzing
    for i in range(10):
        test_cases.append(
            (f"Random Fuzz {i}", random.randint(MIN_VAL, MAX_VAL))
        )

    dut._log.info("Starting PC+4 Verification...")

    for desc, pc in test_cases:
        # Drive pins
        dut.pc_curr_i.value = pc
        await Timer(1, unit="ns")

        # Get Golden Result
        exp_pc = module_pc_plus_4(pc)

        # Read Hardware and clamp to 32 bits
        hw_pc = int(dut.pc_plus_4_o.value) & 0xFFFFFFFF

        assert hw_pc == exp_pc, \
            f"FAIL ({desc})! Exp: 0x{exp_pc:08X} | Act: 0x{hw_pc:08X}"

        dut._log.info(
            f"PASS: {desc} | pc_plus_4_o: 0x{hw_pc:08X}"
        )

    dut._log.info("SUCCESS: All PC+4 boundaries passed!")
