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
        @! is local
        instance st.a

        @! is local
        instance st.b

        @! is local
        instance st.c

        connections Testing {
            st.a.pout -> st.b.pin
            st.b.pout -> st.c.pin
        }
    }
}locate constant main.__MyST_instances.LOCAL_BASE_ID at "out.out.fpp"

locate instance main.__MyST_instances.a at "out.out.fpp"

locate instance main.__MyST_instances.b at "out.out.fpp"

locate instance main.__MyST_instances.c at "out.out.fpp"

locate topology main.MyST at "out.out.fpp"
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
    }
}