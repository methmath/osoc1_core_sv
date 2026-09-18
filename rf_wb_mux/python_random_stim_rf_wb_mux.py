import random
import cocotb
from cocotb.triggers import Timer

# ==============================================================================
# 1. THE GOLDEN ORACLE
# ==============================================================================
def python_rf_wb_mux(alu_res_i, lau_res_i, pc_plus_4_i, d2r_sel_i):
    if d2r_sel_i == 0:
        return alu_res_i
    elif d2r_sel_i == 1:
        return lau_res_i
    elif d2r_sel_i == 2:
        return pc_plus_4_i
    else:
        return 0

# ==============================================================================
# 2. AUTOMATED RANDOM VERIFICATION
# ==============================================================================
@cocotb.test()
async def automated_random_mux_test(dut):
    """Verify the Mux using boundary conditions and constrained random inputs."""
    
    MAX_VAL = 0xFFFFFFFF
    MIN_VAL = 0x00000000
    
    # Step A: Explicitly enforce the mandatory maximum and minimum boundary checks
    test_cases = [
        (MAX_VAL, MIN_VAL, MIN_VAL, 0), 
        (MIN_VAL, MAX_VAL, MIN_VAL, 1), 
        (MIN_VAL, MIN_VAL, MAX_VAL, 2), 
        (MAX_VAL, MAX_VAL, MAX_VAL, 3)  # Invalid select line check
    ]
    
    # Step B: Generate 100 random input permutations for broad coverage
    NUM_RANDOM_TESTS = 100
    
    for _ in range(NUM_RANDOM_TESTS):
        alu = random.randint(MIN_VAL, MAX_VAL)
        lau = random.randint(MIN_VAL, MAX_VAL)
        pc4 = random.randint(MIN_VAL, MAX_VAL)
        sel = random.randint(0, 3)
        test_cases.append((alu, lau, pc4, sel))

    # Step C: The Automated Execution Engine
    for alu, lau, pc4, sel in test_cases:
        
        # 1. Drive the random data into the physical SystemVerilog pins
        dut.alu_res_i.value   = alu
        dut.lau_res_i.value   = lau
        dut.pc_plus_4_i.value = pc4
        dut.d2r_sel_i.value   = sel
        
        # 2. Wait for the combinational logic to propagate
        await Timer(1, unit="ns")
        
        # 3. Ask the Python Oracle what the answer should mathematically be
        expected_output = python_rf_wb_mux(alu, lau, pc4, sel)
        
        # 4. Read the physical hardware pin
        actual_output = int(dut.rf_wd_o.value)
        
        #print(f"alu={alu},lau={lau},pc4={pc4},sel={sel},actual={actual_output},expected={expected_output}\n")
        # 5. Log the inputs and outputs beautifully to the terminal
        dut._log.info(
            f"SEL: {sel} | ALU: {hex(alu):>10} | LAU: {hex(lau):>10} | PC+4: {hex(pc4):>10} || "
            f"EXPECTED: {hex(expected_output):>10} | ACTUAL: {hex(actual_output):>10}"
        )
        #dut._log.info(
        #    f"SEL: {sel} | ALU: {alu:>10} | LAU: {lau:>10} | PC+4: {pc4:>10} || "
        #    f"EXPECTED: {expected_output:>10} | ACTUAL: {actual_output:>10}"
        #)
        # 5. Automatically compare!
        assert actual_output == expected_output, \
            f"FAIL! Sel: {sel} | Expected: {hex(expected_output)} | Hardware: {hex(actual_output)}"

    dut._log.info("-" * 80)
    dut._log.info("SUCCESS: All boundary and random tests passed!")
