module st {
    instance a: Components.A base id 0x1000

    instance b: Components.B base id 0x2000 \
        queue size 100 \
        stack size 200 \
        priority 300

    instance c: Components.C base id 0x3000 \
        queue size 100

    topology st {
        @! is local
        instance st.a

        @! is local
        instance st.b

        instance st.c

        connections Testing {
            st.a.out -> st.b.in
            st.b.out -> st.c.in
        }
    }
}