module st {
    instance a: Components.A base id Components.A + 0x1000 + Constant.C

    instance b: Components.B base id 0x2000 \
        queue size stConfig.Defaults.QUEUE_SIZE \
        stack size stConfig.Defaults.STACK_SIZE \
        priority stConfig.Priorities.b \
        {
            phase Fpp.ToCpp.Phases.configObjects """
                std::cout << "testing" << std::endl;
            """
        }

    instance c: Components.C base id 0x3000 \
        queue size stConfig.Defaults.QUEUE_SIZE

    topology st {
        instance st.a
        instance st.b
        instance st.c

        connections Testing {
            st.a.pout -> st.b.pin
            st.b.pout -> st.c.pin
        }
    }
}locate topology main.MyST at "out.out.fpp"

locate topology main.MyST2 at "out.out.fpp"

locate topology main.MyST3 at "out.out.fpp"
module main {
    instance main_a: Components.A base id 0xAB
    instance b: Components.B base id 0xBC \
        queue size Defaults.QUEUE_SIZE \
        stack size Defaults.STACK_SIZE \
        priority 100
    instance main_c: Components.C base id 0xCD \
        queue size Defaults.QUEUE_SIZE
    




    topology main {
        import MyST
        import MyST2
        import MyST3
    }
}