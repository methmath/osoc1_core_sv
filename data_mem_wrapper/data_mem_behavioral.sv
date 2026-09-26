module data_mem_behavioral #(
    parameter int DEPTH = 1024 
)(
    input  logic        clk_i,
    input  logic [3:0]  we_i,       // 4-bit Write Strobe
    input  logic [31:0] addr_i,     // Full 32-bit Address
    input  logic [31:0] wd_i,       // Write Data

    output logic [31:0] rd_o        // Read Data
);

    // The physical word-addressed memory array
    logic [31:0] memory_array [0:DEPTH-1];

    // =========================================================================
    // X-State Scrubbing (Simulation Only)
    // =========================================================================
    // Instantly zero-out the memory array to prevent Cocotb conversion crashes.
    integer i;
    initial begin
        for (i = 0; i < DEPTH; i = i + 1) begin
            memory_array[i] = 32'h00000000;
        end
    end

    // =========================================================================
    // Word Alignment & Asynchronous Read
    // =========================================================================
    wire [29:0] word_addr = addr_i[31:2];

    assign rd_o = (word_addr < DEPTH) ? memory_array[word_addr] : 32'h00000000;

    // =========================================================================
    // Synchronous Write with Byte Enables
    // =========================================================================
    always_ff @(posedge clk_i) begin
        if (word_addr < DEPTH) begin
            if (we_i[0]) memory_array[word_addr][7:0]   <= wd_i[7:0];
            if (we_i[1]) memory_array[word_addr][15:8]  <= wd_i[15:8];
            if (we_i[2]) memory_array[word_addr][23:16] <= wd_i[23:16];
            if (we_i[3]) memory_array[word_addr][31:24] <= wd_i[31:24];
        end
    end

endmodule
