module main {

  module __MyST_instances {

    constant LOCAL_BASE_ID = 0xCCCC

    instance a: Components.A base id 0x1000 + LOCAL_BASE_ID

    instance b: Components.B base id 0x2000 + LOCAL_BASE_ID \
      queue size 100 \
      stack size 200 \
      priority 300

    instance c: Components.C base id 0x3000 + LOCAL_BASE_ID \
      queue size 100

  }

  topology MyST {

    instance __MyST_instances.a

    instance __MyST_instances.b

    instance __MyST_instances.c

    instance st.Input

    instance st.Output

  }

}
