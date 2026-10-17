// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design internal header
// See Vsoc_b.h for the primary calling header

#ifndef VERILATED_VSOC_B___024ROOT_H_
#define VERILATED_VSOC_B___024ROOT_H_  // guard

#include "verilated.h"


class Vsoc_b__Syms;

class alignas(VL_CACHE_LINE_BYTES) Vsoc_b___024root final {
  public:

    // TOP LEVEL PORTS
    union {
        struct {
            VL_IN8(clk,0,0);
            VL_IN8(resetn,0,0);
            VL_OUT8(uart_tx,0,0);
            VL_IN8(uart_rx,0,0);
            VL_OUT8(led,5,0);
            VL_OUT8(dbg_tx_valid,0,0);
            VL_OUT8(dbg_tx_byte,7,0);
            VL_OUT8(dbg_trap,0,0);
        } __VprimaryPorts;
    };

    // TRIVIALLY CONSTRUCTIBLE STATE
    // Anonymous structures to workaround compiler member-count bugs
    struct {
        ::CData/*7:0*/ soc_b__DOT__tx_byte;
        ::CData/*0:0*/ soc_b__DOT__tx_start;
        ::CData/*7:0*/ soc_b__DOT__rx_hold;
        ::CData/*0:0*/ soc_b__DOT__rx_full;
        ::CData/*0:0*/ soc_b__DOT__hw_run;
        ::CData/*5:0*/ soc_b__DOT__led_r;
        ::CData/*0:0*/ soc_b__DOT__sel_ram_q;
        ::CData/*7:0*/ soc_b__DOT__u_rx__DOT__data;
        ::CData/*0:0*/ soc_b__DOT__u_rx__DOT__valid;
        ::CData/*1:0*/ soc_b__DOT__u_rx__DOT__st;
        ::CData/*3:0*/ soc_b__DOT__u_rx__DOT__n;
        ::CData/*7:0*/ soc_b__DOT__u_rx__DOT__sh;
        ::CData/*0:0*/ soc_b__DOT__u_rx__DOT__rx_q;
        ::CData/*0:0*/ soc_b__DOT__u_rx__DOT__rx_s;
        ::CData/*3:0*/ soc_b__DOT__u_tx__DOT__n;
        ::CData/*7:0*/ soc_b__DOT__u_tx__DOT__c;
        ::CData/*0:0*/ soc_b__DOT__u_core__DOT__mem_valid;
        ::CData/*2:0*/ soc_b__DOT__u_core__DOT__state;
        ::CData/*3:0*/ soc_b__DOT__u_core__DOT__wstrb_r;
        ::CData/*0:0*/ soc_b__DOT__u_core__DOT__valid_r;
        ::CData/*2:0*/ soc_b__DOT__u_core__DOT__ld_f3;
        ::CData/*1:0*/ soc_b__DOT__u_core__DOT__ld_off;
        ::CData/*4:0*/ soc_b__DOT__u_core__DOT__ld_rd;
        ::CData/*0:0*/ soc_b__DOT__u_core__DOT__ld_is;
        ::CData/*2:0*/ soc_b__DOT__u_core__DOT__md_f3;
        ::CData/*4:0*/ soc_b__DOT__u_core__DOT__md_rd;
        ::CData/*5:0*/ soc_b__DOT__u_core__DOT__md_cnt;
        ::CData/*0:0*/ soc_b__DOT__u_core__DOT__md_is_div;
        ::CData/*0:0*/ soc_b__DOT__u_core__DOT__q_neg;
        ::CData/*0:0*/ soc_b__DOT__u_core__DOT__r_neg;
        ::CData/*0:0*/ soc_b__DOT__u_core__DOT__rmd_ge;
        ::CData/*0:0*/ soc_b__DOT__u_core__DOT__div_signed_d;
        ::CData/*0:0*/ soc_b__DOT__u_core__DOT__is_muldiv;
        ::CData/*0:0*/ soc_b__DOT__u_core__DOT__acc_data;
        ::CData/*0:0*/ soc_b__DOT__u_core__DOT__bad;
        ::CData/*7:0*/ __Vdfg_Regularize_706;
        ::CData/*0:0*/ __Vdfg_Regularize_710;
        ::CData/*0:0*/ __Vdfg_Regularize_711;
        ::CData/*0:0*/ __Vdfg_Regularize_712;
        ::CData/*0:0*/ __Vdfg_Regularize_716;
        ::CData/*0:0*/ __Vtrigprevexpr___TOP__clk__0;
        ::CData/*0:0*/ __Vtrigprevexpr___TOP__resetn__0;
        ::CData/*0:0*/ __Vtrigprevexpr___TOP__uart_rx__0;
        ::CData/*0:0*/ __VicoDidInit;
        ::CData/*0:0*/ __Vtrigprevexpr___TOP__clk__1;
        ::SData/*8:0*/ soc_b__DOT__u_rx__DOT__c;
        ::SData/*9:0*/ soc_b__DOT__u_tx__DOT__sh;
        ::SData/*15:0*/ __Vdfg_Regularize_707;
        ::IData/*31:0*/ soc_b__DOT__mem_rdata;
        ::IData/*31:0*/ soc_b__DOT__ram_q;
        ::IData/*31:0*/ soc_b__DOT__hw_cnt;
        ::IData/*31:0*/ soc_b__DOT__per_q;
        ::IData/*31:0*/ soc_b__DOT__u_core__DOT__addr_r;
        ::IData/*31:0*/ soc_b__DOT__u_core__DOT__wdata_r;
        ::IData/*31:0*/ soc_b__DOT__u_core__DOT__pc;
        ::IData/*31:0*/ soc_b__DOT__u_core__DOT__pc_ret;
        ::IData/*31:0*/ soc_b__DOT__u_core__DOT__rv1;
        ::IData/*31:0*/ soc_b__DOT__u_core__DOT__rv2;
        ::IData/*31:0*/ soc_b__DOT__u_core__DOT__d_addr;
        ::IData/*31:0*/ soc_b__DOT__u_core__DOT__md_a;
        ::IData/*31:0*/ soc_b__DOT__u_core__DOT__md_b;
        ::IData/*31:0*/ soc_b__DOT__u_core__DOT__dvd;
        ::IData/*31:0*/ soc_b__DOT__u_core__DOT__dvs;
        ::IData/*31:0*/ soc_b__DOT__u_core__DOT__quo;
    };
    struct {
        ::IData/*31:0*/ soc_b__DOT__u_core__DOT__rmd;
        ::IData/*31:0*/ soc_b__DOT__u_core__DOT__next_pc;
        ::IData/*31:0*/ __Vdfg_Regularize_714;
        ::IData/*31:0*/ __Vdfg_Regularize_715;
        ::QData/*63:0*/ soc_b__DOT__u_core__DOT__cnt_cycle;
        ::QData/*63:0*/ soc_b__DOT__u_core__DOT__cnt_instret;
        ::QData/*63:0*/ soc_b__DOT__u_core__DOT__prod_u;
        ::QData/*32:0*/ soc_b__DOT__u_core__DOT__rmd_sh;
        ::VlUnpacked<::IData/*31:0*/, 16384> soc_b__DOT__ram;
        ::VlUnpacked<::IData/*31:0*/, 32> soc_b__DOT__u_core__DOT__regs;
        ::VlUnpacked<::QData/*63:0*/, 1> __VstlTriggered;
        ::VlUnpacked<::QData/*63:0*/, 2> __VicoTriggered;
        ::VlUnpacked<::QData/*63:0*/, 1> __VactTriggered;
        ::VlUnpacked<::QData/*63:0*/, 1> __VnbaTriggered;
    };

    // INTERNAL VARIABLES
    Vsoc_b__Syms* vlSymsp;
    const char* vlNamep;

    // CONSTRUCTORS
    Vsoc_b___024root(Vsoc_b__Syms* symsp, const char* namep);
    ~Vsoc_b___024root();
    VL_UNCOPYABLE(Vsoc_b___024root);
    VL_UNMOVABLE(Vsoc_b___024root);

    // INTERNAL METHODS
};


#endif  // guard
