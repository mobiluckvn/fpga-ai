// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vsoc_b.h for the primary calling header

#include "Vsoc_b__pch.h"

VL_ATTR_COLD void Vsoc_b___024root___eval_static(Vsoc_b___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vsoc_b___024root___eval_static\n"); );
    Vsoc_b__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    {
        // Inlined CFunc: _eval_static__TOP
        vlSelfRef.soc_b__DOT__rx_hold = 0U;
        vlSelfRef.soc_b__DOT__rx_full = 0U;
        vlSelfRef.soc_b__DOT__hw_cnt = 0U;
        vlSelfRef.soc_b__DOT__hw_run = 0U;
        vlSelfRef.soc_b__DOT__led_r = 0U;
        vlSelfRef.soc_b__DOT__u_rx__DOT__data = 0U;
        vlSelfRef.soc_b__DOT__u_rx__DOT__valid = 0U;
        vlSelfRef.soc_b__DOT__u_rx__DOT__st = 0U;
        vlSelfRef.soc_b__DOT__u_rx__DOT__c = 0U;
        vlSelfRef.soc_b__DOT__u_rx__DOT__n = 0U;
        vlSelfRef.soc_b__DOT__u_rx__DOT__sh = 0U;
        vlSelfRef.soc_b__DOT__u_rx__DOT__rx_q = 1U;
        vlSelfRef.soc_b__DOT__u_rx__DOT__rx_s = 1U;
        vlSelfRef.soc_b__DOT__u_tx__DOT__sh = 0x03ffU;
        vlSelfRef.soc_b__DOT__u_tx__DOT__n = 0U;
        vlSelfRef.soc_b__DOT__u_tx__DOT__c = 0U;
    }
    vlSelfRef.__Vtrigprevexpr___TOP__clk__0 = vlSelfRef.__VprimaryPorts.clk;
    vlSelfRef.__Vtrigprevexpr___TOP__resetn__0 = vlSelfRef.__VprimaryPorts.resetn;
    vlSelfRef.__Vtrigprevexpr___TOP__uart_rx__0 = vlSelfRef.__VprimaryPorts.uart_rx;
    vlSelfRef.__Vtrigprevexpr___TOP__clk__1 = vlSelfRef.__VprimaryPorts.clk;
}

VL_ATTR_COLD void Vsoc_b___024root___eval_initial(Vsoc_b___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vsoc_b___024root___eval_initial\n"); );
    Vsoc_b__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    {
        // Inlined CFunc: _eval_initial__TOP
        VL_READMEM_N(true, 32, 16384, 0, "firmware.hex"s
                     ,  &(vlSelfRef.soc_b__DOT__ram)
                     , 0, ~0ULL);
    }
}

#ifdef VL_DEBUG
VL_ATTR_COLD void Vsoc_b___024root___dump_triggers__stl(const ::VlUnpacked<::QData/*63:0*/, 1> &triggers, const ::std::string &tag);
#endif  // VL_DEBUG
VL_ATTR_COLD bool Vsoc_b___024root___trigger_anySet__stl(const ::VlUnpacked<::QData/*63:0*/, 1> &in);
VL_ATTR_COLD void Vsoc_b___024root___stl_comb__TOP__0(Vsoc_b___024root* vlSelf);

VL_ATTR_COLD bool Vsoc_b___024root___eval_stl(Vsoc_b___024root* vlSelf, ::CData/*0:0*/ firstIteration) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vsoc_b___024root___eval_stl\n"); );
    Vsoc_b__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    ::CData/*0:0*/ __VstlExecute;
    // Body
    vlSelfRef.__VstlTriggered[0U] = ((0xfffffffffffffffeULL 
                                      & vlSelfRef.__VstlTriggered[0U]) 
                                     | (::IData)((::IData)(firstIteration)));
#ifdef VL_DEBUG
    if (VL_UNLIKELY(vlSymsp->_vm_contextp__->debug())) {
        Vsoc_b___024root___dump_triggers__stl(vlSelfRef.__VstlTriggered, "stl"s);
    }
#endif
    __VstlExecute = Vsoc_b___024root___trigger_anySet__stl(vlSelfRef.__VstlTriggered);
    if (__VstlExecute) {
        {
            // Inlined CFunc: _eval_body__stl
            if ((((1ULL & vlSelfRef.__VstlTriggered[0U])) != 0ULL)) {
                Vsoc_b___024root___stl_comb__TOP__0(vlSelf);
            }
        }
    }
    return (__VstlExecute);
}

VL_ATTR_COLD void Vsoc_b___024root___eval_dump_triggers__stl(Vsoc_b___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vsoc_b___024root___eval_dump_triggers__stl\n"); );
    Vsoc_b__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
#ifdef VL_DEBUG
    Vsoc_b___024root___dump_triggers__stl(vlSelfRef.__VstlTriggered, "stl"s);
#endif
}

#ifdef VL_DEBUG
VL_ATTR_COLD void Vsoc_b___024root___dump_triggers__ico(const ::VlUnpacked<::QData/*63:0*/, 2> &triggers, const ::std::string &tag);
#endif  // VL_DEBUG

VL_ATTR_COLD void Vsoc_b___024root___eval_dump_triggers__ico(Vsoc_b___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vsoc_b___024root___eval_dump_triggers__ico\n"); );
    Vsoc_b__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
#ifdef VL_DEBUG
    Vsoc_b___024root___dump_triggers__ico(vlSelfRef.__VicoTriggered, "ico"s);
#endif
}

#ifdef VL_DEBUG
VL_ATTR_COLD void Vsoc_b___024root___dump_triggers__act(const ::VlUnpacked<::QData/*63:0*/, 1> &triggers, const ::std::string &tag);
#endif  // VL_DEBUG

