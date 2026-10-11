// -----------------------------------------------------------------------------
// Module: fixed_point_subtractor
// Fixed-point subtractor with parameterized precision.
//
//   Q : number of fractional bits
//   N : total word width (integer + fractional) of inputs and output
//
// Number representation
//   Inputs and output are two's complement fixed-point words with an implied
//   binary point located Q bits up from the LSB. Because the binary point is
//   identical for a, b and c, the subtraction reduces to a plain two's
//   complement integer subtraction:
//
//       c = a - b        (modulo 2**N)
//
//   Example (N=4): a = 0001 (+1), b = 1111 (-1)  ->  c = 0010 (+2)
//
//   Arithmetic-wrap behavior of two's complement naturally covers every case
//   described in the specification:
//     * same-sign operands  -> magnitudes/parts subtract, sign follows result
//     * opposite-sign operands -> magnitudes add, sign set by the larger value
//     * a zero result is all-zeros, i.e. its sign bit is explicitly 0
//
// The binary point of the result stays at the same position as the operands,
// so Q is preserved without any explicit rescaling (parameter kept for
// interface/elaboration completeness).
// -----------------------------------------------------------------------------

module fixed_point_subtractor #(
    parameter integer Q = 4,   // number of fractional (fraction) bits
    parameter integer N = 8    // total word width, N >= 1
) (
    input  logic [N-1:0] a,    // first  fixed-point operand
    input  logic [N-1:0] b,    // second fixed-point operand
    output logic [N-1:0] c     // result of a - b
);

    // Internal result register
    logic [N-1:0] res;

    // Two's complement fixed-point subtraction.
    // The subtraction is exact for the full N-bit range; any overflow beyond
    // the N-bit container wraps modulo 2**N, which is the specified behavior.
    always_comb begin
        res = a - b;

        // A zero result is always encoded as all zeros, hence its sign bit is
        // explicitly 0 (two's complement has no negative-zero encoding, so
        // this is inherently satisfied and no extra correction is needed).
        if (res == {N{1'b0}})
            res = {N{1'b0}};
    end

    assign c = res;

endmodule
