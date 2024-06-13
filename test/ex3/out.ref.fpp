module main {

  module __MyST_instances {

    constant LOCAL_BASE_ID = 0xCCCC

    instance a: Components.A base id Components.A + 0x1000 + Constant.C + LOCAL_BASE_ID

    instance c: Components.C base id 0x3000 + LOCAL_BASE_ID \
      queue size stConfig.Defaults.QUEUE_SIZE

  }

  module st {

    topology MyST {

      instance __MyST_instances.a

      instance st.b

      instance __MyST_instances.c

      connections Testing {
        st.a.pout -> st.b.pin
        st.b.pout -> st.c.pin
      }

    }

  }

}

module main {

  module __MyST2_instances {

    constant LOCAL_BASE_ID = 0xDDDD

    instance a: Components.A base id Components.A + 0x1000 + Constant.C + LOCAL_BASE_ID

  }

  module st {

    topology MyST2 {

      instance __MyST2_instances.a

      instance st.b

      instance main_a

      connections Testing {
        __MyST2_instances.a.pout -> st.b.pin
        st.b.pout -> main_a.pin
      }

    }

  }

}
