MP MP MP MP
---
layout: doc
title: "Parallel Make"
submissions:
- title: Part 1
  due_date: 03/28 11:59pm
  graded_files:
  - parmake.c
- title: Part 2
  due_date: 04/03 11:59pm
learning_objectives:
  - Parallel Programming with Dependencies
  - Using a Threadsafe Data structure
  - Resource Allocation Graphs (RAG)
  - Deadlock Detection
  - Synchronization
wikibook:
  - "Synchronization, Part 4: The Critical Section Problem"
  - "Synchronization, Part 5: Condition Variables"
  - "Deadlock, Part 1: Resource Allocation Graph"
  - "Deadlock, Part 2: Deadlock Conditions"
---

## Introduction

More and more programs today are being programmed as multithreaded applications.
The goal of this MP is to give you more practice writing multithreaded applications and to expose common pitfalls that occur while designing a program to work in a parallel manner.
Additionally, you will need to make use of synchronization primitives to protect the memory shared amongst the threads.

You are given a task of writing an application which will imitate the common `make` utility.
`make` is a utility that automatically builds executable programs from source code by reading files called `Makefiles` which specify how to derive the target program.
You have encountered Makefiles in CS 241 MPs as well as in your previous undergraduate CS classes and should be familiar with them.

We have provided the code to parse a `Makefile` and list the dependencies and commands specified in the file.
Once the file is parsed, you will need to perform the actions specified by the `Makefile` following the rules specified later in the docs.
Using a fixed pool of threads, you will parallelize this execution process such that all commands are executed as soon as their dependencies are satisfied.

