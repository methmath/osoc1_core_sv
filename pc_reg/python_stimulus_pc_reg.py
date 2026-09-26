import random
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

@cocotb.test()
async def automated_pc_reg_test(dut):
    """Verify the PC Register with strict max/min boundaries and reset behavior."""

    # 1. Start the clock (10 ns period)
    cocotb.start_soon(Clock(dut.clk_i, 10, units="ns").start())

    MAX_VAL = 0xFFFFFFFF
    MIN_VAL = 0x00000000

    # 2. Asynchronous Reset Sequence
    dut._log.info("Applying active-low reset...")
    dut.rst_ni.value = 0
    # Drive maximum garbage data to prove reset overrides the D-input
    dut.pc_d_i.value = MAX_VAL

    # Hold reset for a bit, then release
    await Timer(15, units="ns")

    # Verify Reset State (Absolute Minimum / Boot Address)
    hw_reset_val = int(dut.pc_q_o.value) & MAX_VAL
    assert hw_reset_val == MIN_VAL, f"FAIL! PC did not reset to 0x00000000, got 0x{hw_reset_val:08X}"
    dut._log.info("PASS: Reset cleanly forced PC to absolute minimum boundary (0x00000000)")

    # Release reset and align to the next clock edge
    dut.rst_ni.value = 1
    await RisingEdge(dut.clk_i)

    # 3. Test Matrix: (Description, D-Input)
    test_cases = [
        ("Standard Address Step",     0x00001004),
        ("Standard Address Jump",     0x00002000),
        ("Absolute Maximum Boundary", MAX_VAL),
        ("Absolute Minimum Boundary", MIN_VAL),
        ("Alternating Bits (0x55..)", 0x55555555),
        ("Alternating Bits (0xAA..)", 0xAAAAAAAA),
    ]

    # Add Random Fuzzing
    for i in range(10):
        test_cases.append((f"Random Fuzz {i}", random.randint(MIN_VAL, MAX_VAL)))

    dut._log.info("Starting PC Register sequential verification...")

    for desc, d_val in test_cases:
        # Drive D-input (Setup phase)
        dut.pc_d_i.value = d_val

        # Wait for the next rising edge to capture data
        await RisingEdge(dut.clk_i)

        # Add a tiny delay to simulate clock-to-Q propagation before reading
        await Timer(1, units="ns")

        # Read Q-output (Hardware)
        hw_q = int(dut.pc_q_o.value) & MAX_VAL

        assert hw_q == d_val, f"FAIL ({desc})! Exp: 0x{d_val:08X} | Act: 0x{hw_q:08X}"
        dut._log.info(f"PASS: {desc} | pc_q_o: 0x{hw_q:08X}")


    dut._log.info("SUCCESS: All sequential captures and boundary tests passed!")
