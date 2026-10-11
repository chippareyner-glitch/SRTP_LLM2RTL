module instr_reg (
    input  logic       clk,
    input  logic       rst,
    input  logic [1:0] fetch,
    input  logic [7:0] data,
    output logic [2:0] ins,
    output logic [4:0] ad1,
    output logic [7:0] ad2
);

    logic [7:0] ins_p1;
    logic [7:0] ins_p2;

    always_ff @(posedge clk) begin
        if (!rst) begin
            ins_p1 <= 8'b0;
            ins_p2 <= 8'b0;
            ins    <= 3'b0;
            ad1    <= 5'b0;
            ad2    <= 8'b0;
        end else begin
            case (fetch)
                2'b01: ins_p1 <= data;
                2'b10: ins_p2 <= data;
                default: begin
                    ins_p1 <= ins_p1;
                    ins_p2 <= ins_p2;
                end
            endcase

            // Registered outputs: one clock cycle after internal registers update
            ins <= ins_p1[7:5];
            ad1 <= ins_p1[4:0];
            ad2 <= ins_p2;
        end
    end

endmodule
