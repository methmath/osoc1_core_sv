module lau (
    input  logic [31:0] mem_data_i,
    input  logic        adrs_1_i,
    input  logic        adrs_0_i,
    input  logic [2:0]  funct3_i,

    output logic [31:0] aligned_data_o
);

    logic [31:0] stage1_mux_out;
    logic [31:0] stage2_mux_out;

    // Cascaded right-shift multiplexers
    assign stage1_mux_out = adrs_1_i ? (mem_data_i >> 16) : mem_data_i;
    assign stage2_mux_out = adrs_0_i ? (stage1_mux_out >> 8) : stage1_mux_out;

    // Extract data slices and sign bits
    wire [7:0]  s2_byte      = stage2_mux_out[7:0];
    wire        s2_byte_sign = stage2_mux_out[7];
    wire [15:0] s2_hw        = stage2_mux_out[15:0];
    wire        s2_hw_sign   = stage2_mux_out[15];

    // Mask unit and sign/zero extension
    always_comb begin
        aligned_data_o = '0;

        case (funct3_i)

            // LB - Load Byte Signed
            3'b000: begin
                aligned_data_o = {{24{s2_byte_sign}}, s2_byte};
            end

            // LH - Load Halfword Signed
            3'b001: begin
                aligned_data_o = {{16{s2_hw_sign}}, s2_hw};
            end

            // LW - Load Word
            3'b010: begin
                aligned_data_o = stage2_mux_out;
            end

            // LBU - Load Byte Unsigned
            3'b100: begin
                aligned_data_o = {24'b0, s2_byte};
            end

            // LHU - Load Halfword Unsigned
            3'b101: begin
                aligned_data_o = {16'b0, s2_hw};
            end

            default: aligned_data_o = '0;

        endcase
    end

endmodule