VL_ATTR_COLD void Vsoc_b___024root___eval_dump_triggers__act(Vsoc_b___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vsoc_b___024root___eval_dump_triggers__act\n"); );
    Vsoc_b__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
#ifdef VL_DEBUG
    Vsoc_b___024root___dump_triggers__act(vlSelfRef.__VactTriggered, "act"s);
#endif
}

VL_ATTR_COLD void Vsoc_b___024root___eval_dump_triggers__nba(Vsoc_b___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vsoc_b___024root___eval_dump_triggers__nba\n"); );
    Vsoc_b__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
#ifdef VL_DEBUG
    Vsoc_b___024root___dump_triggers__act(vlSelfRef.__VnbaTriggered, "nba"s);
#endif
}

VL_ATTR_COLD void Vsoc_b___024root___eval_dump_triggers__obs(Vsoc_b___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vsoc_b___024root___eval_dump_triggers__obs\n"); );
    Vsoc_b__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
}

VL_ATTR_COLD void Vsoc_b___024root___eval_dump_triggers__react(Vsoc_b___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vsoc_b___024root___eval_dump_triggers__react\n"); );
    Vsoc_b__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
}

VL_ATTR_COLD void Vsoc_b___024root___eval_final(Vsoc_b___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vsoc_b___024root___eval_final\n"); );
    Vsoc_b__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
}

#ifdef VL_DEBUG
VL_ATTR_COLD void Vsoc_b___024root___dump_triggers__stl(const ::VlUnpacked<::QData/*63:0*/, 1> &triggers, const ::std::string &tag) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vsoc_b___024root___dump_triggers__stl\n"); );
    // Body
    if ((1U & (~ (::IData)(Vsoc_b___024root___trigger_anySet__stl(triggers))))) {
        VL_DBG_MSGS("         No '" + tag + "' region triggers active\n");
    }
    if ((1U & (::IData)(triggers[0U]))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 0 is active: Internal 'stl' trigger - first iteration\n");
    }
}
#endif  // VL_DEBUG

VL_ATTR_COLD bool Vsoc_b___024root___trigger_anySet__stl(const ::VlUnpacked<::QData/*63:0*/, 1> &in) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vsoc_b___024root___trigger_anySet__stl\n"); );
    // Locals
    ::IData/*31:0*/ n;
    // Body
    n = 0U;
    do {
        if (in[n]) {
            return (1U);
        }
        n = ((::IData)(1U) + n);
    } while ((1U > n));
    return (0U);
}

