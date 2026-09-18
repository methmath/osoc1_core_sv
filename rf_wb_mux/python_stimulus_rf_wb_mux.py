import cocotb
from cocotb.triggers import Timer
from cocotb.types import LogicArray

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

def module_rf_wb_mux(alu_res_i, lau_res_i, pc_plus_4_i, d2r_sel_i):
    """
    RF Write-Back Mux (The Yellow Box)
    d2r_sel_i: 0=ALU, 1=LAU (Memory), 2=PC+4
    """
    print(f"--- inside the module module_rf_wb_mux ---")

    # Selection Logic based on the Control Unit 'D2R' signal
    if d2r_sel_i == 0:
        rf_wd_o = alu_res_i       # Path from ALU (Pink wire)
    elif d2r_sel_i == 1:
        rf_wd_o = lau_res_i       # Path from LAU (Brown wire)
    elif d2r_sel_i == 2:
        rf_wd_o = pc_plus_4_i     # Path from pc_plus_4 (Green wire)
    else:
        rf_wd_o = 0               # Safety/Default

    # Logic Analyzer Trace for Debugging
    print ("\n**** Inside rf_wb_mux ******")
    print(f"INPUTS  | alu_res: 0x{alu_res_i:08x} | lau_res: 0x{lau_res_i:08x}\n"
          f"        | pc+4:    0x{pc_plus_4_i:08x} | d2r_sel: {d2r_sel_i}\n"
          f"OUTPUTS | rf_wd_o:  0x{rf_wd_o:08x}")

    return rf_wd_o

# ==============================================================================
# TEST 1: The Latch / 'X' State Visual Demonstration
# ==============================================================================
@cocotb.test()
async def test_mux_x_state(dut):
    """Test how the hardware handles unknown X states on the select line."""
    
    # Set standard data
    dut.alu_res_i.value   = 0xFFFFFFFF
    dut.lau_res_i.value   = 0x00000000
    dut.pc_plus_4_i.value = 0x0000000F
    
    # Drive valid select
    dut.d2r_sel_i.value = 0
    await Timer(1, unit="ns")
    
    # Inject X state
    dut.d2r_sel_i.value = LogicArray("XX")
    await Timer(1, unit="ns")

# ==============================================================================
# TEST 2: The Golden Model & Boundary Validation
# ==============================================================================
@cocotb.test()
async def golden_model_mux_test(dut):
    """Verify all valid select lines against the Python Golden Model using Max/Min boundaries."""
    
    # Define our strict maximum and minimum boundaries for 32-bit architecture
    MAX_VAL = 0xFFFFFFFF
    MIN_VAL = 0x00000000
    
    # Test Vectors: (alu_res, lau_res, pc_plus_4, select_line)
    test_cases = [
        (MAX_VAL, MIN_VAL, MIN_VAL, 0), # Max boundary on ALU
        (MIN_VAL, MAX_VAL, MIN_VAL, 1), # Max boundary on LAU
        (MIN_VAL, MIN_VAL, MAX_VAL, 2), # Max boundary on PC+4
        (0xAAAAAAAA, 0x55555555, 0x12345678, 3)  # Invalid select line (should hit default)
    ]

    for alu, lau, pc4, sel in test_cases:
        # 1. Drive the physical SystemVerilog pins
        dut.alu_res_i.value   = alu
        dut.lau_res_i.value   = lau
        dut.pc_plus_4_i.value = pc4
        dut.d2r_sel_i.value   = sel
        
        # 2. Wait for combinational logic to propagate
        await Timer(1, unit="ns")
        
        # 3. Ask the Python Oracle what the answer should be
        expected_output = module_rf_wb_mux(alu, lau, pc4, sel)
        
        # 4. Read the physical hardware pin
        actual_output = int(dut.rf_wd_o.value)
        
        # 5. Automatically compare!
        assert actual_output == expected_output, \
            f"FAIL! Hardware produced {hex(actual_output)}, but Oracle expected {hex(expected_output)}"
