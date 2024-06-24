module main {
    instance main_a: Components.A base id 0xAB
    instance b: Components.B base id 0xBC \
        queue size 100 \
        stack size 100 \
        priority 100
    instance main_c: Components.C base id 0xCD \
        queue size 100
    
    topology MyST {}
    @<! is st.st base id 0xCCCC

    topology main {
        import MyST
    }
}