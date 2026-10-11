module traffic_light (
    input rst_n,
    input clk,
    input pass_request,
    output [7:0] clock,
    output reg red,
    output reg yellow,
    output reg green
);

    // State encoding
    localparam idle      = 2'b00;
    localparam s1_red    = 2'b01;
    localparam s2_yellow = 2'b10;
    localparam s3_green  = 2'b11;

    reg [1:0] state;
    reg [7:0] cnt;
    reg p_red, p_yellow, p_green;

    // State transition logic
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= idle;
        end else begin
            case (state)
                idle:      state <= s1_red;
                s1_red:    if (cnt == 0) state <= s3_green;
                s3_green:  if (cnt == 0) state <= s2_yellow;
                s2_yellow: if (cnt == 0) state <= s1_red;
                default:   state <= idle;
            endcase
        end
    end

    // Counter logic
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            cnt <= 10;
        end else begin
            if (state == idle) begin
                cnt <= 10;
            end else if (cnt == 0) begin
                case (state)
                    s1_red:    cnt <= 60; // red -> green
                    s3_green:  cnt <= 5;  // green -> yellow
                    s2_yellow: cnt <= 10; // yellow -> red
                    default:   cnt <= 10;
                endcase
            end else if (state == s3_green && pass_request && cnt > 10) begin
                cnt <= 10;
            end else begin
                cnt <= cnt - 1;
            end
        end
    end

    // Combinational next outputs
    always @(*) begin
        p_red    = (state == s1_red);
        p_yellow = (state == s2_yellow);
        p_green  = (state == s3_green);
    end

    // Registered outputs
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            red    <= 0;
            yellow <= 0;
            green  <= 0;
        end else begin
            red    <= p_red;
            yellow <= p_yellow;
            green  <= p_green;
        end
    end

    // Output counter value
    assign clock = cnt;

endmodule
