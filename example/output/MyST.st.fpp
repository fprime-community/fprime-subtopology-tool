module main {

  module __MyST_instances {

    constant LOCAL_BASE_ID = 0xCCCC

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

      instance main.main_a

      instance __MyST_instances.b

      instance __MyST_instances.c

      connections Testing {
        main.main_a.pout -> __MyST_instances.b.pin
        __MyST_instances.b.pout -> __MyST_instances.c.pin
      }

    }

  }

}
