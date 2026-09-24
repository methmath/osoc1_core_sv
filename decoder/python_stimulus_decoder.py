import random 
import cocotb 
from cocotb.triggers import Timer 
from osoc1_core_uarch import module_decoder 
 
# ============================================================================== 
# AUTOMATED RANDOM VERIFICATION 
# ============================================================================== 
@cocotb.test() 
async def automated_decoder_test(dut): 
    """Verify decoder using max/min boundaries and random inputs.""" 
 
    MAX_VAL = 0xFFFFFFFF 
    MIN_VAL = 0x00000000 
 
    # Step A: Mandatory Maximum and Minimum Boundary Checks 
    test_cases = [ 
        MAX_VAL, 
        MIN_VAL, 
        0x7FF10093, # I-Type Max Positive 
        0x80010093, # I-Type Max Negative 
        0x80112023, # S-Type Max Negative 
        0x80000063, # B-Type Max Negative 
        0x800000EF  # J-Type Max Negative 
    ] 
 
    # Step B: Constrained Random Vectors 
    NUM_RANDOM_TESTS = 10 
    for _ in range(NUM_RANDOM_TESTS): 
        # Generate raw 32-bit integers instead of tuples 
        test_cases.append(random.randint(MIN_VAL, MAX_VAL)) 
 
    dut._log.info("Starting decoder Verification...") 
    dut._log.info("-" * 80) 
 
    # Step C: The Execution Engine 
    for instr_i in test_cases: 
 
        # 1. Auto-Generated Hardware Pin Driving 
        dut.instr_i.value = instr_i 
 
        # 2. Wait for propagation 
        await Timer(1, unit="ns") 
 
        # 3. Ask Golden Oracle (Unpack the 7 outputs) 
        exp_op, exp_rd, exp_rs1, exp_rs2, exp_f3, exp_f7, exp_imm = module_decoder(instr_i) 
 
        # 4. Read Hardware Pins 
        hw_op  = int(dut.op_o.value) 
        hw_rd  = int(dut.rd_o.value) 
        hw_f3  = int(dut.f3_o.value) 
        hw_rs1 = int(dut.rs1_o.value) 
        hw_rs2 = int(dut.rs2_o.value) 
        hw_f7  = int(dut.f7_o.value) 
        hw_imm = int(dut.imm_o.value) 
 
        # Force 32-bit unsigned boundaries for Python comparison 
        exp_imm_32b = exp_imm & 0xFFFFFFFF 
        hw_imm_32b  = hw_imm & 0xFFFFFFFF 
 
        # 5. Log Output 
        dut._log.info(f"INPUT: 0x{instr_i:08X} | EXP IMM: 0x{exp_imm_32b:08X} | HW IMM: 0x{hw_imm_32b:08X}") 
 
        # 6. Check Results 
        assert hw_op == exp_op,   f"OPCODE FAIL! Expected: {exp_op} | Actual: {hw_op}" 
        assert hw_rd == exp_rd,   f"RD FAIL! Expected: {exp_rd} | Actual: {hw_rd}" 
        assert hw_rs1 == exp_rs1, f"RS1 FAIL! Expected: {exp_rs1} | Actual: {hw_rs1}" 
        assert hw_rs2 == exp_rs2, f"RS2 FAIL! Expected: {exp_rs2} | Actual: {hw_rs2}" 
        assert hw_f3 == exp_f3,   f"F3 FAIL! Expected: {exp_f3} | Actual: {hw_f3}" 
        assert hw_f7 == exp_f7,   f"F7 FAIL! Expected: {exp_f7} | Actual: {hw_f7}" 
        assert hw_imm_32b == exp_imm_32b, f"IMM FAIL! Expected: 0x{exp_imm_32b:08X} | Actual: 0x{hw_imm_32b:08X}" 
 
    dut._log.info("-" * 80) 
    dut._log.info("SUCCESS: Boundary and random tests passed for decoder!")
