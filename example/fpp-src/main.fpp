module main {
    instance main_a: Components.A base id 0xAB
    instance b: Components.B base id 0xBC \
        queue size Defaults.QUEUE_SIZE \
        stack size Defaults.STACK_SIZE \
        priority 100
    instance main_c: Components.C base id 0xCD \
        queue size Defaults.QUEUE_SIZE
    
    topology MyST {}
    @<! is st.st base id 0xCCCC with {
    @<!    st.a = main.main_a    
    @<! }

    topology main {
        import st.MyST
    }
}