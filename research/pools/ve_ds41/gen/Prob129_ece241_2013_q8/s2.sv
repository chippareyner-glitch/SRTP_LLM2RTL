module TopModule (
    input  clk,
    input  aresetn,
    input  x,
    output z
);

    localparam S0  = 2'b00;
    localparam S1  = 2'b01;
    localparam S10 = 2'b10;

    reg [1:0] state;

    always @(posedge clk or negedge aresetn) begin
        if (!aresetn) begin
            state <= S0;
        end
        else begin
            case (state)
                S0: begin
                    if (x)
                        state <= S1;
                    else
                        state <= S0;
                end
                S1: begin
                    if (x)
                        state <= S1;
                    else
                        state <= S10;
                end
                S10: begin
                    if (x)
                        state <= S1;
                    else
                        state <= S0;
                end
                default: state <= S0;
            endcase
        end
    end

    assign z = (state == S10) && x;

endmodule
