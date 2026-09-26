import random
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

# Import your Golden Model
from osoc1_core_uarch import DataMemory 

@cocotb.test()
async def automated_data_mem_wrapper_test(dut):
    """Verify Wrapper, Word-Alignment, Byte Enables, and Boundaries."""
    
    cocotb.start_soon(Clock(dut.clk_i, 10, unit="ns").start())
    
    golden_dmem = DataMemory()
    
    MAX_VAL = 0xFFFFFFFF
    MIN_VAL = 0x00000000
    
    # Safely cast the hardware parameter to an integer for Cocotb 2.0+
    HW_DEPTH = int(dut.DEPTH.value)

    test_cases = [
        # --- Absolute Hardware Boundaries ---
        ("Full Word Write MAX Limit",     0x00000000, MAX_VAL, 0b1111),
        ("Full Word Write MIN Limit",     0x00000004, MIN_VAL, 0b1111),
        
        # --- Byte Enable (Strobe) Boundary Testing ---
        ("Byte 0 (sb) Max Squeeze",       0x00000008, MAX_VAL, 0b0001),
        ("Byte 1 Max Squeeze",            0x00000008, MAX_VAL, 0b0010),
        ("Halfword (sh) Max Squeeze",     0x0000000C, MAX_VAL, 0b0011),
        ("Upper Halfword Max Squeeze",    0x0000000C, MAX_VAL, 0b1100),
        
        # --- Word Alignment Edge Cases ---
        ("Unaligned Full Write (PC=5)",   0x00000005, 0xAAAAAAAA, 0b1111),
        ("Unaligned Fetch (PC=7)",        0x00000007, 0x00000000, 0b0000),
        
        # --- Hardware Out-of-Bounds Protection ---
        ("Max Boundary Out-of-Bounds",    MAX_VAL,    MAX_VAL,    0b1111),
    ]

    # Add Random Fuzzing for Byte Enables
    for i in range(10):
        test_cases.append((
            f"Random Fuzz Write {i}",
            random.randint(0, (HW_DEPTH * 4) - 1),  
            random.randint(MIN_VAL, MAX_VAL),       
            random.randint(0, 15)                   
        ))

    dut._log.info("Starting Data Memory Wrapper Verification...")
    await RisingEdge(dut.clk_i)

    for desc, addr, wdata, wstrobe in test_cases:
        
        # =====================================================================
        # PHASE 1: SEQUENTIAL WRITE
        # =====================================================================
        dut.we_i.value   = wstrobe
        dut.addr_i.value = addr
        dut.wd_i.value   = wdata
        
        golden_dmem.write(addr, wdata, wstrobe)

        await RisingEdge(dut.clk_i)

        # =====================================================================
        # PHASE 2: COMBINATIONAL READ VERIFICATION
        # =====================================================================
        dut.we_i.value = 0
        
        await Timer(1, unit="ns")

        hw_rd  = int(dut.rd_o.value) & MAX_VAL
        exp_rd = golden_dmem.read(addr) & MAX_VAL

        if (addr // 4) >= HW_DEPTH:
            exp_rd = 0

        assert hw_rd == exp_rd, \
            f"FAIL ({desc})! \nExp: 0x{exp_rd:08X} \nAct: 0x{hw_rd:08X} \nAddr: 0x{addr:08X} \nStrobe: {bin(wstrobe)}"
            
        dut._log.info(f"PASS: {desc} | Addr: 0x{addr:08X} | Data: 0x{hw_rd:08X}")

    dut._log.info("SUCCESS: Data Memory Wrapper passed all byte strokes and bounds!")
