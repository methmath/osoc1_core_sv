import random
import cocotb
from cocotb.triggers import Timer
from osoc1_core_uarch import module_ctrl

@cocotb.test()
async def automated_ctrl_test(dut):
    """Verify Controller Matrix across legal instructions and undefined boundaries."""

    # Format: (Description, Opcode, Funct3, Funct7)
    test_cases = [
        # --- Standard Instruction Checks ---
        ("R-Type ADD",  51,  0, 0),
        ("R-Type SUB",  51,  0, 32),
        ("I-Type ADDI", 19,  0, 0),
        ("I-Type SRAI", 19,  5, 32),
        ("LOAD",        3,   2, 0),
        ("STORE",       35,  2, 0),
        ("BRANCH",      99,  0, 0),
        ("LUI",         55,  0, 0),
        ("AUIPC",       23,  0, 0),
        ("JALR",        103, 0, 0),
        ("JAL",         111, 0, 0),

        # --- Absolute Boundaries & Edge Cases ---
        ("Absolute Min Inputs (All 0s)", 0, 0, 0),
        ("Absolute Max Inputs (All 1s)", 127, 7, 127),
        ("Illegal Opcode",               120, 3, 16),
    ]

    # Add Random Fuzzing for unexpected combinations
    for i in range(15):
        test_cases.append((
            f"Random Fuzz {i}",
            random.randint(0, 127),
            random.randint(0, 7),
            random.randint(0, 127)
        ))

    dut._log.info("Starting CPU Controller Matrix Verification...")

    for desc, op, f3, f7 in test_cases:
        # Drive input ports
        dut.opcode_i.value = op
        dut.funct3_i.value = f3
        dut.funct7_i.value = f7

        await Timer(1, unit="ns")

        # Get Golden Result tuple from Python Model
        # Returns:
        # (is_cond_branch_o, is_jal_o, is_jalr_o, imm_src_o,
        #  alu_src1_ctrl_o, alu_src2_ctrl_o, alu_ctrl_o,
        #  datamem_re_o, datamem_we_o, dataMem2Reg_o, regfile_we_o)
        exp = module_ctrl(op, f3, f7, DEBUG_MODE=False)

        # Read Hardware
        hw_is_cond    = int(dut.is_cond_branch_o.value)
        hw_is_jal     = int(dut.is_jal_o.value)
        hw_is_jalr    = int(dut.is_jalr_o.value)
        hw_imm_src    = int(dut.imm_src_o.value)
        hw_alu_src1   = int(dut.alu_src1_ctrl_o.value)
        hw_alu_src2   = int(dut.alu_src2_ctrl_o.value)
        hw_alu_ctrl   = int(dut.alu_ctrl_o.value)
        hw_dmem_re    = int(dut.datamem_re_o.value)
        hw_dmem_we    = int(dut.datamem_we_o.value)
        hw_m2reg      = int(dut.dataMem2Reg_o.value)
        hw_rf_we      = int(dut.regfile_we_o.value)

        # Assertions
        assert hw_is_cond  == exp[0],  f"IS_COND Fail on {desc}"
        assert hw_is_jal   == exp[1],  f"IS_JAL Fail on {desc}"
        assert hw_is_jalr  == exp[2],  f"IS_JALR Fail on {desc}"
        assert hw_imm_src  == exp[3],  f"IMM_SRC Fail on {desc}"
        assert hw_alu_src1 == exp[4],  f"ALU_SRC1 Fail on {desc}"
        assert hw_alu_src2 == exp[5],  f"ALU_SRC2 Fail on {desc}"
        assert hw_alu_ctrl == exp[6],  f"ALU_CTRL Fail on {desc}"
        assert hw_dmem_re  == exp[7],  f"DMEM_RE Fail on {desc}"
        assert hw_dmem_we  == exp[8],  f"DMEM_WE Fail on {desc}"
        assert hw_m2reg    == exp[9],  f"M2REG Fail on {desc}"
        assert hw_rf_we    == exp[10], f"RF_WE Fail on {desc}"

        dut._log.info(f"PASS: {desc} mapped securely.")

    dut._log.info(
        "SUCCESS: All CPU Control states and default edge limits are fully verified!"
    )
