import random
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

# Import your Golden Model directly from your central uArch file
from osoc1_core_uarch import RegisterFile 

@cocotb.test()
async def automated_reg_file_test(dut):
    """Verify combinational reads, sequential writes, and data boundaries."""
    
    # 1. Start the Background Clock (10 ns period)
    # Note: cocotb 2.0 uses 'unit' instead of 'units'. Updated here to clear your deprecation warning!
    cocotb.start_soon(Clock(dut.clk_i, 10, unit="ns").start())
    
    # Instantiate the Golden Model from your imported class
    golden_rf = RegisterFile()
    
    MAX_VAL = 0xFFFFFFFF
    MIN_VAL = 0x00000000

    # =========================================================================
    # NEW: HARDWARE SYNCHRONIZATION PHASE (The X-State Fix)
    # =========================================================================
    dut._log.info("Scrubbing hardware memory to eliminate X-states...")
    for i in range(1, 32):
        dut.we_i.value = 1
        dut.rd_i.value = i
        dut.wd_i.value = 0
        await RisingEdge(dut.clk_i)
        
    dut.we_i.value = 0 # Turn off write enable after scrubbing
    await RisingEdge(dut.clk_i)
    dut._log.info("Hardware memory synchronized to 0x00000000.")

    # =========================================================================
    # TEST MATRIX EXECUTION
    # =========================================================================
    # Test Matrix: (Description, WE, Dest_Reg, Write_Data, Read_Reg1, Read_Reg2)
    test_cases = [
        # --- The Safety Gate Boundaries ---
        ("Attempt Write MAX to x0",    1, 0,  MAX_VAL, 0, 0),
        ("Attempt Write MIN to x0",    1, 0,  MIN_VAL, 0, 0),
        
        # --- Absolute Data Boundaries ---
        ("Write MAX_VAL to x1",        1, 1,  MAX_VAL, 1, 0),
        ("Write MIN_VAL to x31",       1, 31, MIN_VAL, 31, 0),
        
        # --- Write Enable (WE) Limits ---
        ("Disabled Write (WE=0)",      0, 5,  0xDEADBEEF, 5, 0),
        
        # --- Dual Port Simultaneous Reads ---
        ("Read x1(MAX) and x31(MIN)",  0, 0,  0, 1, 31),
    ]

    # Add Random Fuzzing
    for i in range(15):
        test_cases.append((
            f"Random Fuzz Write {i}",
            1,                                # WE = 1
            random.randint(1, 31),            # Valid destination registers
            random.randint(MIN_VAL, MAX_VAL), # Random 32-bit data
            random.randint(0, 31),            # Random Read 1
            random.randint(0, 31)             # Random Read 2
        ))

    dut._log.info("Starting Register File Verification...")

    # Wait for initial clock edge alignment
    await RisingEdge(dut.clk_i)

    for desc, we, rd_addr, wd_data, rs1_addr, rs2_addr in test_cases:
        
        # =====================================================================
        # PHASE 1: SETUP & SEQUENTIAL WRITE
        # =====================================================================
        dut.we_i.value  = we
        dut.rd_i.value  = rd_addr
        dut.wd_i.value  = wd_data
        
        # Update Python Golden Model
        golden_rf.write(rd_addr, wd_data, we)

        # Wait for the clock edge to physically lock the data into the flip-flops
        await RisingEdge(dut.clk_i)
        
        # =====================================================================
        # PHASE 2: ASYNCHRONOUS COMBINATIONAL READ
        # =====================================================================
        # Drive the read addresses AFTER the clock edge
        dut.rs1_i.value = rs1_addr
        dut.rs2_i.value = rs2_addr
        
        # Add a tiny 1ns delay to allow combinational mux paths to settle
        await Timer(1, unit="ns")

        # Get Golden Model Combinational Reads
        exp_rd1 = golden_rf.read_rs1(rs1_addr)
        exp_rd2 = golden_rf.read_rs2(rs2_addr)

        # Read Hardware Simulator (Clamped to 32-bit boundary)
        hw_rd1 = int(dut.rd1_o.value) & MAX_VAL
        hw_rd2 = int(dut.rd2_o.value) & MAX_VAL

        # =====================================================================
        # PHASE 3: ASSERTIONS
        # =====================================================================
        assert hw_rd1 == exp_rd1, \
            f"FAIL ({desc}) RD1! Exp: 0x{exp_rd1:08X} | Act: 0x{hw_rd1:08X} at Addr: {rs1_addr}"
        
        assert hw_rd2 == exp_rd2, \
            f"FAIL ({desc}) RD2! Exp: 0x{exp_rd2:08X} | Act: 0x{hw_rd2:08X} at Addr: {rs2_addr}"

        dut._log.info(f"PASS: {desc} | RD1: 0x{hw_rd1:08X} | RD2: 0x{hw_rd2:08X}")

    dut._log.info("SUCCESS: Register File bounds and asynchronous reads verified!")
