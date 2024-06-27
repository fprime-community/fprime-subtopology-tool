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
}