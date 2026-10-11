module traffic_light (
    input  logic       rst_n,
    input  logic       clk,
    input  logic       pass_request,
    output wire [7:0]  clock,
    output logic       red,
    output logic       yellow,
    output logic       green
);

    parameter [1:0] idle      = 2'd0;
    parameter [1:0] s1_red    = 2'd1;
    parameter [1:0] s2_yellow = 2'd2;
    parameter [1:0] s3_green  = 2'd3;

    logic [7:0] cnt;
    logic [1:0] state;
    logic       p_red, p_yellow, p_green;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state    <= idle;
            p_red    <= 1'b0;
            p_yellow <= 1'b0;
            p_green  <= 1'b0;
        end else begin
            case (state)
                idle: begin
                    p_red    <= 1'b0;
                    p_yellow <= 1'b0;
                    p_green  <= 1'b0;
                    state    <= s1_red;
                end
                s1_red: begin
                    p_red    <= 1'b1;
                    p_yellow <= 1'b0;
                    p_green  <= 1'b0;
                    if (cnt == 8'd3) state <= s3_green;
                end
                s2_yellow: begin
                    p_red    <= 1'b0;
                    p_yellow <= 1'b1;
                    p_green  <= 1'b0;
                    if (cnt == 8'd3) state <= s1_red;
                end
                s3_green: begin
                    p_red    <= 1'b0;
                    p_yellow <= 1'b0;
                    p_green  <= 1'b1;
                    if (cnt == 8'd3) state <= s2_yellow;
                end
                default: state <= idle;
            endcase
        end
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            cnt <= 8'd10;
        end else if (pass_request && green && (cnt > 8'd10)) begin
            cnt <= 8'd10;
        end else if (!green && p_green) begin
            cnt <= 8'd60;
        end else if (!yellow && p_yellow) begin
            cnt <= 8'd5;
        end else if (!red && p_red) begin
            cnt <= 8'd10;
        end else begin
            cnt <= cnt - 8'd1;
        end
    end

    assign clock = cnt;

    always_ff @(posedge clk or negedge rst_n) begin
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
