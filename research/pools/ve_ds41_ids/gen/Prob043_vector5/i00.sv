module TopModule (
    input  logic a,
    input  logic b,
    input  logic c,
    input  logic d,
    input  logic e,
    output logic [24:0] out
);

    assign out = {
        ~(a ^ a), // out[24]
        ~(a ^ b), // out[23]
        ~(a ^ c), // out[22]
        ~(a ^ d), // out[21]
        ~(a ^ e), // out[20]
        ~(b ^ a), // out[19]
        ~(b ^ b), // out[18]
        ~(b ^ c), // out[17]
        ~(b ^ d), // out[16]
        ~(b ^ e), // out[15]
        ~(c ^ a), // out[14]
        ~(c ^ b), // out[13]
        ~(c ^ c), // out[12]
        ~(c ^ d), // out[11]
        ~(c ^ e), // out[10]
        ~(d ^ a), // out[9]
        ~(d ^ b), // out[8]
        ~(d ^ c), // out[7]
        ~(d ^ d), // out[6]
        ~(d ^ e), // out[5]
        ~(e ^ a), // out[4]
        ~(e ^ b), // out[3]
        ~(e ^ c), // out[2]
        ~(e ^ d), // out[1]
        ~(e ^ e)  // out[0]
    };

endmodule