Before starting you should read the Wikipedia article on [Make](http://en.wikipedia.org/wiki/Make_(software)).

You might also want to look [here](https://www.cs.umd.edu/class/fall2002/cmsc214/Tutorial/makefile.html) for some notes that explain makefiles really well.
(They start with some C++ specific details but you can skip to the 'Now, makefiles' section. Also, do note that the makefile for this MP does NOT use makefile macros.)


**THIS IS A HARD MP. WE RECOMMEND THAT YOU START EARLY.**

## Resource Allocation Graphs

A good way to think about this MP at a high level is by using a model [covered in lecture](https://github.com/angrave/SystemProgramming/wiki/Deadlock%2C-Part-1%3A-Resource-Allocation-Graph), Resource Allocation Graphs. You can think of `make` targets as nodes in the graph and dependency relations as directed edges that point from targets to dependencies. This visualization comes in handy when we are dealing with programs that may encounter deadlock. Given that a `Makefile` may contain a circular dependency (what are the required conditions for a program to deadlock?), keep this model at the back of your mind when building your solution.

Here is an example Makefile:

    d: a c
        echo D
    a: b
        echo A
    b: a
        echo B
    c:
    	echo C

The following graph represents the above Makefile. Note that 'a' and 'b' form a cycle (-> 'b' -> 'a' ->). 

![Flow Chart](images/ColorfulDeadlock.svg)

Some more resources on RAGs & Deadlock: [Wikipedia](https://en.wikipedia.org/wiki/Deadlock), [Wikibook](https://github.com/angrave/SystemProgramming/wiki/Deadlock%2C-Part-2%3A-Deadlock-Conditions).

## Graph Data Structure

Since a Makefile is a representation of a dependency graph, our parser returns a directed graph data structure. You may find the graph API in `includes/graph.h`. To access Makefile rules from this graph, you would use
```
rule_t * rule = (rule_t *)graph_get_vertex_value(dependency_graph, target_name)
```

where `target_name` is a string representing a rule. To get a list of all target names, use 

```
vector *target_names = graph_vertices(dependency_graph)
```

To get a list of all the dependencies of a rule with a given target name, use 

```
vector *dependencies = graph_neighbors(dependency_graph, target_name)
```

See `rule.h` for a description of the `rule_t` API. And read `parser.h` for more usage details on the dependency graph.

**USAGE WARNINGS**:
* Any vectors returned from graph functions must be destroyed manually to prevent memory leaks. Destroying these vectors will not destroy anything in the actual graph. 
* Destroying the graph or removing vertices from the graph will completely destroy all associated target names, rules, and edges. So copy anything you need for later use before removal or destruction.
* **The graph and vector classes are *not* thread-safe!** You must enforce mutual exclusion if multiple threads are to concurrently modify and access these structures.

## Graph Searching and Cycle Detection

The graph returned from the `parmake` parser will contain all the vertices and edges depicting rules and dependencies in a Makefile. In addition, it will contain an empty sentinel rule (with key "") whose neighbors are the build targets. *Do not execute this rule*. Instead, you should only work on rules that descend from this rule (i.e. the build targets and all their descendents). Here, "B descends from A" means that that 'A' implicitly depends on 'B' to run.

GNU `make` handles cyclical dependencies by attempting to delete edges that cause cycles. If you tried to call `make d` on the example Makefile shown earlier, GNU `make` would essentially attempt to convert that Makefile to this one:

    d: a c
    	echo D
    a: b
    	echo A
    b:  #a (comment out 'a': no more cycles if you remove this edge!)
    	echo B
    c:
    	echo C

To highlight the importance of cycle detection in resource allocation schemes, we also require that you explicitly handle cycles. However, *your implementation of parmake will ignore all build targets whose descendents belong to cycles*. That is, calling `./parmake d` on this makefile would execute nothing, since 'd' cannot be satisfied due to the cyclical dependency (-> 'a' -> 'b' ->). However, calling `./parmake c` will still execute `echo C`, since the (nonexistent) descendents of 'c'
don't belong to cycles.

Moreover, you must announce any build targets that are dropped due to existence of cyclical dependencies *before you start working on any rules* using the function `print_cycle_failure()` found in `format.h`. Read the header file for usage information.

Since this MP requires you to implement some graph algorithms, you may want to consult [this resource](http://www.cs.cornell.edu/courses/cs2112/2012sp/lectures/lec24/lec24-12sp.html) to jog your CS 225 memory.

## Startup

The first thing you will need to do is to parse the given command-line options.
All handling of options should be done using [getopt()](http://www.gnu.org/software/libc/manual/html_node/Getopt.html) .
This function will allow you to specify which options are valid and which require arguments.
The usage for parmake looks like:

```
parmake [ -f makefile ] [ -j threads ] [ targets ]
```

* If a `-f makefile` is not specified, `./makefile` or `./Makefile` should be used (in that order), if they exist (see `access()`).
  Return a non-zero value if
	- `-f makefile` is not specified and neither of `./makefile` or `./Makefile` exists.
	- the file specified by `-f` cannot be opened or read.
    - you do not need to print an error message in these cases, but it might help you when you are developing.
* If the number of worker threads `-j` is not specified, the default value of `1` should be used.
  The `j` worker threads are in addition to the one main thread (so if `j=1`, you will have one worker thread, and one main thread).
* The list of targets will always come last and is optional.
  If no targets are listed, then just set it to be null when passing to the parser.
  The parser will automatically determine the first target and set that as the make target if none is provided explicitly.
* The man page for `getopt()` shows an example of how to locate the position of targets within argc.

### Expected inputs to the program

As stated above, the input for this MP will be expected to be in the following format:

```
./path/to/parmake [-f path/to/makefile] [-j positive-integer] [targets ...]
```

This means that all the inputs will either be empty or have a list of string targets with optional flags from {-f, -j} in any order, followed by a space and then the parameter for the flag as specified by the input description.
If -f exists in the arguments,then it will only be followed a single space, then by a string (which will be a path).
Likewise if -j exists, it will only be followed by a single space, then a positive integer.
There will not be any extraneous spaces in the inputs.

Note: the -f flag could come before -j or vice-versa, but the targets will always come at the end.

You may use the sample makefiles provided as a gouge of the kind of the tests that the autograder will run.
While you should still write test cases to determine the full functionality of your parmake application as described in the documentation.
These input will NOT be tested for by the autograder:

* Any filename string that has more than one word
* Invalid flags (example `-j 1.1` or `-j mydogatemyhomework`)
* Targets which are not defined

Note: Relative paths for makefile names will be resolved with respect to the directory `parmake` is opened in.

Nota Bene: If you use `getopt()`, then you can pretty much ignore this section.

## Process the Makefile

Next, the main thread should process the makefile.
The makefile will always consist of one or more rules of the form:

```
target [target ...]: [dependency ...]
    [command 1]
    .
    .
    [command n]
```

For example:

```
rule1: rule2 rule3
    commandtoberun withargs
    commandtoberun2 withargs

rule2:
    othercommand

rule3 rule4:
    finalcommand
```

If you are unfamiliar with the syntax, do not be afraid.
We have provided you with a parsing function, `parser_parse_makefile()`.
However, you should still take a look at the [Wikipedia page](https://en.wikipedia.org/wiki/Make_(software)) if you do not know how to read a Makefile.

`parser_parse_makefile()` takes the filename and a `NULL`-terminated array of strings as inputs.
The array of strings specify the targets you are planning to run (specified by the arguments to the program, see the first section). Remember, if the array is null or empty, the parser will use the first target found in the Makefile. The parser returns a graph data structure containing all rules and dependencies in the `Makefile`, even those that do not need to be executed.

For example, suppose we have the `Makefile`:

```
a: b c
    echo A
b: c
    echo B
c:
    echo C
d:
    echo D
```

The parser will return a graph containing 5 vertices, once each for rule 'a', 'b', 'c', and 'd', as well as one sentinel (labelled as an empty string) whose neighbor is rule 'a' (i.e. the only build target).

Those curious of the implementation can view the source in `parser.c` although this is not necessary.

We have provided an implementation of a thread safe queue, a non-thread safe vector, and a non-thread safe graph for you to use.
This is the same queue from luscious locks and the same vector from your vector lab. The graph is a new data structure from the CS 241 provided library. 
You can view the header information in `includes/`.

## Satisfy the rules

Each rule depends on a set of other rules and files.
It is important to note that each dependency is either the name of another rule or the name of a file on disk or BOTH. A rule can be run if and only if all of rules that it depends on have been satisfied and none of them have failed (See what determines a failed rule in Running Commands).

Note that rules which do not descend from any build targets, or whose only ancestors otherwise possess descendents that form cycles, should never be run.

`parmake` must satisfy all of the rules needed to build the specified targets correctly and as quickly as possible.
To ensure that rules are executed correctly, a rule can only be run once it's dependencies are satisfied.
Because we want maximum runtime performance, you need to be running a rule on each worker thread, if possible. Threads should not stay idle when there are jobs that can be executed.

When a rule is ready to be satisfied, we must determine if we actually need to run the rule's commands. We run its commands if and only if at least one of the following is true:

*   The name of the rule is not the name of a file on disk.
    **Example:**

```
clean :
    rm -rf *
```

or

```
makenewfile:
    touch newfile
```

*   The rule depends on another rule that is not the name of a file on disk.
    **Example:**

```
clean : take_backup
    rm -rf *
take_backup :
    cp -r * ../backup
```

*   The rule is the name of a file on disk, and it depends on another file with a NEWER modification time than the modification time of the file which corresponds to the name of the rule. To determine whether a file is NEWER, you should use stat and difftime to determine if it is newer. The differences in time will have a granularity of 1 second.

Once we run a rule's commands, we may mark the rule as satisfied.

### Running the commands

You can use `system()` to run the commands associated with each rule. There are a few conditions to think about when evaluating whether or not a rule should be satisfied:

* If any of a rule's commands fail while evaluating that rule, then the rule should "fail" and no more of its commands should be run
* If a rule fails, its parent rules (rules which have this rule as a dependency) should fail as well. Note that this is not necessarily true for the converse (i.e. if a parent fails, its children may still be satisfied -- why is that?)
* Finally, if none of a rule's ancestors are build targets, or its only build target ancestors cannot be satisfied due to circular dependencies, the rule should never be worked on.

For your convenience these rules are captured in the following flow chart:

![Flow Chart](images/parmake_flowchart.svg)

## Parallelize!

The number of threads running rules is given as the command-line option `-j.`
Each worker thread process rules as soon as they become available.
To process a rule, first determine whether its dependencies have been fulfilled.
If they have, execute any associated commands.
There are two important parallelism requirements:

* You should NOT run any rule unless its dependencies have been met (all dependent rules have been run, see the previous section)
* If a thread is available, and there is at least one rule which is ready to run (all of its dependencies satisfied), the available thread should work on that rule.

## Example

Suppose we have `makefile`:

```
a: b c
    echo A
b: c
    echo B
c:
    echo C
```

Running `./parmake` should output:

```
C
B
A
```

There are many more examples provided in your MP folder.

### Notes

* Only make changes in `parmake.c`
* You can assume all makefiles will be in valid Makefile style syntax that can be parsed by our parser.
  You can also expect that there will be no variable references in the Makefiles (e.g. CC=gcc)
* To achieve a perfect score, you should  maximize parallelization by ensuring that every given rule that can be run at a given time is being run.
* You will receive 0 points if your implementation uses `sleep()`.
* For full points, avoid busy-waiting.
* You must only ever launch `T+1` threads, where `T` is the number of worker threads (+1 comes from the main thread).
  Do not keep re-spawning new threads for every rule.
* We will try to artificially create spurious wakeups, so think about how you would resolve that.
* GNU `make` will print out the commands such as 'echo hello' before running it. Your `parmake` application should not do this.
* Remember, the order of the outputs matter for some of the tests!

## Compiling and Running


As usual, we have provided you with a Makefile which will compile your code in a variety of ways.
Unfortunately, you can't use `parmake` to compile `parmake`, because our parser does not support variables and variable expansions.

To compile in release mode, run `make`, for debug mode, use `make debug.`

### ThreadSanitizer
The provided `Makefile` also builds a ThreadSanitizer instrumented version of your code.
The tsan executable is `parmake-tsan`.
You can run this (instead of `parmake`) to use the ThreadSanitizer race condition detection tool with parmake.
For a tsan example, see [the tsan docs](./tsan)

**We will be using ThreadSanitizer to grade your code! If the autograder detects a data race, you won't automatically get 0 points, but a few points will be deducted.**

### (Almost) a reference implementation
You can use the real GNU `make` to check your code.
Note that the real version of `make` usually prints every command it runs.
To get GNU `make` to behave more like `parmake`, run `make` with the flag `-s` (for silent). GNU `make` also deals with cycles differently than `parmake` will, so do not use its behavior as a reference.

Example:

```
    $ ./parmake -f testfile4 -j 2
```

This should generate the same output as:

```
    $ make -s -f testfile4 -j 2
```

provided that testfile4 does not contain cycles.


## Grading

Here is the grading breakdown:

* Part 1 (50%): Create a single-threaded version of `parmake` (so just `make`). This version should:
	- parse user arguments and correctly select a makefile and appropriate build targets for the parser (in particular, you should still parse the -j flag, though we will only test -j 1)
	- identify cycles in the dependency graph returned by the parser and remove build targets that depend on them
	- attempt to run all other build targets by recursively running all their dependencies and *only* their dependencies
	- identify whether or not to run a rule as per the flowchart recipe and run it once possible (or reject it if not possible)
* Part 2 (50%): Create the full multi-threaded version of `parmake` (so `par`). This version should:
	- perform the same functions as in Part 1
	- run with 2-4 threads (excluding the main thread) for any given makefile
	- concurrently run all rules whose dependencies have been satisfied, subject to the thread limit
	- avoid deadlock, data races, livelock, and busy-waiting
	- create performant code that doesn't incur excessive overhead (e.g > 10 ms per rule)

MP MP MP MP
