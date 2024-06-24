# Syntax for the Subtopology AC Tool

Before reading this file, it is recommended to take a quick glance over the [Design](./Design.md) documentation file, as it provides justification for the existence of these syntaxes.

1. [In the subtopology](#in-the-subtopology)
2. [In the main topology](#in-the-main-topology)
3. [Examples](#examples)

## In the subtopology

The only syntax in the subtopology that is valid is defining instances to be *local*. Local instances are those that are immutable, and are always defined in a subtopology. Any non-local components in a subtopology are exposed to be used in the parent topology, and they can be replaced.

**Syntax**: `@! is local`

**Modifiers**: None

**Applies to**: instance specifications


The following is an example of what your subtopology file may look like with local components.

```
module Main {
    passive component A {}

    instance myCoolComponent = Main.A base id 0xFFFF

    topology ST {
        @! is local # magic annotation
        instance Main.myCoolComponent # qualified names are highly recommended
    }
}
```

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