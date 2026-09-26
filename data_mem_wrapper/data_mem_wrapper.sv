module data_mem_wrapper #(
    parameter int DEPTH = 1024
)(
    // =========================================================================
    // CPU-Facing Interface
    // =========================================================================
    input  logic        clk_i,
    input  logic [3:0]  we_i,
    input  logic [31:0] addr_i,
    input  logic [31:0] wd_i,
    output logic [31:0] rd_o
);

`ifdef USE_OPENRAM

    // Physical Design: OpenRAM Instantiation
    logic csb0;
    logic web0;
    
    assign csb0 = 1'b0;          
    assign web0 = ~(|we_i);      

    sram_4kb_32b_openram u_physical_macro (
        .clk0   (clk_i),
        .csb0   (csb0),
        .web0   (web0),
        .wmask0 (we_i),          
        .addr0  (addr_i[11:2]),  
        .din0   (wd_i),          
        .dout0  (rd_o)
    );

`else

    // Simulation: Behavioral Model Instantiation
    data_mem_behavioral #(
        .DEPTH(DEPTH)
    ) u_behav_macro (
        .clk_i  (clk_i),
        .we_i   (we_i),
        .addr_i (addr_i),
        .wd_i   (wd_i),
        .rd_o   (rd_o)
    );

`endif

endmodule
