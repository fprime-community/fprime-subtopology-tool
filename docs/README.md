# Subtopology AC / Documentation

1. [Overview](#overview)
2. [Software Requirements](#software-requirements)
3. [Installation](#installation)

## Documentation

- [Syntax.md](./Syntax.md) - information about syntax in fpp files for this tool
- [Example.md](./Example.md) - documentation for an example project that uses this tool
- [Design.md](./Design.md) - design methodology for this tool

## Overview

This tool is split into two parts: the **autocoder**, which is injected into the build process of an F Prime project, and the **tool behavior**, written in Python files. The purpose of the autocoder is to trigger the python tool on `.fpp` files in F Prime modules, while the python files are responsible for parsing the files, reconstructing subtopologies, and more.

Simple syntax such as:

```
topology MyST {}
@<! is st.st base id 0xCCCC with {
@<!    st.a = main.main_a    
@<! }
```

within a single file is taken and two files are generated in the build cache: `<dynamic>.subtopologies.fpp`, and `st-locs.fpp`, which define the subtopology instance and location of new definitions respectfully.

We must make clear that the terminology "subtopology instance" is used only for simplicity in understanding, but technically is not correct. Within F Prime, topologies do not have a first-party sense of "class", and so the final output of this tool provides a *modified duplication* of the defined subtopology. So in the above example, **MyST** becomes a modified duplication of the topology defined at **st.st**. 

> In the documentation, we will refer to the modified duplication as a subtopology *instance* and the original subtopology as the *base topology*.

## Software Requirements

As of the writing of this documentation, this tool will not work out of the box with the latest stable releases of F Prime. This is because of certain changed with fpp, F Prime's modeling language, and F Prime's autocoder structure. To that end, the minimum versions of certain tools are provided:

- nasa/fprime >= commit UNRELEASED
- nasa/fpp >= commit adee0c8
- Python >= release 3.8

## Installation

To install this tool requires cloning this repository and linking it into the build system for F Prime. So, start by cloning this repository, preferably in the root directory of your F Prime project:

```bash
git clone https://github.com/mosa11aei/fprime-rngLibrary.git
```

Then, we need to update the project's root `CMakeLists.txt` file to include our autocoder. Update that file accordingly:

```cmake
####
# This sets up the build system for the 'new-fprime-rngLibrary' project, including
# components and deployments from project.cmake. In addition, it imports the core F Prime components.
####

cmake_minimum_required(VERSION 3.13)
project(new-fprime-rngLibrary C CXX)

###
# F' Core Setup
# This includes all of the F prime core components, and imports the make-system.
###
include("${CMAKE_CURRENT_LIST_DIR}/fprime/cmake/FPrime.cmake")

# === INSERT THIS LINE ===
register_fprime_build_autocoder("${CMAKE_CURRENT_LIST_DIR}/fprime-subtopology-tool/src/cmake/autocoder/subtopology.cmake" ON) 

fprime_setup_included_code()


# This includes project-wide objects
include("${CMAKE_CURRENT_LIST_DIR}/project.cmake")

```

That's it! Now, whenever the generate step of the F Prime build process is called (i.e., `fprime-util generate`), the autocoder will be called. The `ON` parameter that is included in the arguments of `register_fprime_build_autocoder` tells CMake that our autocoder should execute before any other autocoders. Read more about this in the [design]() section.