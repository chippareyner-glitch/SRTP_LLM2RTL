module TopModule (
    input  clk,
    input  areset,
    input  bump_left,
    input  bump_right,
    input  ground,
    input  dig,
    output walk_left,
    output walk_right,
    output aaah,
    output digging
);

    localparam [2:0] WL    = 3'd0,
                     WR    = 3'd1,
                     FL    = 3'd2,
                     FR    = 3'd3,
                     DL    = 3'd4,
                     DR    = 3'd5,
                     SPLAT = 3'd6;

    logic [2:0] state;
    logic [4:0] cnt;

    always_ff @(posedge clk or posedge areset) begin
        if (areset) begin
            state <= WL;
            cnt   <= 5'd0;
        end else begin
            case (state)
                WL: begin
                    if (!ground) begin
                        state <= FL;
                        cnt   <= 5'd1;
                    end else if (dig) begin
                        state <= DL;
                        cnt   <= 5'd0;
                    end else if (bump_left) begin
                        state <= WR;
                        cnt   <= 5'd0;
                    end else begin
                        state <= WL;
                        cnt   <= 5'd0;
                    end
                end

                WR: begin
                    if (!ground) begin
                        state <= FR;
                        cnt   <= 5'd1;
                    end else if (dig) begin
                        state <= DR;
                        cnt   <= 5'd0;
                    end else if (bump_right) begin
                        state <= WL;
                        cnt   <= 5'd0;
                    end else begin
                        state <= WR;
                        cnt   <= 5'd0;
                    end
                end

                DL: begin
                    if (!ground) begin
                        state <= FL;
                        cnt   <= 5'd1;
                    end else begin
                        state <= DL;
                        cnt   <= 5'd0;
                    end
                end

                DR: begin
                    if (!ground) begin
                        state <= FR;
                        cnt   <= 5'd1;
                    end else begin
                        state <= DR;
                        cnt   <= 5'd0;
                    end
                end

                FL: begin
                    if (ground) begin
                        if (cnt > 5'd20)
                            state <= SPLAT;
                        else
                            state <= WL;
                        cnt <= 5'd0;
                    end else begin
                        state <= FL;
                        if (cnt < 5'd21)
                            cnt <= cnt + 5'd1;
                        else
                            cnt <= cnt;
                    end
                end

                FR: begin
                    if (ground) begin
                        if (cnt > 5'd20)
                            state <= SPLAT;
                        else
                            state <= WR;
                        cnt <= 5'd0;
                    end else begin
                        state <= FR;
                        if (cnt < 5'd21)
                            cnt <= cnt + 5'd1;
                        else
                            cnt <= cnt;
                    end
                end

                SPLAT: begin
                    state <= SPLAT;
                    cnt   <= 5'd0;
                end

                default: begin
                    state <= WL;
                    cnt   <= 5'd0;
                end
            endcase
        end
    end

    assign walk_left  = (state == WL);
    assign walk_right = (state == WR);
    assign aaah       = (state == FL) || (state == FR);
    assign digging    = (state == DL) || (state == DR);

endmodule
