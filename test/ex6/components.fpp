module Components {
    port P (
        m_main: U32
    )
    passive component A {
        sync input port in: Components.P
        output port out: Components.P
    }
    active component B {
        async input port in: Components.P
        output port out: Components.P
    }
    queued component C {
        async input port in: Components.P
        output port out: Components.P
    }
}