module main {

  module __MyST_instances {

    constant LOCAL_BASE_ID = 0xCCCC

    instance a: Components.A base id Components.A + 0x1000 + Constant.C + LOCAL_BASE_ID

    instance b: Components.B base id 0x2000 + LOCAL_BASE_ID \
      queue size stConfig.Defaults.QUEUE_SIZE \
      stack size stConfig.Defaults.STACK_SIZE \
      priority stConfig.Priorities.b \
      {
        phase Fpp.ToCpp.Phases.configObjects "std::cout << \"testing\" << std::endl;"
      }

    instance c: Components.C base id 0x3000 + LOCAL_BASE_ID \
      queue size stConfig.Defaults.QUEUE_SIZE

  }

  module st {

    topology MyST {

      instance __MyST_instances.a

      instance __MyST_instances.b

      instance __MyST_instances.c

      connections Testing {
        st.a.pout -> st.b.pin
        st.b.pout -> st.c.pin
      }

    }

  }

}
locate constant main.__MyST_instances.LOCAL_BASE_ID at "out.out.fpp"

locate instance main.__MyST_instances.a at "out.out.fpp"

locate instance main.__MyST_instances.b at "out.out.fpp"

locate instance main.__MyST_instances.c at "out.out.fpp"

locate topology main.st.MyST at "out.out.fpp"
