// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Symbol table internal header
//
// Internal details; most calling programs do not need this header,
// unless using verilator public meta comments.

#ifndef VERILATED_VSOC_B__SYMS_H_
#define VERILATED_VSOC_B__SYMS_H_  // guard

#include "verilated.h"

// INCLUDE MODEL CLASS

#include "Vsoc_b.h"

// INCLUDE MODULE CLASSES
#include "Vsoc_b___024root.h"

// SYMS CLASS (contains all model state)
class alignas(VL_CACHE_LINE_BYTES) Vsoc_b__Syms final : public VerilatedSyms {
  public:
    // INTERNAL STATE
    Vsoc_b* const __Vm_modelp;
    VlDeleter __Vm_deleter;
    bool& __Vm_didInit;

    // MODULE INSTANCE STATE
    union {
        struct {
            Vsoc_b___024root               TOP;
        } vlInst;
    };

    // CONSTRUCTORS
    Vsoc_b__Syms(VerilatedContext* contextp, const char* namep, Vsoc_b* modelp);
    ~Vsoc_b__Syms();

    // METHODS
    const char* name() const { return vlInst.TOP.vlNamep; }
};

#endif  // guard
