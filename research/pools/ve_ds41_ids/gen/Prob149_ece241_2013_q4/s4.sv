module TopModule (
    input  logic clk,
    input  logic reset,
    input  logic [2:0] s,
    output logic fr2,
    output logic fr1,
    output logic fr0,
    output logic dfr
);

    logic [1:0] state;      // current water level: 00, 01, 10, 11
    logic [1:0] new_level;
    logic       dfr_reg;
    logic       next_dfr;

    // Determine new water level from sensors
    always_comb begin
        case (s)
            3'b111: new_level = 2'b11; // above s[2]
            3'b011: new_level = 2'b10; // between s[2] and s[1]
            3'b001: new_level = 2'b01; // between s[1] and s[0]
            3'b000: new_level = 2'b00; // below s[0]
            default: new_level = 2'b00; // default to lowest level
        endcase
    end

    // Compute next value of dfr
    always_comb begin
        if (new_level == 2'b00)
            next_dfr = 1'b1;          // below lowest sensor: max flow
        else if (new_level == 2'b11)
            next_dfr = 1'b0;          // above highest sensor: zero flow
        else
            next_dfr = (state < new_level) ? 1'b1 : 1'b0; // increase if previous < current
    end

    // Synchronous state and dfr update with active-high reset
    always_ff @(posedge clk) begin
        if (reset) begin
            state   <= 2'b00;
            dfr_reg <= 1'b1;
        end else begin
            state   <= new_level;
            dfr_reg <= next_dfr;
        end
    end

    // Nominal flow rate outputs based on current water level
    assign fr0 = (state != 2'b11) ? 1'b1 : 1'b0; // asserted for levels 0,1,2
    assign fr1 = (state <  2'b10) ? 1'b1 : 1'b0; // asserted for levels 0,1
    assign fr2 = (state == 2'b00) ? 1'b1 : 1'b0; // asserted for level 0
    assign dfr = dfr_reg;

endmodule
