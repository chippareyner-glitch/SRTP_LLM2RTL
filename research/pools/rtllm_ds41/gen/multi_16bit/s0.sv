module multi_16bit (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        start,
    input  wire [15:0] ain,
    input  wire [15:0] bin,
    output wire [31:0] yout,
    output wire        done
);

    reg [4:0]  i;        // shift count register
    reg [15:0] areg;     // multiplicand register
    reg [15:0] breg;     // multiplier register
    reg [31:0] yout_r;   // product register
    reg        done_r;   // multiplication completion flag

    assign yout = yout_r;
    assign done = done_r;

    //------------------------------------------------------------------
    // Shift count register
    //------------------------------------------------------------------
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            i <= 5'd0;
        else if (start && (i < 5'd17))
            i <= i + 5'd1;
        else if (!start)
            i <= 5'd0;
    end

    //------------------------------------------------------------------
    // Multiplication completion flag
    //------------------------------------------------------------------
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            done_r <= 1'b0;
        else if (i == 5'd16)
            done_r <= 1'b1;
        else if (i == 5'd17)
            done_r <= 1'b0;
    end

    //------------------------------------------------------------------
    // Shift and accumulate operation
    //------------------------------------------------------------------
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            areg   <= 16'd0;
            breg   <= 16'd0;
            yout_r <= 32'd0;
        end
        else if (start) begin
            if (i == 5'd0) begin
                areg <= ain;
                breg <= bin;
            end
            else if (i < 5'd17) begin
                if (areg[i - 1])
                    yout_r <= yout_r + (breg << (i - 1));
            end
        end
    end

endmodule
