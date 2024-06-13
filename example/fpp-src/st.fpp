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
}