module TopModule(
    input clk,
    input load,
    input [255:0] data,
    output logic [255:0] q
);

    logic [255:0] current;
    logic [255:0] next_q;

    // When load=1, the game advances from the loaded data.
    // When load=0, it advances from the current state q.
    always_comb begin
        current = load ? data : q;
    end

    // Compute the next state of the 16x16 toroidal game of life.
    always_comb begin
        int live_neighbors;
        int idx;
        int nr, nc, n_idx;

        for (int r = 0; r < 16; r++) begin
            for (int c = 0; c < 16; c++) begin
                live_neighbors = 0;

                // Sum the 8 neighbours with wrap-around.
                for (int dr = -1; dr <= 1; dr++) begin
                    for (int dc = -1; dc <= 1; dc++) begin
                        if (dr != 0 || dc != 0) begin
                            nr = (r + dr + 16) % 16;
                            nc = (c + dc + 16) % 16;
                            n_idx = nr * 16 + nc;
                            live_neighbors += current[n_idx];
                        end
                    end
                end

                idx = r * 16 + c;

                // Apply the rules.
                if (live_neighbors <= 1)
                    next_q[idx] = 1'b0;
                else if (live_neighbors == 2)
                    next_q[idx] = current[idx];
                else if (live_neighbors == 3)
                    next_q[idx] = 1'b1;
                else
                    next_q[idx] = 1'b0;
            end
        end
    end

    always_ff @(posedge clk) begin
        q <= next_q;
    end

endmodule