VL_ATTR_COLD void Vsoc_b___024root___stl_comb__TOP__0(Vsoc_b___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vsoc_b___024root___stl_comb__TOP__0\n"); );
    Vsoc_b__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Locals
    ::IData/*31:0*/ soc_b__DOT__u_core__DOT__imm_i;
    soc_b__DOT__u_core__DOT__imm_i = 0;
    ::IData/*31:0*/ soc_b__DOT__u_core__DOT__alu_b;
    soc_b__DOT__u_core__DOT__alu_b = 0;
    ::CData/*4:0*/ soc_b__DOT__u_core__DOT__shamt;
    soc_b__DOT__u_core__DOT__shamt = 0;
    ::CData/*0:0*/ soc_b__DOT__u_core__DOT__lt_s;
    soc_b__DOT__u_core__DOT__lt_s = 0;
    ::CData/*0:0*/ soc_b__DOT__u_core__DOT__lt_u;
    soc_b__DOT__u_core__DOT__lt_u = 0;
    ::IData/*31:0*/ soc_b__DOT__u_core__DOT__ld_addr;
    soc_b__DOT__u_core__DOT__ld_addr = 0;
    ::CData/*0:0*/ soc_b__DOT__u_core__DOT__is_csr;
    soc_b__DOT__u_core__DOT__is_csr = 0;
    ::CData/*0:0*/ __Vdfg_Regularize_717;
    __Vdfg_Regularize_717 = 0;
    ::CData/*0:0*/ __Vdfg_Regularize_718;
    __Vdfg_Regularize_718 = 0;
    ::CData/*0:0*/ __Vdfg_Regularize_719;
    __Vdfg_Regularize_719 = 0;
    // Body
    vlSelfRef.__VprimaryPorts.led = (0x0000003fU & 
                                     (~ (::IData)(vlSelfRef.soc_b__DOT__led_r)));
    vlSelfRef.__VprimaryPorts.uart_tx = (1U & (::IData)(vlSelfRef.soc_b__DOT__u_tx__DOT__sh));
    vlSelfRef.soc_b__DOT__u_core__DOT__mem_valid = 
        ((~ (::IData)(vlSelfRef.__VprimaryPorts.dbg_trap)) 
         & (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__valid_r));
    vlSelfRef.__Vdfg_Regularize_710 = ((::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__ld_is) 
                                       & (0U != (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__ld_rd)));
    vlSelfRef.__Vdfg_Regularize_711 = ((3U == (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__state)) 
                                       & ((0U == (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__md_cnt)) 
                                          & (0U != (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__md_rd))));
    vlSelfRef.soc_b__DOT__u_core__DOT__rmd_sh = (((::QData)((::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__rmd)) 
                                                  << 1U) 
                                                 | (::QData)((::IData)(
                                                                       (vlSelfRef.soc_b__DOT__u_core__DOT__dvd 
                                                                        >> 0x0000001fU))));
    vlSelfRef.soc_b__DOT__u_core__DOT__prod_u = ((::QData)((::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__md_b)) 
                                                 * (::QData)((::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__md_a)));
    vlSelfRef.soc_b__DOT__mem_rdata = ((::IData)(vlSelfRef.soc_b__DOT__sel_ram_q)
                                        ? vlSelfRef.soc_b__DOT__ram_q
                                        : vlSelfRef.soc_b__DOT__per_q);
    vlSelfRef.soc_b__DOT__u_core__DOT__rmd_ge = (vlSelfRef.soc_b__DOT__u_core__DOT__rmd_sh 
                                                 >= (::QData)((::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__dvs)));
    vlSelfRef.__Vdfg_Regularize_714 = (::IData)((((vlSelfRef.soc_b__DOT__u_core__DOT__prod_u 
                                                   - 
                                                   (((::QData)((::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__md_b)) 
                                                     << 0x00000020U) 
                                                    & (- (::QData)((::IData)(
                                                                             (((1U 
                                                                                == (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__md_f3)) 
                                                                               | (2U 
                                                                                == (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__md_f3))) 
                                                                              & (vlSelfRef.soc_b__DOT__u_core__DOT__md_a 
                                                                                >> 0x0000001fU))))))) 
                                                  - 
                                                  (((::QData)((::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__md_a)) 
                                                    << 0x00000020U) 
                                                   & (- (::QData)((::IData)(
                                                                            ((1U 
                                                                              == (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__md_f3)) 
                                                                             & (vlSelfRef.soc_b__DOT__u_core__DOT__md_b 
                                                                                >> 0x0000001fU))))))) 
                                                 >> 0x00000020U));
    vlSelfRef.soc_b__DOT__u_core__DOT__div_signed_d 
        = ((4U == (7U & (vlSelfRef.soc_b__DOT__mem_rdata 
                         >> 0x0000000cU))) | (6U == 
                                              (7U & 
                                               (vlSelfRef.soc_b__DOT__mem_rdata 
                                                >> 0x0000000cU))));
    if ((2U & (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__ld_off))) {
        vlSelfRef.__Vdfg_Regularize_706 = (0x000000ffU 
                                           & ((1U & (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__ld_off))
                                               ? (vlSelfRef.soc_b__DOT__mem_rdata 
                                                  >> 0x00000018U)
                                               : (vlSelfRef.soc_b__DOT__mem_rdata 
                                                  >> 0x00000010U)));
        vlSelfRef.__Vdfg_Regularize_707 = (0x0000ffffU 
                                           & (vlSelfRef.soc_b__DOT__mem_rdata 
                                              >> 0x00000010U));
    } else {
        vlSelfRef.__Vdfg_Regularize_706 = (0x000000ffU 
                                           & ((1U & (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__ld_off))
                                               ? (vlSelfRef.soc_b__DOT__mem_rdata 
                                                  >> 8U)
                                               : vlSelfRef.soc_b__DOT__mem_rdata));
        vlSelfRef.__Vdfg_Regularize_707 = (0x0000ffffU 
                                           & vlSelfRef.soc_b__DOT__mem_rdata);
    }
    vlSelfRef.soc_b__DOT__u_core__DOT__is_muldiv = (::IData)(
                                                             (0x02000033U 
                                                              == 
                                                              (0xfe00007fU 
                                                               & vlSelfRef.soc_b__DOT__mem_rdata)));
    vlSelfRef.__Vdfg_Regularize_716 = (::IData)((3U 
                                                 == 
                                                 (0x0000000bU 
                                                  & vlSelfRef.soc_b__DOT__mem_rdata)));
    __Vdfg_Regularize_717 = (1U & ((~ (vlSelfRef.soc_b__DOT__mem_rdata 
                                       >> 2U)) | (~ 
                                                  (3U 
                                                   == 
                                                   (3U 
                                                    & vlSelfRef.soc_b__DOT__mem_rdata)))));
    __Vdfg_Regularize_719 = (1U & ((0U != (0x0000000cU 
                                           & vlSelfRef.soc_b__DOT__mem_rdata)) 
                                   | (~ (3U == (3U 
                                                & vlSelfRef.soc_b__DOT__mem_rdata)))));
    soc_b__DOT__u_core__DOT__is_csr = ((0x73U == (0x0000007fU 
                                                  & vlSelfRef.soc_b__DOT__mem_rdata)) 
                                       & (0U != (7U 
                                                 & (vlSelfRef.soc_b__DOT__mem_rdata 
                                                    >> 0x0000000cU))));
    vlSelfRef.soc_b__DOT__u_core__DOT__acc_data = (
                                                   (0x23U 
                                                    == 
                                                    (0x0000007fU 
                                                     & vlSelfRef.soc_b__DOT__mem_rdata)) 
                                                   | (3U 
                                                      == 
                                                      (0x0000007fU 
                                                       & vlSelfRef.soc_b__DOT__mem_rdata)));
    vlSelfRef.soc_b__DOT__u_core__DOT__rv2 = ((0U == 
                                               (0x0000001fU 
                                                & (vlSelfRef.soc_b__DOT__mem_rdata 
                                                   >> 0x00000014U)))
                                               ? 0U
                                               : vlSelfRef.soc_b__DOT__u_core__DOT__regs
                                              [(0x0000001fU 
                                                & (vlSelfRef.soc_b__DOT__mem_rdata 
                                                   >> 0x00000014U))]);
    soc_b__DOT__u_core__DOT__imm_i = (((- (::IData)(
                                                    (vlSelfRef.soc_b__DOT__mem_rdata 
                                                     >> 0x0000001fU))) 
                                       << 0x0000000cU) 
                                      | (vlSelfRef.soc_b__DOT__mem_rdata 
                                         >> 0x00000014U));
    vlSelfRef.soc_b__DOT__u_core__DOT__rv1 = ((0U == 
                                               (0x0000001fU 
                                                & (vlSelfRef.soc_b__DOT__mem_rdata 
                                                   >> 0x0000000fU)))
                                               ? 0U
                                               : vlSelfRef.soc_b__DOT__u_core__DOT__regs
                                              [(0x0000001fU 
                                                & (vlSelfRef.soc_b__DOT__mem_rdata 
                                                   >> 0x0000000fU))]);
    if ((0x13U == (0x0000007fU & vlSelfRef.soc_b__DOT__mem_rdata))) {
        soc_b__DOT__u_core__DOT__shamt = (0x0000001fU 
                                          & (vlSelfRef.soc_b__DOT__mem_rdata 
                                             >> 0x00000014U));
        soc_b__DOT__u_core__DOT__alu_b = soc_b__DOT__u_core__DOT__imm_i;
    } else {
        soc_b__DOT__u_core__DOT__shamt = (0x0000001fU 
                                          & vlSelfRef.soc_b__DOT__u_core__DOT__rv2);
        soc_b__DOT__u_core__DOT__alu_b = vlSelfRef.soc_b__DOT__u_core__DOT__rv2;
    }
    soc_b__DOT__u_core__DOT__ld_addr = (vlSelfRef.soc_b__DOT__u_core__DOT__rv1 
                                        + soc_b__DOT__u_core__DOT__imm_i);
    soc_b__DOT__u_core__DOT__lt_s = VL_LTS_III(32, vlSelfRef.soc_b__DOT__u_core__DOT__rv1, soc_b__DOT__u_core__DOT__alu_b);
    soc_b__DOT__u_core__DOT__lt_u = (vlSelfRef.soc_b__DOT__u_core__DOT__rv1 
                                     < soc_b__DOT__u_core__DOT__alu_b);
    vlSelfRef.soc_b__DOT__u_core__DOT__d_addr = ((0x23U 
                                                  == 
                                                  (0x0000007fU 
                                                   & vlSelfRef.soc_b__DOT__mem_rdata))
                                                  ? 
                                                 (vlSelfRef.soc_b__DOT__u_core__DOT__rv1 
                                                  + 
                                                  (((- (::IData)(
                                                                 (vlSelfRef.soc_b__DOT__mem_rdata 
                                                                  >> 0x0000001fU))) 
                                                    << 0x0000000cU) 
                                                   | ((0x00000fe0U 
                                                       & (vlSelfRef.soc_b__DOT__mem_rdata 
                                                          >> 0x00000014U)) 
                                                      | (0x0000001fU 
                                                         & (vlSelfRef.soc_b__DOT__mem_rdata 
                                                            >> 7U)))))
                                                  : soc_b__DOT__u_core__DOT__ld_addr);
    vlSelfRef.__Vdfg_Regularize_715 = (((0x00004000U 
                                         & vlSelfRef.soc_b__DOT__mem_rdata)
                                         ? ((0x00002000U 
                                             & vlSelfRef.soc_b__DOT__mem_rdata)
                                             ? ((0x00001000U 
                                                 & vlSelfRef.soc_b__DOT__mem_rdata)
                                                 ? 
                                                (vlSelfRef.soc_b__DOT__u_core__DOT__rv1 
                                                 & soc_b__DOT__u_core__DOT__alu_b)
                                                 : 
                                                (vlSelfRef.soc_b__DOT__u_core__DOT__rv1 
                                                 | soc_b__DOT__u_core__DOT__alu_b))
                                             : ((0x00001000U 
                                                 & vlSelfRef.soc_b__DOT__mem_rdata)
                                                 ? 
                                                ((0x40000000U 
                                                  & vlSelfRef.soc_b__DOT__mem_rdata)
                                                  ? 
                                                 VL_SHIFTRS_III(32,32,5, vlSelfRef.soc_b__DOT__u_core__DOT__rv1, (::IData)(soc_b__DOT__u_core__DOT__shamt))
                                                  : 
                                                 (vlSelfRef.soc_b__DOT__u_core__DOT__rv1 
                                                  >> (::IData)(soc_b__DOT__u_core__DOT__shamt)))
                                                 : 
                                                (vlSelfRef.soc_b__DOT__u_core__DOT__rv1 
                                                 ^ soc_b__DOT__u_core__DOT__alu_b)))
                                         : ((0x00002000U 
                                             & vlSelfRef.soc_b__DOT__mem_rdata)
                                             ? ((0x00001000U 
                                                 & vlSelfRef.soc_b__DOT__mem_rdata)
                                                 ? (::IData)(soc_b__DOT__u_core__DOT__lt_u)
                                                 : (::IData)(soc_b__DOT__u_core__DOT__lt_s))
                                             : ((0x00001000U 
                                                 & vlSelfRef.soc_b__DOT__mem_rdata)
                                                 ? 
                                                (vlSelfRef.soc_b__DOT__u_core__DOT__rv1 
                                                 << (::IData)(soc_b__DOT__u_core__DOT__shamt))
                                                 : 
                                                ((::IData)(
                                                           (0x40000033U 
                                                            == 
                                                            (0x4000007fU 
                                                             & vlSelfRef.soc_b__DOT__mem_rdata)))
                                                  ? 
                                                 (vlSelfRef.soc_b__DOT__u_core__DOT__rv1 
                                                  - soc_b__DOT__u_core__DOT__alu_b)
                                                  : 
                                                 (vlSelfRef.soc_b__DOT__u_core__DOT__rv1 
                                                  + soc_b__DOT__u_core__DOT__alu_b))))) 
                                       & (- (::IData)(
                                                      (3U 
                                                       == 
                                                       (3U 
                                                        & vlSelfRef.soc_b__DOT__mem_rdata)))));
    vlSelfRef.soc_b__DOT__u_core__DOT__next_pc = ((0x6fU 
                                                   == 
                                                   (0x0000007fU 
                                                    & vlSelfRef.soc_b__DOT__mem_rdata))
                                                   ? 
                                                  (vlSelfRef.soc_b__DOT__u_core__DOT__pc 
                                                   + 
                                                   ((((0x00000ffeU 
                                                       & ((- (::IData)(
                                                                       (vlSelfRef.soc_b__DOT__mem_rdata 
                                                                        >> 0x0000001fU))) 
                                                          << 1U)) 
                                                      | (vlSelfRef.soc_b__DOT__mem_rdata 
                                                         >> 0x0000001fU)) 
                                                     << 0x00000014U) 
                                                    | ((((0x000001feU 
                                                          & (vlSelfRef.soc_b__DOT__mem_rdata 
                                                             >> 0x0000000bU)) 
                                                         | (1U 
                                                            & (vlSelfRef.soc_b__DOT__mem_rdata 
                                                               >> 0x00000014U))) 
                                                        << 0x0000000bU) 
                                                       | (0x000007feU 
                                                          & (vlSelfRef.soc_b__DOT__mem_rdata 
                                                             >> 0x00000014U)))))
                                                   : 
                                                  ((0x67U 
                                                    == 
                                                    (0x0000007fU 
                                                     & vlSelfRef.soc_b__DOT__mem_rdata))
                                                    ? 
                                                   (0xfffffffeU 
                                                    & soc_b__DOT__u_core__DOT__ld_addr)
                                                    : 
                                                   ((0x63U 
                                                     == 
                                                     (0x0000007fU 
                                                      & vlSelfRef.soc_b__DOT__mem_rdata))
                                                     ? 
                                                    ((1U 
                                                      & ((0x00004000U 
                                                          & vlSelfRef.soc_b__DOT__mem_rdata)
                                                          ? 
                                                         ((0x00002000U 
                                                           & vlSelfRef.soc_b__DOT__mem_rdata)
                                                           ? 
                                                          ((0x00001000U 
                                                            & vlSelfRef.soc_b__DOT__mem_rdata)
                                                            ? 
                                                           (~ (::IData)(soc_b__DOT__u_core__DOT__lt_u))
                                                            : (::IData)(soc_b__DOT__u_core__DOT__lt_u))
                                                           : 
                                                          ((0x00001000U 
                                                            & vlSelfRef.soc_b__DOT__mem_rdata)
                                                            ? 
                                                           (~ (::IData)(soc_b__DOT__u_core__DOT__lt_s))
                                                            : (::IData)(soc_b__DOT__u_core__DOT__lt_s)))
                                                          : 
                                                         ((~ 
                                                           (vlSelfRef.soc_b__DOT__mem_rdata 
                                                            >> 0x0000000dU)) 
                                                          & ((0x00001000U 
                                                              & vlSelfRef.soc_b__DOT__mem_rdata)
                                                              ? 
                                                             (vlSelfRef.soc_b__DOT__u_core__DOT__rv1 
                                                              != vlSelfRef.soc_b__DOT__u_core__DOT__rv2)
                                                              : 
                                                             (vlSelfRef.soc_b__DOT__u_core__DOT__rv1 
                                                              == vlSelfRef.soc_b__DOT__u_core__DOT__rv2)))))
                                                      ? 
                                                     (vlSelfRef.soc_b__DOT__u_core__DOT__pc 
                                                      + 
                                                      (((- (::IData)(
                                                                     (vlSelfRef.soc_b__DOT__mem_rdata 
                                                                      >> 0x0000001fU))) 
                                                        << 0x0000000dU) 
                                                       | ((((2U 
                                                             & (vlSelfRef.soc_b__DOT__mem_rdata 
                                                                >> 0x0000001eU)) 
                                                            | (1U 
                                                               & (vlSelfRef.soc_b__DOT__mem_rdata 
                                                                  >> 7U))) 
                                                           << 0x0000000bU) 
                                                          | ((0x000007e0U 
                                                              & (vlSelfRef.soc_b__DOT__mem_rdata 
                                                                 >> 0x00000014U)) 
                                                             | (0x0000001eU 
                                                                & (vlSelfRef.soc_b__DOT__mem_rdata 
                                                                   >> 7U))))))
                                                      : 
                                                     ((::IData)(4U) 
                                                      + vlSelfRef.soc_b__DOT__u_core__DOT__pc))
                                                     : 
                                                    ((::IData)(4U) 
                                                     + vlSelfRef.soc_b__DOT__u_core__DOT__pc))));
    __Vdfg_Regularize_718 = (::IData)(((0x00002000U 
                                        == (0x00007000U 
                                            & vlSelfRef.soc_b__DOT__mem_rdata)) 
                                       & (0U != (3U 
                                                 & vlSelfRef.soc_b__DOT__u_core__DOT__d_addr))));
    vlSelfRef.soc_b__DOT__u_core__DOT__bad = (1U & 
                                              (((0x00000040U 
                                                 & vlSelfRef.soc_b__DOT__mem_rdata)
                                                 ? 
                                                ((~ 
                                                  (vlSelfRef.soc_b__DOT__mem_rdata 
                                                   >> 5U)) 
                                                 | ((0x00000010U 
                                                     & vlSelfRef.soc_b__DOT__mem_rdata)
                                                     ? 
                                                    (((~ 
                                                       ((0x0c00U 
                                                         == 
                                                         (vlSelfRef.soc_b__DOT__mem_rdata 
                                                          >> 0x00000014U)) 
                                                        | ((0x0c80U 
                                                            == 
                                                            (vlSelfRef.soc_b__DOT__mem_rdata 
                                                             >> 0x00000014U)) 
                                                           | ((0x0c02U 
                                                               == 
                                                               (vlSelfRef.soc_b__DOT__mem_rdata 
                                                                >> 0x00000014U)) 
                                                              | (0x0c82U 
                                                                 == 
                                                                 (vlSelfRef.soc_b__DOT__mem_rdata 
                                                                  >> 0x00000014U)))))) 
                                                      & (::IData)(soc_b__DOT__u_core__DOT__is_csr)) 
                                                     | (::IData)(__Vdfg_Regularize_719))
                                                     : 
                                                    ((8U 
                                                      & vlSelfRef.soc_b__DOT__mem_rdata)
                                                      ? (::IData)(__Vdfg_Regularize_717)
                                                      : 
                                                     ((~ 
                                                       (3U 
                                                        == 
                                                        (3U 
                                                         & vlSelfRef.soc_b__DOT__mem_rdata))) 
                                                      | ((0U 
                                                          != 
                                                          (7U 
                                                           & (vlSelfRef.soc_b__DOT__mem_rdata 
                                                              >> 0x0000000cU))) 
                                                         & (vlSelfRef.soc_b__DOT__mem_rdata 
                                                            >> 2U))))))
                                                 : 
                                                ((0x00000020U 
                                                  & vlSelfRef.soc_b__DOT__mem_rdata)
                                                  ? 
                                                 ((0x00000010U 
                                                   & vlSelfRef.soc_b__DOT__mem_rdata)
                                                   ? 
                                                  (((4U 
                                                     & vlSelfRef.soc_b__DOT__mem_rdata)
                                                     ? 
                                                    (~ 
                                                     (3U 
                                                      == 
                                                      (3U 
                                                       & vlSelfRef.soc_b__DOT__mem_rdata)))
                                                     : 
                                                    (~ 
                                                     ((3U 
                                                       == 
                                                       (3U 
                                                        & vlSelfRef.soc_b__DOT__mem_rdata)) 
                                                      & ((1U 
                                                          == 
                                                          (vlSelfRef.soc_b__DOT__mem_rdata 
                                                           >> 0x00000019U)) 
                                                         | ((0U 
                                                             == 
                                                             (vlSelfRef.soc_b__DOT__mem_rdata 
                                                              >> 0x00000019U)) 
                                                            | ((0x20U 
                                                                == 
                                                                (vlSelfRef.soc_b__DOT__mem_rdata 
                                                                 >> 0x00000019U)) 
                                                               & ((5U 
                                                                   == 
                                                                   (7U 
                                                                    & (vlSelfRef.soc_b__DOT__mem_rdata 
                                                                       >> 0x0000000cU))) 
                                                                  | (0U 
                                                                     == 
                                                                     (7U 
                                                                      & (vlSelfRef.soc_b__DOT__mem_rdata 
                                                                         >> 0x0000000cU)))))))))) 
                                                   | (vlSelfRef.soc_b__DOT__mem_rdata 
                                                      >> 3U))
                                                   : (::IData)(__Vdfg_Regularize_719))
                                                  : 
                                                 ((0x00000010U 
                                                   & vlSelfRef.soc_b__DOT__mem_rdata)
                                                   ? 
                                                  ((~ 
                                                    (3U 
                                                     == 
                                                     (3U 
                                                      & vlSelfRef.soc_b__DOT__mem_rdata))) 
                                                   | (vlSelfRef.soc_b__DOT__mem_rdata 
                                                      >> 3U))
                                                   : 
                                                  ((8U 
                                                    & vlSelfRef.soc_b__DOT__mem_rdata)
                                                    ? (::IData)(__Vdfg_Regularize_717)
                                                    : 
                                                   ((vlSelfRef.soc_b__DOT__mem_rdata 
                                                     >> 2U) 
                                                    | ((~ 
                                                        (3U 
                                                         == 
                                                         (3U 
                                                          & vlSelfRef.soc_b__DOT__mem_rdata))) 
                                                       | ((6U 
                                                           == 
                                                           (7U 
                                                            & (vlSelfRef.soc_b__DOT__mem_rdata 
                                                               >> 0x0000000cU))) 
                                                          | ((3U 
                                                              == 
                                                              (7U 
                                                               & (vlSelfRef.soc_b__DOT__mem_rdata 
                                                                  >> 0x0000000cU))) 
                                                             | (7U 
                                                                == 
                                                                (7U 
                                                                 & (vlSelfRef.soc_b__DOT__mem_rdata 
                                                                    >> 0x0000000cU))))))))))) 
                                               | ((((3U 
                                                     == 
                                                     (0x0000007fU 
                                                      & vlSelfRef.soc_b__DOT__mem_rdata))
                                                     ? 
                                                    (((1U 
                                                       == 
                                                       (7U 
                                                        & (vlSelfRef.soc_b__DOT__mem_rdata 
                                                           >> 0x0000000cU))) 
                                                      | (5U 
                                                         == 
                                                         (7U 
                                                          & (vlSelfRef.soc_b__DOT__mem_rdata 
                                                             >> 0x0000000cU))))
                                                      ? vlSelfRef.soc_b__DOT__u_core__DOT__d_addr
                                                      : (::IData)(__Vdfg_Regularize_718))
                                                     : 
                                                    ((1U 
                                                      == 
                                                      (7U 
                                                       & (vlSelfRef.soc_b__DOT__mem_rdata 
                                                          >> 0x0000000cU)))
                                                      ? vlSelfRef.soc_b__DOT__u_core__DOT__d_addr
                                                      : (::IData)(__Vdfg_Regularize_718))) 
                                                   & (::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__acc_data)) 
                                                  | (::IData)(
                                                              (0x00000073U 
                                                               == 
                                                               (0x0000707fU 
                                                                & vlSelfRef.soc_b__DOT__mem_rdata))))));
    vlSelfRef.__Vdfg_Regularize_712 = ((~ ((::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__bad) 
                                           | ((::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__acc_data) 
                                              | ((::IData)(vlSelfRef.soc_b__DOT__u_core__DOT__is_muldiv) 
                                                 | (0U 
                                                    == 
                                                    (0x0000001fU 
                                                     & (vlSelfRef.soc_b__DOT__mem_rdata 
                                                        >> 7U))))))) 
                                       & ((0x00000040U 
                                           & vlSelfRef.soc_b__DOT__mem_rdata)
                                           ? (((0x00000010U 
                                                & vlSelfRef.soc_b__DOT__mem_rdata)
                                                ? (::IData)(
                                                            ((3U 
                                                              == 
                                                              (0x0000000fU 
                                                               & vlSelfRef.soc_b__DOT__mem_rdata)) 
                                                             & (::IData)(soc_b__DOT__u_core__DOT__is_csr)))
                                                : (::IData)(
                                                            (7U 
                                                             == 
                                                             (7U 
                                                              & vlSelfRef.soc_b__DOT__mem_rdata)))) 
                                              & (vlSelfRef.soc_b__DOT__mem_rdata 
                                                 >> 5U))
                                           : ((vlSelfRef.soc_b__DOT__mem_rdata 
                                               >> 4U) 
                                              & (::IData)(vlSelfRef.__Vdfg_Regularize_716))));
}

