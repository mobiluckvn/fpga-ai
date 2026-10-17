// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vsoc_b.h for the primary calling header

#include "Vsoc_b__pch.h"

void Vsoc_b___024root___ctor_var_reset(Vsoc_b___024root* vlSelf);

void Vsoc_b___024root__ctor(Vsoc_b___024root* vlSelf, Vsoc_b__Syms* symsp, const char* namep) {
    vlSelf->vlSymsp = symsp;
    vlSelf->vlNamep = strdup(namep);
    // Construct members
    // Reset structure values
    Vsoc_b___024root___ctor_var_reset(vlSelf);
}

Vsoc_b___024root::Vsoc_b___024root(Vsoc_b__Syms* symsp, const char* namep) {
    Vsoc_b___024root__ctor(this, symsp, namep);
}

void Vsoc_b___024root__dtor(Vsoc_b___024root* vlSelf) {
    // Destroy members
    VL_DO_DANGLING(std::free(const_cast<char*>(vlSelf->vlNamep)), vlSelf->vlNamep);
}

Vsoc_b___024root::~Vsoc_b___024root() {
    Vsoc_b___024root__dtor(this);
}
