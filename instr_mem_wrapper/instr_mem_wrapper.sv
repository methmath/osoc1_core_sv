module instr_mem_wrapper #(
    parameter int DEPTH = 1024
)(
    // =========================================================================
    // CPU-Facing Interface
    // =========================================================================
    input  logic        clk_i, // Required for future physical macro timing
    input  logic [31:0] pc_i,
    output logic [31:0] instr_o
);

`ifdef USE_OPENRAM

    // =========================================================================
    // Physical Design: OpenRAM ROM/SRAM Instantiation
    // =========================================================================
    logic csb0;
    assign csb0 = 1'b0; // Chip Select Bar (Always active for fetching)

    // Example instantiation for a generated physical macro
    sram_4kb_32b_openram_rom u_physical_macro (
        .clk0   (clk_i),
        .csb0   (csb0),
        .addr0  (pc_i[11:2]), // Word alignment
        .dout0  (instr_o)
    );

`else

    // =========================================================================
    // Simulation: Behavioral Model Instantiation
    // =========================================================================
    instr_mem_behavioral #(
        .DEPTH(DEPTH)
    ) u_behav_macro (
        .pc_i    (pc_i),
        .instr_o (instr_o)
    );

`endif

endmodule
