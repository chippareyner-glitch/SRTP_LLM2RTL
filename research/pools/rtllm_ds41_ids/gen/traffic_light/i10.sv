module traffic_light (
    input  wire       rst_n,
    input  wire       clk,
    input  wire       pass_request,
    output wire [7:0] clock,
    output reg        red,
    output reg        yellow,
    output reg        green
);

    parameter [1:0] idle      = 2'd0,
                    s1_red    = 2'd1,
                    s2_yellow = 2'd2,
                    s3_green  = 2'd3;

    reg [7:0] cnt;
    reg [1:0] state;
    reg       p_red, p_yellow, p_green;
    reg [1:0] next_state;
    reg       pass_request_d;

    wire pass_request_pulse;
    assign pass_request_pulse = pass_request & ~pass_request_d;

    always @(*) begin
        next_state = state;

        case (state)
            idle:      next_state = s1_red;
            s1_red:    next_state = (cnt == 8'd1) ? s3_green  : s1_red;
            s3_green:  next_state = (cnt == 8'd1) ? s2_yellow : s3_green;
            s2_yellow: next_state = (cnt == 8'd1) ? s1_red    : s2_yellow;
            default:   next_state = idle;
        endcase

        p_red    = (next_state == s1_red);
        p_yellow = (next_state == s2_yellow);
        p_green  = (next_state == s3_green);
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state          <= idle;
            cnt            <= 8'd10;
            pass_request_d <= 1'b0;
        end else begin
            pass_request_d <= pass_request;
            state          <= next_state;

            if (pass_request_pulse && state == s3_green && cnt > 8'd10) begin
                cnt <= 8'd10;
            end else if (next_state != state) begin
                case (next_state)
                    s1_red:    cnt <= 8'd10;
                    s3_green:  cnt <= 8'd60;
                    s2_yellow: cnt <= 8'd5;
                    default:   cnt <= cnt;
                endcase
            end else if (cnt > 8'd1) begin
                cnt <= cnt - 8'd1;
            end else begin
                cnt <= cnt;
            end
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

    assign clock = cnt;

endmodule
