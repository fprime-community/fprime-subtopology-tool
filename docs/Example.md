# Subtopology AC Worked Example

The following document provides a worked example of a project that uses the subtopology autocoder tool. This document assumes that you have an F Prime project set up, and have followed the [installation instructions](./README.md#installation).

1. [Context](#context)
2. [The library](#the-library)
    - [RNG Component](#rng-component)
    - [RNGTopology](#rngtopology)
3. [External components (hardware, receiver)](#external-components-hardware-receiver)
4. [Deployment and subtopology instantiation](#deployment-and-subtopology-instantiation)
5. [Build and Conclusion](#build-and-conclusion)

## Context

In this example, we will emulate a typical hardware interface with software behavior. We will create three components: the hardware, the data processor, and a receiver. Since we will do this all via software, the hardware component will just pass randomly generated numbers to the data processor on a clock cycle. The data processor will "process" the data, and return the resultant number to the receiver, which will output the data as an event.

The subtopology in our situation will be the wiring between the hardware, data processor and receiver. This subtopology then drops into our main deployment.

## The library

The library will include our subtopology, and also our data processor component, as it is a local component and is best scoped in the library itself. The structure of the library folder is as follows:

```bash
RNGLibrary/
├── library.cmake
├── CMakeLists.txt
├── RNG/
│   ├── RNG.fpp
│   ├── RNG.cpp
│   ├── RNG.hpp
│   └── ...
└── RNGTopology/
    ├── intentionally-empty.cpp
    ├── CMakeLists.txt
    ├── RNGTopology.fpp
    ├── RNGTopologyConfig.fpp
    └── RNGTopologyTopologyDefs.hpp
```

> The `intentionally-empty.cpp` file is a necessary inclusion if you run `fprime-util build --all`. This is to tell the build system to replace the output of the build of this module with empty files to solve an issue with naming of subtopologies from fpp. However, if you run `fprime-util build` (as normal), you do not need this file. 

`RNG` is a component, which can be generated using `fprime-util new --component`. `RNGTopology` is the subtopology that will be instantiated later.

### RNG Component

The RNG component will be our data process. It will have an input port to accept data, and a port that outputs that data. It will also have a command that sets a random seed if the user would like. The component also defines a function that will be called on configuration of the component to set an initial seed.

```
# in RNG.fpp

module RNGLibrary {
    @ A component that releases random numbers to the GDS. Connected to a rate group.
    active component RNG {

        # command to set RNG seed
        async command SET_RNG_SEED(seed: U32)
        
        # telemetry from the component
        telemetry DataIn: U32
        telemetry RNGSeed: U32

        sync input port data: RNGTopologyConfig.MessagePort
        output port processed: RNGTopologyConfig.MessagePort
    }

    ...
}

# in RNGTopologyConfig

module RNGTopologyConfig {
    module Defaults {
        constant QUEUE_SIZE = 10
        constant STACK_SIZE = 64 * 1024
    }

    port MessagePort(
        m_message: U32
    )
}
```

It is up to your discretion what goes on in the RNG component, however at minimum, set a value out to the processed port (`this->processed_out(0, message_final);`) in the `data_handler` function, and define a function called "set_initial_seed()":

```cpp
// in RNG.hpp

public:
      void set_initial_seed(U32 seed);

// in RNG.cpp

void RNG :: 
set_initial_seed(U32 seed) {
    std::srand(seed);
}
```

### RNGTopology

We now want to create our subtopology. Start by filling in the CMakeLists.txt file:

```cmake
set(SOURCE_FILES
    "${CMAKE_CURRENT_LIST_DIR}/RNGTopology.fpp"
    "${CMAKE_CURRENT_LIST_DIR}/intentionally-empty.cpp"
)

register_fprime_module()

set_target_properties(
    ${FPRIME_CURRENT_MODULE}
    PROPERTIES
    SOURCES "${CMAKE_CURRENT_LIST_DIR}/intentionally-empty.cpp"
)
```

In `RNGTopology.fpp`, we will define our local instance of our data processor, which needs to be specially configured when our flight software boots up. We achieve this with [fpp Phases](https://nasa.github.io/fpp/fpp-users-guide.html#Defining-Component-Instances_Init-Specifiers_Execution-Phases).

```
# in RNGTopology.fpp

module RNGTopology {
    instance rng: RNGLibrary.RNG base id 0x4444 \
        queue size RNGTopologyConfig.Defaults.QUEUE_SIZE \
        stack size RNGTopologyConfig.Defaults.STACK_SIZE \
        priority 100 \
        {
            phase Fpp.ToCpp.Phases.configComponents """
                RNGTopology_rng.set_initial_seed(state.RNGTopology_state.initialSeed);
            """
        }

    topology RNG {
        @! is local
        instance RNGTopology.rng

        instance receiver
        instance hardware

        connections Topology {
            RNGTopology.rng.processed -> receiver.received
            hardware.data -> RNGTopology.rng.data
        }
    } # end topology
} # end RNGTopology
```

As you may see, we see our magic annotations finally show up, with `rng` being defined as a local component. This refrains it from being overwritten. `receiver` and `hardware` are instance specifications that are left undefined, which is because we are not concerned about this subtopology building by itself. These two instances will be replaced later when we instantiate our subtopology.

The last step is to fill in out `RNGTopologyTopologyDefs.hpp` file, which will include the topology state struct that you can see is in our phase. It also could include any other definitions that may be required for our subtopology.

```cpp

// in RNGTopologyTopologyDefs.hpp

#ifndef RNGTOPOLOGY_DEFS_HPP
#define RNGTOPOLOGY_DEFS_HPP

namespace RNGTopology
{
    struct RNGTopologyState {
        U32 initialSeed;
    };

    struct TopologyState {
        RNGTopologyState RNGTopology_state;
    };
}

#endif
```

## External components (hardware, receiver)

We now want to create our external components. These are example components of what the user may provide, where `hardware` is like a hardware interface driver, and `receiver` is a component that utilizes the output of our subtopology.

Create two components (i.e., Hardware and Receiver) that are defined as such:

```
# in Hardware.fpp, model file for Hardware component

module Components {
    @ Software simulated hardware
    active component Hardware {

        async input port run: Svc.Sched
        output port data: RNGTopologyConfig.MessagePort

        telemetry HardwareData: U32

        ...
    }
}

# in Receiver.fpp, model file for Receiver component

module Components {
    @ Receives data and presents it as telemetry
    active component Receiver {

        async input port received: RNGTopologyConfig.MessagePort
        event ReceivedData(value:U32) severity activity high id 0 format "Received data: {}"
    }
}
```

In `Hardware`, you should pass the `data` output port some data in the `run_handler` function. In `Receiver`, you should send the received data out to the `ReceivedData` event.

## Deployment and Subtopology instantiation

We now want to create an instance of our `RNG` topology inside a main topology, which will be the topology of a deployment we create. 

Create a deployment (`fprime-util new --deployment`), and within `<YourDeployment>/Top/instances.fpp`, define instances of the `Hardware` and `Receiver` components. For the sake of this context, assume `<YourDeployment> = MainDeployment`

```
# in MainDeployment/Top/instances.fpp

...

instance hardware: Components.Hardware base id 0x0E00 \
    queue size Default.QUEUE_SIZE \
    stack size Default.STACK_SIZE \
    priority 95

instance receiver: Components.Receiver base id 0x0F00 \
    queue size Default.QUEUE_SIZE \
    stack size Default.STACK_SIZE \
    priority 94

...
```

Within `MainDeployment/Top/topology.fpp`, we are now going to create the instance of the subtopology `RNG`. We will replace `receiver` and `hardware` in the subtopology with `MainDeployment.hardware` and `MainDeployment.receiver`.

```
# in MainDeployment/Top/topology.fpp

module MainDeployment {

    ...

    constant Testing = {}
    @<! is topology RNGTopology.RNG base id 0xCCCC with {
    @<!    hardware = MainDeployment.hardware,
    @<!    receiver = MainDeployment.receiver
    @<! }

    ...

    topology MainDeployment {
        import RNG.Testing

        ... # make sure to hook up MainDeployment.hardware.run to a rate group's output port!
    }

}
```

The last step is that in our `MainDeployment/Top` directory, we want to create a topology definitions file for our instantiated subtopology. Each subtopology instance requires its own instance, but it can be simplified to include parts from the subtopology's topology definitions file. This part was not automated as the user may want access to this header file to make modifications and add configuration changes on a case-by-case basis.

```cpp

// create TestingTopologyDefs.hpp in MainDeployment/Top

#include "RNGLibrary/RNGTopology/RNGTopologyTopologyDefs.hpp"

#ifndef TESTINGTOPOLOGY_DEFS_HPP
#define TESTINGTOPOLOGY_DEFS_HPP

using TopologyState = RNGTopology::TopologyState;

// ... your own configuration

#endif
```

## Build and Conclusion

You're all set to now build your deployment! It is recommended to purge your build cache and generate from scratch, but it is not required. After that, you can run build, and you should have a working deployment!

```bash
# purge (optional)
fprime-util purge # answer with "yes"

# generate
fprime-util generate # you optionally may need -DFPRIME_SKIP_TOOLS_VERSION_CHECK=ON if you have developer versions of fprime/fpp/etc

# build, in MainDeployment
fprime-util build

```

To test your build, you can run the `fprime-gds` in place.

```bash
# you may need to manually define your dictionary if GDS starts and loads partially
fprime-gds --dictionary path/to/MainDeploymentAppDictionary.xml
```

This example was meant to provide a minimal use case for subtopologies. This tool aims to improve the abtraction of F Prime projects and behaviors. If you would like to view the completed example, it is available at [github:mosa11aei/fprime-rngLibrary](https://github.com/mosa11aei/fprime-rngLibrary/tree/example/st-instances).