bool Vsoc_b___024root___trigger_anySet__ico(const ::VlUnpacked<::QData/*63:0*/, 2> &in);

#ifdef VL_DEBUG
VL_ATTR_COLD void Vsoc_b___024root___dump_triggers__ico(const ::VlUnpacked<::QData/*63:0*/, 2> &triggers, const ::std::string &tag) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vsoc_b___024root___dump_triggers__ico\n"); );
    // Body
    if ((1U & (~ (::IData)(Vsoc_b___024root___trigger_anySet__ico(triggers))))) {
        VL_DBG_MSGS("         No '" + tag + "' region triggers active\n");
    }
    if ((1U & (::IData)(triggers[0U]))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 0 is active: @( clk)\n");
    }
    if ((1U & (::IData)((triggers[0U] >> 1U)))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 1 is active: @( resetn)\n");
    }
    if ((1U & (::IData)((triggers[0U] >> 2U)))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 2 is active: @( uart_rx)\n");
    }
    if ((1U & (::IData)(triggers[1U]))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 64 is active: Internal 'ico' trigger - first iteration\n");
    }
}
#endif  // VL_DEBUG

bool Vsoc_b___024root___trigger_anySet__act(const ::VlUnpacked<::QData/*63:0*/, 1> &in);

#ifdef VL_DEBUG
VL_ATTR_COLD void Vsoc_b___024root___dump_triggers__act(const ::VlUnpacked<::QData/*63:0*/, 1> &triggers, const ::std::string &tag) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vsoc_b___024root___dump_triggers__act\n"); );
    // Body
    if ((1U & (~ (::IData)(Vsoc_b___024root___trigger_anySet__act(triggers))))) {
        VL_DBG_MSGS("         No '" + tag + "' region triggers active\n");
    }
    if ((1U & (::IData)(triggers[0U]))) {
        VL_DBG_MSGS("         '" + tag + "' region trigger index 0 is active: @(posedge clk)\n");
    }
}
#endif  // VL_DEBUG

