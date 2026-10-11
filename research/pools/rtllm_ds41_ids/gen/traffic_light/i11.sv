module traffic_light (
    input wire rst_n,
    input wire clk,
    input wire pass_request,
    output wire [7:0] clock,
    output reg red,
    output reg yellow,
    output reg green
);

    localparam idle      = 2'b00;
    localparam s1_red    = 2'b01;
    localparam s2_yellow = 2'b10;
    localparam s3_green  = 2'b11;

    reg [7:0] cnt;
    reg [1:0] state;
    reg p_red, p_yellow, p_green;

    assign clock = cnt;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state    <= idle;
            cnt      <= 8'd10;
            p_red    <= 1'b0;
            p_yellow <= 1'b0;
            p_green  <= 1'b0;
        end else begin
            case (state)
                idle: begin
                    state    <= s1_red;
                    cnt      <= 8'd10;
                    p_red    <= 1'b1;
                    p_yellow <= 1'b0;
                    p_green  <= 1'b0;
                end
                s1_red: begin
                    if (cnt == 8'd1) begin
                        state    <= s3_green;
                        cnt      <= 8'd60;
                        p_red    <= 1'b0;
                        p_yellow <= 1'b0;
                        p_green  <= 1'b1;
                    end else begin
                        state    <= s1_red;
                        cnt      <= cnt - 1'b1;
                        p_red    <= 1'b1;
                        p_yellow <= 1'b0;
                        p_green  <= 1'b0;
                    end
                end
                s2_yellow: begin
                    if (cnt == 8'd1) begin
                        state    <= s1_red;
                        cnt      <= 8'd10;
                        p_red    <= 1'b1;
                        p_yellow <= 1'b0;
                        p_green  <= 1'b0;
                    end else begin
                        state    <= s2_yellow;
                        cnt      <= cnt - 1'b1;
                        p_red    <= 1'b0;
                        p_yellow <= 1'b1;
                        p_green  <= 1'b0;
                    end
                end
                s3_green: begin
                    if (pass_request) begin
                        state    <= s3_green;
                        cnt      <= 8'd10;
                        p_red    <= 1'b0;
                        p_yellow <= 1'b0;
                        p_green  <= 1'b1;
                    end else if (cnt == 8'd1) begin
                        state    <= s2_yellow;
                        cnt      <= 8'd5;
                        p_red    <= 1'b0;
                        p_yellow <= 1'b1;
                        p_green  <= 1'b0;
                    end else begin
                        state    <= s3_green;
                        cnt      <= cnt - 1'b1;
                        p_red    <= 1'b0;
                        p_yellow <= 1'b0;
                        p_green  <= 1'b1;
                    end
                end
                default: begin
                    state    <= idle;
                    cnt      <= 8'd10;
                    p_red    <= 1'b0;
                    p_yellow <= 1'b0;
                    p_green  <= 1'b0;
                end
            endcase
        end
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            red    <= 1'b0;
            yellow <= 1'b0;
            green  <= 1'b0;
        end else begin
            red    <= p_red;
            yellow <= p_yellow;
            green  <= p_green;
        end
    end

endmodule
