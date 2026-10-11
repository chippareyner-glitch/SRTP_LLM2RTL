module multi_16bit (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        start,
    input  wire [15:0] ain,
    input  wire [15:0] bin,
    output wire [31:0] yout,
    output reg         done
);

    reg [4:0]  i;
    reg [15:0] areg;
    reg [15:0] breg;
    reg [31:0] yout_r;

    assign yout = yout_r;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            i      <= 5'd0;
            done   <= 1'b0;
            areg   <= 16'd0;
            breg   <= 16'd0;
            yout_r <= 32'd0;
        end
        else begin
            /* Multiplication completion flag generation */
            if (i == 5'd16)
                done <= 1'b1;
            else if (i == 5'd17)
                done <= 1'b0;

            /* Data bit control (shift counter) */
            if (start && (i < 5'd17))
                i <= i + 5'd1;
            else if (!start)
                i <= 5'd0;

            /* Shift and accumulate */
            if (start) begin
                if (i == 5'd0) begin
                    areg   <= ain;
                    breg   <= bin;
                    yout_r <= 32'd0;
                end
                else if ((i > 5'd0) && (i < 5'd17)) begin
                    if (areg[i - 5'd1])
                        yout_r <= yout_r + (breg << (i - 5'd1));
                end
            end
        end
    end

endmodule
