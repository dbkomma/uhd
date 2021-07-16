module mtx_sig2 #(
  parameter SIN_COS_WIDTH = 16,
  parameter PHASE_WIDTH   = 24 ,
  parameter NSYMB_WIDTH   = 16,
  parameter TX_SYNC_BITS  = 3,
  parameter [NSYMB_WIDTH-1:0] NSYMB        = 8, 
  parameter [PHASE_WIDTH-1:0] NSIG         = 8192,
  parameter [PHASE_WIDTH-1:0] DPH_INC      = 16384,
  parameter [PHASE_WIDTH-1:0] START_PH_INC = 4096,
  parameter [PHASE_WIDTH-1:0] FREQ_SHIFT   = 8192,
  parameter [PHASE_WIDTH-1:0] START_PH     = 24'h000000,
  parameter [PHASE_WIDTH-1:0] NPH_SHIFT    = 24'h000000
)(
  input   clk,
  input   reset,
  input   srst,

  /* phase data*/
  input  phase_tvalid, 
  input  phase_tlast, 
  output phase_tready,

  /* IQ output */
  output  out_tlast,
  output  out_tvalid,
  input   out_tready,
  output [SIN_COS_WIDTH-1:0]  itx,
  output [SIN_COS_WIDTH-1:0]  qtx,

  output sync_ready,

  /*debug*/
  output [PHASE_WIDTH-1:0] ph,
  output [PHASE_WIDTH-1:0] ph_start,
  output [PHASE_WIDTH-1:0] sigN,
  output [NSYMB_WIDTH-1:0] symbN
);


reg  [PHASE_WIDTH-1:0]  ncount;
reg  [NSYMB_WIDTH-1:0]  symb_count;
reg  [PHASE_WIDTH-1:0]  phase_inc, start_phase, phase, phase_inc2, phase2;
wire [PHASE_WIDTH-1:0]  phase_tdata = phase;

wire [PHASE_WIDTH-1:0]  phase_tdata2 = phase2;

reg  [TX_SYNC_BITS-1:0] tx_symb_per_synch;
assign sync_ready = &tx_symb_per_synch;

wire [SIN_COS_WIDTH-1:0]  sin_01, sin_02, cos_01, cos_02, itx, qtx;

add2_and_clip sum_01(.in1(cos_01), .in2(cos_02), .sum(itx));
add2_and_clip sum_02(.in1(sin_01), .in2(sin_02), .sum(qtx));

assign ph       = phase;
assign ph_start = start_phase;
assign sigN     = ncount;
assign symbN    = symb_count;

dds_sin_cos_lut_only dds_inst (
    .aclk(clk),                                // input wire aclk
    .aresetn(~reset),            // input wire aresetn active low rst
    .s_axis_phase_tvalid(phase_tvalid),  // input wire s_axis_phase_tvalid
    .s_axis_phase_tready(phase_tready),  // output wire s_axis_phase_tready
    .s_axis_phase_tlast(phase_tlast),    //tlast
    .s_axis_phase_tdata(phase_tdata),    // input wire [23 : 0] s_axis_phase_tdata
    .m_axis_data_tvalid(out_tvalid),    // output wire m_axis_data_tvalid
    .m_axis_data_tready(out_tready),    // input wire m_axis_data_tready
    .m_axis_data_tlast(out_tlast),      // output wire m_axis_data_tready
    .m_axis_data_tdata({sin_01, cos_01})      // output wire [31 : 0] m_axis_data_tdata
);

dds_sin_cos_lut_only dds_inst2 (
    .aclk(clk),                                // input wire aclk
    .aresetn(~reset),            // input wire aresetn active low rst
    .s_axis_phase_tvalid(phase_tvalid),  // input wire s_axis_phase_tvalid
    .s_axis_phase_tready(),  // output wire s_axis_phase_tready
    .s_axis_phase_tlast(phase_tlast),    //tlast
    .s_axis_phase_tdata(phase_tdata2),    // input wire [23 : 0] s_axis_phase_tdata
    .m_axis_data_tvalid(),    // output wire m_axis_data_tvalid
    .m_axis_data_tready(out_tready),    // input wire m_axis_data_tready
    .m_axis_data_tlast(),      // output wire m_axis_data_tready
    .m_axis_data_tdata({sin_02, cos_02})      // output wire [31 : 0] m_axis_data_tdata
);

always @(posedge clk) begin
    if (reset || srst) begin
      phase  <= START_PH;
      phase2 <= START_PH; 
      ncount <= NSIG;
      symb_count <= NSYMB;
      phase_inc <= START_PH_INC;
      phase_inc <= START_PH_INC + FREQ_SHIFT;
      start_phase <= START_PH;
      tx_symb_per_synch <= {(TX_SYNC_BITS){1'b1}};
    end 
    else if (ncount == NSIG) begin 
      ncount <= 1;
      phase2 <= START_PH;
      if (symb_count == NSYMB) begin
        tx_symb_per_synch <= tx_symb_per_synch + 1;
        symb_count <= 1;
        phase  <= START_PH;
        phase_inc <= START_PH_INC;
        phase_inc2 <= START_PH_INC + FREQ_SHIFT;
        start_phase <= START_PH - NPH_SHIFT;
      end else begin
        phase  <= start_phase;
        symb_count <= symb_count + 1;
        phase_inc <= phase_inc + DPH_INC;
        phase_inc2 <= phase_inc2 + DPH_INC;
        start_phase <= start_phase - NPH_SHIFT;
      end   
    end
    else begin
      phase  <= phase + phase_inc;
      phase2 <= phase2 + phase_inc2;
      ncount <= ncount + 1;
    end
end

endmodule