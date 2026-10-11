module TopModule (
    input  logic clk,
    input  logic load,
    input  logic [255:0] data,
    output logic [255:0] q
);

    logic [255:0] q_reg = 256'd0;
    wire  [255:0] next_q;

    genvar i;
    generate
        for (i = 0; i < 256; i = i + 1) begin : gen_cells
            localparam int r = i >> 4;
            localparam int c = i & 15;
            localparam int up = (r + 15) & 15;
            localparam int down = (r + 1) & 15;
            localparam int left = (c + 15) & 15;
            localparam int right = (c + 1) & 15;

            wire [7:0] neigh;
            assign neigh[0] = q_reg[up*16 + left];
            assign neigh[1] = q_reg[up*16 + c];
            assign neigh[2] = q_reg[up*16 + right];
            assign neigh[3] = q_reg[r*16 + left];
            assign neigh[4] = q_reg[r*16 + right];
            assign neigh[5] = q_reg[down*16 + left];
            assign neigh[6] = q_reg[down*16 + c];
            assign neigh[7] = q_reg[down*16 + right];

            wire [3:0] count = {3'b0, neigh[0]} + {3'b0, neigh[1]} + {3'b0, neigh[2]} + {3'b0, neigh[3]} +
                               {3'b0, neigh[4]} + {3'b0, neigh[5]} + {3'b0, neigh[6]} + {3'b0, neigh[7]};

            assign next_q[i] = (count == 3) || (count == 2 && q_reg[i]);
        end
    endgenerate

    always_ff @(posedge clk) begin
        if (load)
            q_reg <= data;
        else
            q_reg <= next_q;
    end

    assign q = q_reg;

endmodule
