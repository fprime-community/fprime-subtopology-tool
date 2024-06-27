module st {
    instance a: Components.A base id 0x1000

    instance b: Components.B base id 0x2000 \
        queue size 100 \
        stack size 200 \
        priority 300

    instance c: Components.C base id 0x3000 \
        queue size 100

    instance Input: ExampleInterface.Input base id 0x4000
    instance Output: ExampleInterface.Output base id 0x5000

    topology st {
        @! is local
        instance st.a

        @! is local
        instance st.b

        @! is local
        instance st.c

        @! is interface input
        instance st.Input

        @! is interface output
        instance st.Output

        connections Interface {
            st.a.out -> st.b.in
            st.Input.clock_in -> st.c.in
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
    queue size 100 \
    stack size 100 \
    priority 100

  instance main_c: Components.C base id 0xCD \
    queue size 100

  topology main {

    import MyST



    instance main_a

    include "./MyST_interface.fppi"

  }

}
instance __MyST_instances.c

connections Interface_MyST {
    main_a.out -> __MyST_instances.c.in

}
