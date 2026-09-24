import random
import cocotb
from cocotb.triggers import Timer
from osoc1_core_uarch import module_bcu

@cocotb.test()
async def automated_bcu_test(dut):
    """Verify BCU logic, Priority Encoder, and extreme flag boundaries."""

    # Test Matrix: (Description, f3, flags(Z,S,O,C), cond_br, jal, jalr)
    test_cases = [
        # --- Absolute Boundaries: Priority Encoder Overrides ---
        ("JALR Priority Max Flags",  0, (1,1,1,1), 1, 1, 1),
        ("JALR Priority Min Flags",  0, (0,0,0,0), 0, 0, 1),
        ("JAL Priority over Branch", 0, (0,0,0,0), 0, 1, 0),

        # --- Branch Equivalency Boundaries (BEQ / BNE) ---
        ("BEQ Match (Z=1)",     0, (1,0,0,0), 1, 0, 0),
        ("BEQ No Match (Z=0)",  0, (0,0,0,0), 1, 0, 0),
        ("BNE Match (Z=0)",     1, (0,0,0,0), 1, 0, 0),
        ("BNE No Match (Z=1)",  1, (1,0,0,0), 1, 0, 0),

        # --- Signed Comparison Boundaries (BLT / BGE) ---
        ("BLT True (S!=O)",     4, (0,1,0,0), 1, 0, 0),
        ("BLT False (S==O)",    4, (0,1,1,0), 1, 0, 0),
        ("BGE True (S==O)",    5, (0,0,0,0), 1, 0, 0),
        ("BGE False (S!=O)",   5, (0,1,0,0), 1, 0, 0),

        # --- Unsigned Comparison Boundaries (BLTU / BGEU) ---
        ("BLTU True (C=0)",     6, (0,0,0,0), 1, 0, 0),
        ("BLTU False (C=1)",    6, (0,0,0,1), 1, 0, 0),
        ("BGEU True (C=1)",     7, (0,0,0,1), 1, 0, 0),
        ("BGEU False (C=0)",    7, (0,0,0,0), 1, 0, 0),

        # --- No Branch Triggered (PC+4 Fallthrough) ---
        ("Normal Instruction",  0, (0,0,0,0), 0, 0, 0),
    ]

    # Add Random Fuzzing for unexpected combinations
    for i in range(20):
        test_cases.append((
            f"Random Fuzz {i}",
            random.choice([0, 1, 4, 5, 6, 7]),
            (
                random.randint(0,1),
                random.randint(0,1),
                random.randint(0,1),
                random.randint(0,1)
            ),
            random.randint(0, 1),
            random.randint(0, 1),
            random.randint(0, 1)
        ))

    dut._log.info("Starting BCU Verification...")

    for desc, f3, flags, cond_br, jal, jalr in test_cases:

        # Pack the flags tuple into a 4-bit integer
        z, s, o, c = flags
        flags_int = (z << 3) | (s << 2) | (o << 1) | c

        # Drive pins
        dut.f3_i.value = f3
        dut.flags_i.value = flags_int
        dut.is_cond_branch_i.value = cond_br
        dut.is_jal_i.value = jal
        dut.is_jalr_i.value = jalr

        await Timer(1, unit="ns")

        # Get Golden Results from Python Execution Engine
        exp_pc_src = module_bcu(f3, flags, cond_br, jal, jalr)

        # Read Hardware
        hw_pc_src = int(dut.pc_src_o.value)

        assert hw_pc_src == exp_pc_src, \
            f"FAIL ({desc})! Exp pc_src: {exp_pc_src} | Act: {hw_pc_src}"

        dut._log.info(f"PASS: {desc} | pc_src_o: {hw_pc_src}")

    dut._log.info("SUCCESS: All BCU logic and priority bounds passed!")
