module main {

  module st {

    topology MyST {

      instance st.a

      instance st.b

      instance st.c

      connections Testing {
        st.a.pout -> st.b.pin
        st.b.pout -> st.c.pin
      }

    }

  }

}

module main {

  module st {

    topology MyST2 {

      instance st.a

      instance main.b

      instance st.c

      connections Testing {
        st.a.pout -> main.b.pin
        main.b.pout -> st.c.pin
      }

    }

  }

}

module main {

  module st {

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
locate topology main.st.MyST at "out.out.fpp"

locate topology main.st.MyST2 at "out.out.fpp"

locate topology main.st.MyST3 at "out.out.fpp"
