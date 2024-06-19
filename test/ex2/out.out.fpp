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

  module local {

    topology MyST {

      instance __MyST_instances.a

      instance __MyST_instances.b

      instance __MyST_instances.c

      connections Testing {
        __MyST_instances.a.pout -> __MyST_instances.b.pin
        __MyST_instances.b.pout -> __MyST_instances.c.pin
      }

    }

  }

}

module main {

  module __MyST2_instances {

    constant LOCAL_BASE_ID = 0xDDDD

    instance a: Components.A base id Components.A + 0x1000 + Constant.C + LOCAL_BASE_ID

    instance c: Components.C base id 0x3000 + LOCAL_BASE_ID \
      queue size stConfig.Defaults.QUEUE_SIZE

  }

  module local {

    topology MyST2 {

      instance __MyST2_instances.a

      instance main.b

      instance __MyST2_instances.c

      connections Testing {
        __MyST2_instances.a.pout -> main.b.pin
        main.b.pout -> __MyST2_instances.c.pin
      }

    }

  }

}

module main {

  module local {

    topology MyST3 {

      instance main.main_a

      instance main.b

      instance main.main_c

      connections Testing {
        main.main_a.pout -> main.b.pin
        main.b.pout -> main.main_c.pin
      }

    }

  }

}
locate constant main.__MyST2_instances.LOCAL_BASE_ID at "out.out.fpp"

locate constant main.__MyST_instances.LOCAL_BASE_ID at "out.out.fpp"

locate instance main.__MyST2_instances.a at "out.out.fpp"

locate instance main.__MyST2_instances.c at "out.out.fpp"

locate instance main.__MyST_instances.a at "out.out.fpp"

locate instance main.__MyST_instances.b at "out.out.fpp"

locate instance main.__MyST_instances.c at "out.out.fpp"

locate topology main.local.MyST at "out.out.fpp"

locate topology main.local.MyST2 at "out.out.fpp"

locate topology main.local.MyST3 at "out.out.fpp"
