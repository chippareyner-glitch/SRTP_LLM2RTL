module TopModule (
    input  logic clk,
    input  logic reset,
    input  logic slowena,
    output logic [3:0] q
);

    logic [3:0] count; // count[3] is MSB, count[0] is LSB

    always_ff @(posedge clk) begin
        if (reset) begin
            count <= 4'd0;
        end
        else if (slowena) begin
            if (count == 4'd9)
                count <= 4'd0;
            else
                count <= count + 4'd1;
        end
    end

    // q[0] is MSB and q[3] is LSB
    assign q = {count[0], count[1], count[2], count[3]};

endmodule
