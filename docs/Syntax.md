# Syntax for the Subtopology AC Tool

Before reading this file, it is recommended to take a quick glance over the [Design](./Design.md) documentation file, as it provides justification for the existence of these syntaxes.

1. [In the subtopology](#in-the-subtopology)
2. [In the main topology](#in-the-main-topology)
3. [Examples](#examples)

## In the subtopology

### Defining local instances

Local instances are those that are immutable, and are always defined in a subtopology. Any non-local components in a subtopology are exposed to be used in the parent topology, and they can be replaced.

**Syntax**: `@! is local`

**Modifiers**: None

**Applies to**: instance specifications

The following is an example of what your subtopology file may look like with local components.

```
module Main {
    passive component A {}

    instance myCoolComponent: Main.A base id 0xFFFF

    topology ST {
        @! is local # magic annotation
        instance Main.myCoolComponent # qualified names are highly recommended
    }
}
```

### Defining subtopology interfaces

Subtopology interfaces (described further in the [Interfaces.md](./Interfaces.md) document) are formal definitions for interfacing with components inside a topology.

**Syntax**: `@! is interface [input,output]`

**Modifiers**: Choose either `input` or `output` depending on the interface

**Applies to**: instance specifications

The following is an example of what your subtopology file may look like with interfaces.

```
module Main {
    passive component STInput {}
    passive component STOutput {}

    instance Input: Main.STInput base id 0xFFFF
    instance Output: Main.STOutput base id 0xAAAA

    topology ST {
        @! is interface input
        instance Main.Input

        @! is interface output
        instance Main.Output
    }
}
```

### Exporting patterned connection graphs

While seeming like a niche application, it may be the case that one would like to have a patterned connection graph be defined inside the subtopology, but apply to the importing topology. 

For example, `ST` can be a subtopology for a telemetry component, which instantiates component `Tlm` that can be the source for the `telemetry` patterned connection graph. The developer of `ST` would like `Tlm` to be able to hook up to all potential component instances in the parent topology `Main`. 

This can be done with the syntax:

```
topology ST {
    instance Tlm

    @! export
    telemetry connection instance Tlm
}
```

The `@! export` syntax applies to any patterned connection graph type. It also is especially useful if `Tlm` is defined as a local instance, as the syntax will ensure that the patterned connection graph name is renamed.

## In the main topology

In the main topology, we want to be able to define that we want to use our subtopology. Following the above example, `Main.ST` is our subtopology. The following is the syntax to define a subtopology instance in your main deployment's topology fpp file:

```
...

topology MyInstance {}
@<! is Main.ST base id 0xCCCC

....
```

In the above example, `MyInstance` becomes the name of the instance of `Main.ST`. `0xCCCC` becomes the base id offset for all local component instances to `MyInstance` (local instances of `Main.ST` become locally defined instances of `MyInstance`).

We can also add more to our magic annotations to define *instance replacements*. Instance replacements are as they sound, they replace the instance specification in the topology with a user-defined instance. For example, note the syntax below.

```
module MainDeployment {
    instance myCoolerComponent = Main.A base id 0xDDDD

    topology MyInstance {}
    @<! is Main.ST base id 0xCCCC with { # opens a "list" of instance replacements
    @<!     Main.myCoolComponent = myCoolerComponent
    @<! }

}
```

These magic annotations must be tied to a topology; the autocoder will not find it if it is attached to any other element.

In the same way as above, we can also replace the config module name in the subtopology. For subtopologies, it is highly recommended that defaults (i.e., queue size) should be written into a config file, like `STConfig.fpp`. A user may want to create a new config for `MyInstance`, like `MyInstanceConfig.fpp`.

In the autocoder, "Config" is a reserved keyword; if the instance replacement contains "Config", it will modify any qualifiers that use the old config module with the new config module. For example:

```
...

topology MyInstance {}
@<! is Main.ST base id 0xCCCC with {
@<!     Main.myCoolComponent = myCoolerComponent, # multiple instance replacements are comma separated
@<!     STConfig = MyInstanceConfig
@<! }

...
```

Lastly, to be able to import the subtopology into another topology (i.e., your main topology), the qualified path to the subtopology is `<NewTopologyName>`.

```
module MainDeployment {
    instance myCoolerComponent = Main.A base id 0xDDDD

    topology MyInstance {}
    @<! is Main.ST base id 0xCCCC with {
    @<!     Main.myCoolComponent = myCoolerComponent,
    @<!     STConfig = MyInstanceConfig
    @<! }

    topology MainDeployment {
        import MyInstance

        ...
    }

}
```

## Examples

Examples of the syntax, as well as the output files that are made by the autocoder are located in the [example](../example/) directory.

The [Example](./Example.md) documentation file walks through an example project that uses this tool.