# The future of the Subtopology AC in fpp

This tool, while feature complete per the [Design](./Design.md), is not the final step for this tool. The end goal, and on the roadmap for [fpp](https://github.com/nasa/fpp), is to integrate the [Syntax](./Syntax.md) into native fpp to be able to properly model subtopologies. This document recommends the proposed syntax native fpp should adopt.

## Subtopology Instances

In the current version of the autocoder, to instantiate a subtopology, we utilize the syntax:

```
topology MyInstance {}
@<! is Main.ST base id 0xCCCC with {
@<!     Main.myCoolComponent = myCoolerComponent
@<! }
```

Inherently, this reads well, as it shows that `MyST` is a topology that is `Main.ST` (the subtopology) provided a base ID offset `0xCCCC` with `myCoolComponent` being replaced with `myCoolerComponent`. As such, we recommend that the following syntax is an appropriate fpp-based approach to the same goal:

```
topology MyInstance: Main.ST base id 0xCCCC \
    Main.MyCoolComponent = myCoolerComponent
```

Chiefly, we remove the annotation syntax, and replace with `{}` with `:`, which is similar syntax used in defining component instances. In the same vein, we are *defining* a topology instance (dubbed a subtopology). Additionally, we replace the `with {}` with fpp's newline character `\`, to match the usage elsewhere in fpp. We maintain the `<STInstance> = <MyInstance>` syntax, as it maintains the essence of replacement (or redefinition) of the instance in the subtopology with our own defined component instance.

## Local Instances

In the current version of the autocoder, to define that a component instance is local to a topology, we utilize the syntax:

```
topology ST {
    @! is local
    instance Main.myCoolComponent
}
```

We also believe that this reads well, as it cleanly shows that the instance `Main.myCoolComponent`, which is specified in some topology, is local. Of course, this can be defined more simply in fpp with:

```
topology ST {
    local instance Main.myCoolComponent
}
```

The annotation is removed, and the `local` keyword is moved down in line with the instance specification.

## Topology Instances

In the current version of the autocoder, to define an interface for a subtopology, passive components with port pair definitions are created, as well as including the following instance specifications:

```
topology ST {
    @! is interface input
    instance Main.Input

    @! is interface output
    instance Main.Output
}
```

The following syntax works well, but it does not abstract well with the concept of an "interface". In fpp, the goal is that formal interfaces can also be utilized on components (like `include .fppi` with port definitions). The syntax for that would look something like:

```
interface MyCoolInterface {
    sync input port A: Svc.Sched
    output port B: Svc.Sched
    ...
}
```

and in a component, they could be utilized like:

```
passive component G {
    include interface MyCoolInterface
    ...
}
```

Now, this would provide the component `G` with the set of ports that `MyCoolInterface` defines. We could also use this structure to add interfaces into a topology, like so:

```
topology ST {
    ...

    interface MyCoolInterface

    ...
}
```

This syntax is similar to how instance specifications work; instead this specifies an *interface* to the topology `ST`. In the fpp autocoder, this syntax would be similar to the passive component and its removal in the current autocoder. The developer of the topology `ST` can utilize `MyCoolInterface` as a component with the ports it defined, and hook it up properly in connection graphs, without the overhead of needing to define passive components and defining component instances.