import random
import cocotb
from cocotb.triggers import Timer
from osoc1_core_uarch import module_alu_in_muxes, get_max


@cocotb.test()
async def automated_alu_in_muxes_test(dut):
    """Verify alu_in_muxes using max/min boundaries and random inputs."""

    MAX_32 = get_max(32)
    MAX_2 = get_max(2)
    MAX_1 = get_max(1)
    MIN_VAL = 0

    test_cases = [
        (MIN_VAL, MIN_VAL, MIN_VAL, MIN_VAL, MIN_VAL, MIN_VAL),
        (MAX_32, MAX_32, MAX_32, MAX_32, MAX_2, MAX_1)
    ]

    NUM_RANDOM_TESTS = 10

    for _ in range(NUM_RANDOM_TESTS):
        test_cases.append((
            random.randint(MIN_VAL, MAX_32),
            random.randint(MIN_VAL, MAX_32),
            random.randint(MIN_VAL, MAX_32),
            random.randint(MIN_VAL, MAX_32),
            random.randint(MIN_VAL, MAX_2),
            random.randint(MIN_VAL, MAX_1)
        ))

    dut._log.info("Starting alu_in_muxes Verification...")
    dut._log.info("-" * 80)

    for pc_curr_i, rs1_val_i, rs2_val_i, imm_i, s1_sel_i, s2_sel_i in test_cases:

        dut.pc_curr_i.value = pc_curr_i
        dut.rs1_val_i.value = rs1_val_i
        dut.rs2_val_i.value = rs2_val_i
        dut.imm_i.value = imm_i
        dut.s1_sel_i.value = s1_sel_i
        dut.s2_sel_i.value = s2_sel_i

        await Timer(1, unit="ns")

        expected_results = module_alu_in_muxes(
            pc_curr_i,
            rs1_val_i,
            rs2_val_i,
            imm_i,
            s1_sel_i,
            s2_sel_i
        )

        exp_a, exp_b = expected_results

        act_a = int(dut.alu_a_o.value)
        act_b = int(dut.alu_b_o.value)

        assert act_a == exp_a, \
            f"FAIL MUX A! Expected: {exp_a} | Actual: {act_a}"

        assert act_b == exp_b, \
            f"FAIL MUX B! Expected: {exp_b} | Actual: {act_b}"

    dut._log.info("-" * 80)
    dut._log.info("SUCCESS: Boundary and random tests passed for alu_in_muxes!")
