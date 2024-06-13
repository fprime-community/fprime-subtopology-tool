module MainDeployment {

  module RNGTopology {

    topology TestingTopology {

      instance inputs

      instance outputs

      instance rng

      instance rateGroup

      connections Interface {
        inputs.clock -> rng.run
        rng.rngVal -> outputs.RNGValue
      }

    }

  }

}
