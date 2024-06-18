# Subtopology AC: A tool to add subtopology instances to F Prime

This tool provides the ability to "instantiate" subtopologies within [F Prime](https://fprime.jpl.nasa.gov).

Topologies are models that represent the connections between instantiated components in a given project. A particularly interesting scope of topologies is the concept of "subtopologies", which aim to provide contained topologies for sets of behavior. 

> For example, an implementation of software behavior for a custom GPS would be a great usage of subtopologies in a project. A GPS could be a contained subsystem of the larger project.

In the current version of F Prime, the ability to make a subtopology exists. However, it's capabilities are limited in a few ways, notably:

1. You can only have one "instance" of a subtopology. If you'd like to reuse a subtopology with different configurations or components, you have to write a new subtopology and use that.

2. Subtopologies do not (yet) have formal interfaces. Thus, if a subtopology would like to provide an uninstantiated component (i.e., device specific like a HID), an end user of a subtopology would have to write in the subtopology their component instance.

The following tool is provided as an autocoder for F Prime, which takes syntactic sugar in the form of annotations in `.fpp` files and adds capabilities to subtopologies in F Prime.

## Documentation

[docs](/docs) - Provides documentation for setting up this tool and further developing it

[nasa/fprime/docs](/docs) - Provides documentation for getting up and running with a subtopology using this tool