VL_ATTR_COLD void Vsoc_b___024root___ctor_var_reset(Vsoc_b___024root* vlSelf) {
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vsoc_b___024root___ctor_var_reset\n"); );
    Vsoc_b__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    auto& vlSelfRef = std::ref(*vlSelf).get();
    // Body
    const uint64_t __VscopeHash = VL_MURMUR64_HASH(vlSelf->vlNamep);
    vlSelf->__VprimaryPorts.clk = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 16707436170211756652ull);
    vlSelf->__VprimaryPorts.resetn = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 8624841754543469506ull);
    vlSelf->__VprimaryPorts.uart_tx = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 1761512799854230840ull);
    vlSelf->__VprimaryPorts.uart_rx = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 2399467654730215438ull);
    vlSelf->__VprimaryPorts.led = VL_SCOPED_RAND_RESET_I(6, __VscopeHash, 14009161575225144129ull);
    vlSelf->__VprimaryPorts.dbg_tx_valid = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 3708476144463707885ull);
    vlSelf->__VprimaryPorts.dbg_tx_byte = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 8032316398146771299ull);
    vlSelf->__VprimaryPorts.dbg_trap = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 3973858979703362152ull);
    vlSelf->soc_b__DOT__mem_rdata = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 11722589530922572271ull);
    for (int __Vi0 = 0; __Vi0 < 16384; ++__Vi0) {
        vlSelf->soc_b__DOT__ram[__Vi0] = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 15757993959643410425ull);
    }
    vlSelf->soc_b__DOT__ram_q = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 14841621830797357757ull);
    vlSelf->soc_b__DOT__tx_byte = VL_SCOPED_RAND_RESET_I(8, __VscopeHash, 6794925549481847099ull);
    vlSelf->soc_b__DOT__tx_start = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 7043756594884600373ull);
    vlSelf->soc_b__DOT__sel_ram_q = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 1176214116555800454ull);
    vlSelf->soc_b__DOT__per_q = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 13853861027028782684ull);
    vlSelf->soc_b__DOT__u_core__DOT__mem_valid = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 5192211788865856065ull);
    vlSelf->soc_b__DOT__u_core__DOT__state = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 3246755886304329961ull);
    vlSelf->soc_b__DOT__u_core__DOT__addr_r = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 6279880217136444880ull);
    vlSelf->soc_b__DOT__u_core__DOT__wdata_r = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 7010623258062311422ull);
    vlSelf->soc_b__DOT__u_core__DOT__wstrb_r = VL_SCOPED_RAND_RESET_I(4, __VscopeHash, 15853927902233429508ull);
    vlSelf->soc_b__DOT__u_core__DOT__valid_r = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 3650184756765937633ull);
    vlSelf->soc_b__DOT__u_core__DOT__pc = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 8297742831797239219ull);
    vlSelf->soc_b__DOT__u_core__DOT__pc_ret = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 144203259657389820ull);
    for (int __Vi0 = 0; __Vi0 < 32; ++__Vi0) {
        vlSelf->soc_b__DOT__u_core__DOT__regs[__Vi0] = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 6705421414210051326ull);
    }
    vlSelf->soc_b__DOT__u_core__DOT__rv1 = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 2024891927278844808ull);
    vlSelf->soc_b__DOT__u_core__DOT__rv2 = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 9523726580779545171ull);
    vlSelf->soc_b__DOT__u_core__DOT__d_addr = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 2384419088745713398ull);
    vlSelf->soc_b__DOT__u_core__DOT__ld_f3 = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 1571178252723834892ull);
    vlSelf->soc_b__DOT__u_core__DOT__ld_off = VL_SCOPED_RAND_RESET_I(2, __VscopeHash, 1600409768328046418ull);
    vlSelf->soc_b__DOT__u_core__DOT__ld_rd = VL_SCOPED_RAND_RESET_I(5, __VscopeHash, 8700139843244359542ull);
    vlSelf->soc_b__DOT__u_core__DOT__ld_is = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 1456404853865279703ull);
    vlSelf->soc_b__DOT__u_core__DOT__cnt_cycle = VL_SCOPED_RAND_RESET_Q(64, __VscopeHash, 5818200650992215046ull);
    vlSelf->soc_b__DOT__u_core__DOT__cnt_instret = VL_SCOPED_RAND_RESET_Q(64, __VscopeHash, 1405384240313425069ull);
    vlSelf->soc_b__DOT__u_core__DOT__md_a = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 5872513638157717571ull);
    vlSelf->soc_b__DOT__u_core__DOT__md_b = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 5384185125827206706ull);
    vlSelf->soc_b__DOT__u_core__DOT__md_f3 = VL_SCOPED_RAND_RESET_I(3, __VscopeHash, 10531804070993632164ull);
    vlSelf->soc_b__DOT__u_core__DOT__md_rd = VL_SCOPED_RAND_RESET_I(5, __VscopeHash, 10307991585172644287ull);
    vlSelf->soc_b__DOT__u_core__DOT__md_cnt = VL_SCOPED_RAND_RESET_I(6, __VscopeHash, 656745921499416824ull);
    vlSelf->soc_b__DOT__u_core__DOT__md_is_div = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 11375943702525764068ull);
    vlSelf->soc_b__DOT__u_core__DOT__prod_u = VL_SCOPED_RAND_RESET_Q(64, __VscopeHash, 12276967786929282887ull);
    vlSelf->soc_b__DOT__u_core__DOT__dvd = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 810002824633864349ull);
    vlSelf->soc_b__DOT__u_core__DOT__dvs = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 15576915444125944514ull);
    vlSelf->soc_b__DOT__u_core__DOT__quo = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 14431281237632641689ull);
    vlSelf->soc_b__DOT__u_core__DOT__rmd = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 410628892467305616ull);
    vlSelf->soc_b__DOT__u_core__DOT__q_neg = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 12537849490616259477ull);
    vlSelf->soc_b__DOT__u_core__DOT__r_neg = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 7733207335727776277ull);
    vlSelf->soc_b__DOT__u_core__DOT__rmd_sh = VL_SCOPED_RAND_RESET_Q(33, __VscopeHash, 9022415428266691460ull);
    vlSelf->soc_b__DOT__u_core__DOT__rmd_ge = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 11150800896517924111ull);
    vlSelf->soc_b__DOT__u_core__DOT__div_signed_d = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 12825440977057786386ull);
    vlSelf->soc_b__DOT__u_core__DOT__is_muldiv = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 7271989926162456301ull);
    vlSelf->soc_b__DOT__u_core__DOT__next_pc = VL_SCOPED_RAND_RESET_I(32, __VscopeHash, 14927134857514038884ull);
    vlSelf->soc_b__DOT__u_core__DOT__acc_data = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 3502494875915170544ull);
    vlSelf->soc_b__DOT__u_core__DOT__bad = VL_SCOPED_RAND_RESET_I(1, __VscopeHash, 13218137375517266230ull);
    vlSelf->__Vdfg_Regularize_706 = 0;
    vlSelf->__Vdfg_Regularize_707 = 0;
    vlSelf->__Vdfg_Regularize_710 = 0;
    vlSelf->__Vdfg_Regularize_711 = 0;
    vlSelf->__Vdfg_Regularize_712 = 0;
    vlSelf->__Vdfg_Regularize_714 = 0;
    vlSelf->__Vdfg_Regularize_715 = 0;
    vlSelf->__Vdfg_Regularize_716 = 0;
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->__VstlTriggered[__Vi0] = 0;
    }
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->__VicoTriggered[__Vi0] = 0;
    }
    vlSelf->__Vtrigprevexpr___TOP__clk__0 = 0;
    vlSelf->__Vtrigprevexpr___TOP__resetn__0 = 0;
    vlSelf->__Vtrigprevexpr___TOP__uart_rx__0 = 0;
    vlSelf->__VicoDidInit = 0;
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->__VactTriggered[__Vi0] = 0;
    }
    vlSelf->__Vtrigprevexpr___TOP__clk__1 = 0;
    for (int __Vi0 = 0; __Vi0 < 1; ++__Vi0) {
        vlSelf->__VnbaTriggered[__Vi0] = 0;
    }
}
