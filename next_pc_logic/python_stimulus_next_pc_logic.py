import random
import cocotb
from cocotb.triggers import Timer
from osoc1_core_uarch import module_next_pc_logic, module_pc_plus_4

@cocotb.test()
async def automated_next_pc_test(dut):
    """Verify Next PC logic including memory wrapping bounds and LSB masking."""

    MAX_VAL = 0xFFFFFFFF
    MIN_VAL = 0x00000000

    # Test Matrix: (Desc, pc_curr, pc_plus_4, imm, alu_res, pc_src)
    test_cases = [
        # --- Absolute Boundaries: JALR LSB Masking ---
        ("JALR LSB Strip (Max Val)",    MIN_VAL, MIN_VAL, MIN_VAL, MAX_VAL, 2),
        ("JALR LSB Strip (Odd number)", MIN_VAL, MIN_VAL, MIN_VAL, 0x0000000F, 2),
        ("JALR No Strip (Even number)", MIN_VAL, MIN_VAL, MIN_VAL, 0x0000000E, 2),

        # --- Absolute Boundaries: Branch Adder Wrapping ---
        ("Branch Wrap Max PC + Max Imm", MAX_VAL, MIN_VAL, MAX_VAL, MIN_VAL, 1),
        ("Branch Wrap Max PC + 4",       MAX_VAL, MIN_VAL, 4,       MIN_VAL, 1),
        ("Branch Min PC + Min Imm",      MIN_VAL, MIN_VAL, MIN_VAL, MIN_VAL, 1),

        # --- Standard Fallthrough Boundaries ---
        ("PC+4 Pass-through (Max PC)",   MAX_VAL, module_pc_plus_4(MAX_VAL), MIN_VAL, MIN_VAL, 0),
        ("PC+4 Pass-through (Min PC)",   MIN_VAL, module_pc_plus_4(MIN_VAL), MIN_VAL, MIN_VAL, 0),
    ]

    # Add Random Fuzzing
    for i in range(10):
        pc = random.randint(MIN_VAL, MAX_VAL)
        test_cases.append((
            f"Random Fuzz {i}",
            pc,
            module_pc_plus_4(pc),
            random.randint(MIN_VAL, MAX_VAL),
            random.randint(MIN_VAL, MAX_VAL),
            random.choice([0, 1, 2])
        ))

    dut._log.info("Starting Next-PC Logic Verification...")

    for desc, pc, pc4, imm, alu, src in test_cases:
        # Drive pins
        dut.pc_curr_i.value   = pc
        dut.pc_plus_4_i.value = pc4
        dut.imm_i.value       = imm
        dut.alu_res_i.value   = alu
        dut.pc_src_i.value    = src

        await Timer(1, unit="ns")

        # Get Golden Result
        exp_next_pc = module_next_pc_logic(pc, pc4, imm, alu, src)

        # Read Hardware and clamp to 32 bits
        hw_next_pc = int(dut.pc_next_o.value) & 0xFFFFFFFF

        assert hw_next_pc == exp_next_pc, \
            f"FAIL ({desc})! Exp: 0x{exp_next_pc:08X} | Act: 0x{hw_next_pc:08X}"

        dut._log.info(f"PASS: {desc} | pc_next_o: 0x{hw_next_pc:08X}")

    dut._log.info("SUCCESS: All Next-PC boundaries and masking tests passed!")
