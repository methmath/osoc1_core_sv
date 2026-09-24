import random
import cocotb
from cocotb.triggers import Timer
from osoc1_core_uarch import module_lau


@cocotb.test()
async def automated_lau_test(dut):
    """Verify LAU using max/min boundaries across all alignments and extensions."""

    MAX_VAL = 0xFFFFFFFF
    MIN_VAL = 0x00000000

    # Test Matrix:
    # (Description, Data, adrs_1, adrs_0, funct3)
    #
    # funct3:
    # 0 = LB
    # 1 = LH
    # 2 = LW
    # 4 = LBU
    # 5 = LHU

    test_cases = [

        # --- Absolute Boundaries on Load Byte Signed (LB) ---
        ("LB Max Negative (0xFF), Offset 0", MAX_VAL, 0, 0, 0),
        ("LB Max Negative (0xFF), Offset 3", MAX_VAL, 1, 1, 0),
        ("LB Min Zeros, Offset 2", MIN_VAL, 1, 0, 0),
        ("LB Specific Sign Bit (0x80)", 0x00000080, 0, 0, 0),

        # --- Absolute Boundaries on Load Byte Unsigned (LBU) ---
        ("LBU Max Val (0xFF), Offset 0", MAX_VAL, 0, 0, 4),
        ("LBU Max Val (0xFF), Offset 3", MAX_VAL, 1, 1, 4),

        # --- Absolute Boundaries on Load Halfword Signed (LH) ---
        ("LH Max Negative (0xFFFF), Offset 0", MAX_VAL, 0, 0, 1),
        ("LH Max Negative (0xFFFF), Offset 2", MAX_VAL, 1, 0, 1),
        ("LH Specific Sign Bit (0x8000)", 0x00008000, 0, 0, 1),

        # --- Absolute Boundaries on Load Halfword Unsigned (LHU) ---
        ("LHU Max Val (0xFFFF), Offset 0", MAX_VAL, 0, 0, 5),
        ("LHU Max Val (0xFFFF), Offset 2", MAX_VAL, 1, 0, 5),

        # --- Absolute Boundaries on Load Word (LW) ---
        ("LW Max Val", MAX_VAL, 0, 0, 2),
        ("LW Min Val", MIN_VAL, 0, 0, 2),
    ]

    # Add Random Fuzzing
    for i in range(15):
        test_cases.append((
            f"Random Fuzz {i}",
            random.randint(MIN_VAL, MAX_VAL),
            random.randint(0, 1),
            random.randint(0, 1),
            random.choice([0, 1, 2, 4, 5])
        ))

    dut._log.info("Starting LAU Verification...")

    for desc, mem_data, a1, a0, f3 in test_cases:

        # Drive pins
        dut.mem_data_i.value = mem_data
        dut.adrs_1_i.value = a1
        dut.adrs_0_i.value = a0
        dut.funct3_i.value = f3

        await Timer(1, unit="ns")

        # Get Golden Results from Python Execution Engine
        exp_aligned = module_lau(mem_data, a1, a0, f3)

        # Read Hardware
        hw_aligned = int(dut.aligned_data_o.value)

        # Force both to 32-bit unsigned boundaries
        exp_aligned_32b = exp_aligned & 0xFFFFFFFF
        hw_aligned_32b = hw_aligned & 0xFFFFFFFF

        assert hw_aligned_32b == exp_aligned_32b, \
            f"DATA FAIL ({desc})! Exp: 0x{exp_aligned_32b:08X} | Act: 0x{hw_aligned_32b:08X}"

        dut._log.info(
            f"PASS: {desc} | Data: 0x{hw_aligned_32b:08X}"
        )

    dut._log.info(
        "SUCCESS: All LAU boundary and extraction tests passed!"
    )
