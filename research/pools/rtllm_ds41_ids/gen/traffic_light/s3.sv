module traffic_light(
    input rst_n,
    input clk,
    input pass_request,
    output [7:0] clock,
    output reg red,
    output reg yellow,
    output reg green
);

    parameter idle = 2'b00,
              s1_red = 2'b01,
              s2_yellow = 2'b10,
              s3_green = 2'b11;

    reg [7:0] cnt;
    reg [1:0] state;
    reg p_red, p_yellow, p_green;

    // State transition and next-light logic
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= idle;
            p_red <= 1'b0;
            p_yellow <= 1'b0;
            p_green <= 1'b0;
        end else begin
            case (state)
                idle: begin
                    p_red <= 1'b0;
                    p_yellow <= 1'b0;
                    p_green <= 1'b0;
                    state <= s1_red;
                end
                s1_red: begin
                    p_red <= 1'b1;
                    p_yellow <= 1'b0;
                    p_green <= 1'b0;
                    if (cnt == 8'd2) state <= s3_green;
                end
                s2_yellow: begin
                    p_red <= 1'b0;
                    p_yellow <= 1'b1;
                    p_green <= 1'b0;
                    if (cnt == 8'd2) state <= s1_red;
                end
                s3_green: begin
                    p_red <= 1'b0;
                    p_yellow <= 1'b0;
                    p_green <= 1'b1;
                    if (cnt == 8'd2) state <= s2_yellow;
                end
                default: begin
                    p_red <= 1'b0;
                    p_yellow <= 1'b0;
                    p_green <= 1'b0;
                    state <= idle;
                end
            endcase
        end
    end

    // Internal counter logic
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            cnt <= 8'd10;
        end else begin
            if (pass_request && green && (cnt > 8'd10)) begin
                cnt <= 8'd10;
            end else if (!green && p_green) begin
                cnt <= 8'd60;
            end else if (!yellow && p_yellow) begin
                cnt <= 8'd5;
            end else if (!red && p_red) begin
                cnt <= 8'd10;
            end else begin
                cnt <= cnt - 1'b1;
            end
        end
    end

    // Output registers
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            red <= 1'b0;
            yellow <= 1'b0;
            green <= 1'b0;
        end else begin
            red <= p_red;
            yellow <= p_yellow;
            green <= p_green;
        end
    end

    assign clock = cnt;

endmodule
