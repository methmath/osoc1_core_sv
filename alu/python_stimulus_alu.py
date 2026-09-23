import cocotb
from cocotb.triggers import Timer
import random
import sys
import os

# Append parent directory so we can import the golden model
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from osoc1_core_uarch import module_alu

@cocotb.test()
async def test_alu_boundaries(dut):
    """Test ALU against strict maximum, minimum, and random boundary checks."""
    
    # -------------------------------------------------------------
    # MANDATORY MAXIMUM AND MINIMUM NUMBER CHECKS
    # These must be evaluated for every instruction going forward.
    # -------------------------------------------------------------
    boundary_values = [
        0x00000000, # Absolute Minimum (Unsigned/Signed Positive)
        0xFFFFFFFF, # Maximum Unsigned / Signed -1
        0x7FFFFFFF, # Maximum Signed Positive (+2.14B)
        0x80000000, # Minimum Signed Negative (-2.14B)
        0x00000001, # Standard +1
        0xFFFFFFFE  # Standard -2
    ]
    
    # Inject randomized stimulus for broader datapath coverage
    for _ in range(10):
        boundary_values.append(random.randint(0, 0xFFFFFFFF))

    # Opcode mapping matching cpu_sv_package.sv
    ops = {
        0: "ADD", 1: "SUB", 2: "SLT", 3: "SLTU", 4: "SLL", 
        5: "XOR", 6: "SRL", 7: "SRA", 8: "OR", 9: "AND"
    }

    error_count = 0

    for op_code, op_name in ops.items():
        for a in boundary_values:
            for b in boundary_values:
                
                # Drive the SystemVerilog hardware inputs
                dut.src1_i.value = a
                dut.src2_i.value = b
                dut.alu_op_i.value = op_code
                
                # Allow combinational logic to settle
                await Timer(1, unit="ns")
                
                # Sample the physical hardware output wires
                hw_res   = int(dut.res_o.value)
                hw_z     = int(dut.z_o.value)
                hw_s     = int(dut.s_o.value)
                hw_ovfl  = int(dut.ovfl_o.value)
                hw_carry = int(dut.carry_o.value)
                
                # Fetch expected results from the centralized Python Golden Model
                exp_res, exp_z, exp_s, exp_ovfl, exp_carry = module_alu(a, b, op_code)
                
                # Compare Hardware vs. Golden Model
                if hw_res != exp_res or hw_z != exp_z or hw_s != exp_s or \
                   hw_ovfl != exp_ovfl or hw_carry != exp_carry:
                    
                    dut._log.error(f"FAIL at {op_name} (A={hex(a)}, B={hex(b)})")
                    dut._log.error(f"  EXPECTED: Res={hex(exp_res)}, Z={exp_z}, S={exp_s}, V={exp_ovfl}, C={exp_carry}")
                    dut._log.error(f"  HARDWARE: Res={hex(hw_res)}, Z={hw_z}, S={hw_s}, V={hw_ovfl}, C={hw_carry}")
                    error_count += 1

    assert error_count == 0, f"Test failed with {error_count} boundary errors."
    dut._log.info("SUCCESS! All maximum and minimum boundary checks passed.")
