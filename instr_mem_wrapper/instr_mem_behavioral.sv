module instr_mem_behavioral #(
    parameter int DEPTH = 1024
)(
    input  logic [31:0] pc_i,
    output logic [31:0] instr_o
);

    // The physical memory array (Word addressed)
    logic [31:0] memory_array [0:DEPTH-1];

    // Initialize memory with hex firmware at time zero
    initial begin
        $readmemh("firmware.hex", memory_array);
    end

    // =========================================================================
    // Asynchronous Combinational Fetch
    // =========================================================================
    // Shift PC right by 2 to convert Byte-Address to Word-Address
    wire [29:0] word_addr = pc_i[31:2];

    // Fetch instruction. If PC is out of bounds, return 0 (safe fallback)
    assign instr_o = (word_addr < DEPTH) ? memory_array[word_addr] : 32'h00000000;

endmodule
